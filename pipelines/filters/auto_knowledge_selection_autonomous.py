import asyncio
from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any, Optional, Dict
import json
import re

from open_webui.models.users import Users
from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.misc import get_last_user_message
from open_webui.models.knowledge import Knowledges
from open_webui.models.files import Files
from open_webui.utils.middleware import chat_web_search_handler
from open_webui.models.users import UserModel


class Filter:
    class Valves(BaseModel):
        status: bool = Field(default=True)

    def __init__(self):
        self.valves = self.Valves()

    async def emit_status(
        self,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        level: str,
        message: str,
        done: bool,
    ):
        if self.valves.status:
            await __event_emitter__(
                {
                    "type": level,
                    "data": {
                        "description": message,
                        "done": done,
                    },
                }
            )

    async def parse_json_response(self, content: str) -> Optional[Dict]:
        """
        Utility to parse JSON response from model output.
        """
        try:
            content = content.replace("```json", "").replace("```", "").strip()
            content = content.replace(
                "'", '"'
            )  # Replace single quotes with double quotes
            match = re.search(r"\{.*?\}", content, flags=re.DOTALL)
            if match:
                content = match.group(0)
            else:
                return None

            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            return None

    async def answer_plan(self, body: dict, __user__: Optional[dict]) -> Optional[dict]:
        """
        1) 사용자의 질의가 상세 보고서 형식(report_mode)을 요구하는지 먼저 파악
        """
        messages = body["messages"]
        user_message = get_last_user_message(messages)
        system_prompt = (
            "Analyze the user's prompt to determine if a detailed report-style response is necessary. "
            "Return your response in JSON format with the following structure:\n"
            "{\n"
            '  "report_mode": boolean (true if detailed report is needed, false otherwise),\n'
            '  "contents": array of strings (table of contents if report_mode is true, null if false)\n'
            "}\n"
            "If this is the first message and a report-style conversation is already ongoing, return:\n"
            "{\n"
            '  "report_mode": false,\n'
            '  "contents": null\n'
            "}\n"
            "Do not provide any additional explanations."
        )

        prompt = (
            "History:\n"
            + "\n".join(
                [
                    f"{message['role'].upper()}: \"\"\"{message['content']}\"\"\""
                    for message in messages[::-1][:4]
                ]
            )
            + f"\nQuery: {user_message}"
        )

        return {
            "system_prompt": system_prompt,
            "prompt": prompt,
            "model": "gpt-4o",
        }

    async def knowledge_plan(
        self,
        body: dict,
        __user__: Optional[dict],
    ) -> Optional[dict]:
        """
        2) 메시지(사용자 질의)에 대해 적절한 지식베이스를 선택할 것인지,
           혹은 웹 검색이 필요한지 여부(web_search_enabled)를 판단
        """
        messages = body["messages"]
        user_message = get_last_user_message(messages)
        all_knowledge_bases = Knowledges.get_knowledge_bases_by_user_id(
            __user__.get("id"), "read"
        )

        knowledge_bases_list = "\n".join(
            [
                f"- ID: {getattr(knowledge_base, 'id', 'Unknown')}\n"
                f"  Name: {getattr(knowledge_base, 'name', 'Unknown')}\n"
                f"  Description: {getattr(knowledge_base, 'description', 'Unknown')}\n"
                for knowledge_base in all_knowledge_bases
            ]
        )

        system_prompt = f"""Based on the user's prompt, please find the knowledge base that the user desires.
Available knowledge bases:
{knowledge_bases_list}
Please select the most suitable knowledge base from the above list that best fits the user's requirements.

Additionally, analyze the user's prompt to determine if a web search is required to reflect the latest information. 
Return your response in JSON format with the following fields:
- "id": KnowledgeID (or null if no suitable knowledge base is found)
- "name": Knowledge Name (or null if no suitable knowledge base is found)
- "web_search_enabled": True if a web search is required, False otherwise.
Do not provide any additional explanations.
"""

        return {
            "system_prompt": system_prompt,
            "prompt": user_message,
            "model": "gpt-4o",
        }

    async def _process_toc_section(
        self,
        section: str,
        user_message: str,
        user: Any,
        __request__: Any,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __user__: Optional[dict],
    ) -> str:
        """
        report_mode == True일 때, 각 TOC 항목을 처리하는 헬퍼 함수:
        1) knowledge_plan 으로 적절한 지식베이스/검색 필요 여부 파악
        2) 웹 검색이 필요하면 수행 -> 결과를 messages 또는 별도 구조에 반영
        3) 지식베이스가 있으면 해당 파일 목록을 가져와 section_payload['files'] 에 담기
        4) 최종 GPT 호출하여 섹션 분석 결과를 텍스트로 리턴
        """
        # 1) 먼저 section 단위의 knowledge_plan 세팅
        #    user_message + section 을 합쳐서 body를 구성
        temp_body = {
            "messages": [
                {"role": "user", "content": f"{user_message}\n\n[Section: {section}]"}
            ]
        }
        knowledge_plan_result = await self.knowledge_plan(temp_body, __user__)
        if knowledge_plan_result is None:
            # knowledge_plan_result 못 구하면 그대로 섹션 분석 없이 반환
            return f"[No knowledge plan result for '{section}']"

        # 2) knowledge_plan GPT 호출
        plan_payload = {
            "model": 'gpt-4o',
            "messages": [
                {
                    "role": "system",
                    "content": knowledge_plan_result["system_prompt"],
                },
                {"role": "user", "content": knowledge_plan_result["prompt"]},
            ],
            "stream": False,
        }

        plan_response = await generate_chat_completion(
            request=__request__, form_data=plan_payload, user=user
        )

        plan_content = plan_response["choices"][0]["message"]["content"]
        plan_parsed = await self.parse_json_response(plan_content)

        selected_knowledge_base_id = None
        selected_knowledge_base_info = None
        web_search_required = False

        if plan_parsed:
            selected_knowledge_base_id = plan_parsed.get("id")
            web_search_required = plan_parsed.get("web_search_enabled", False)

        # 3) 웹 검색이 필요하다면 수행
        #    - 실제론 검색 결과를 가져와야 하고, 그걸 messages 또는 files 형태로 넣어줄 수 있음
        search_results_text = None
        if web_search_required:
            print(f"[Section: {section}] Web search required.")
            # 웹 검색을 위해 임시 body를 구성
            search_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": f"User prompt + section: {user_message}\n\n{section}",
                    }
                ],
                "model": "gpt-4o",

            }
            # chat_web_search_handler가 내부적으로 body["messages"]에 검색 결과를 append한다고 가정
            await chat_web_search_handler(
                __request__,
                search_body,
                {"__event_emitter__": __event_emitter__},
                user,
            )
            # 이제 search_body["messages"] 안에 검색 결과 메시지가 들어있다고 가정
            # 간단히 문자열로 합쳐 놓음
            search_results_text = "\n".join(
                f"{m['role']}: {m['content']}" for m in search_body["messages"]
            )

        # 4) 지식베이스가 있다면 파일 목록을 가져오기
        knowledge_files_data = []
        if selected_knowledge_base_id:
            selected_knowledge_base_info = Knowledges.get_knowledge_by_id(
                selected_knowledge_base_id
            )
            if selected_knowledge_base_info:
                kb_file_ids = selected_knowledge_base_info.data["file_ids"]
                kb_files = Files.get_file_metadatas_by_ids(kb_file_ids)
                # 지식베이스를 GPT에 전달하기 위한 구조화
                knowledge_files_data = [file.model_dump() for file in kb_files]

        # 이제 섹션 분석을 위한 최종 Payload 준비
        # - files 구조에 지식베이스 파일(knowledge_files_data)을 포함
        # - 웹 검색 결과도 필요하다면 text 형태로 추가할 수도 있음
        section_payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are ChatGPT. You will analyze the given section in detail.\n"
                        "Please provide a thorough exploration of the following topic.\n\n"
                        "If there are attached 'files' or 'search_results', use them as context.\n"
                        "Do not summarize final output globally; just present your analysis."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original User Prompt:\n{user_message}\n\n"
                        f"Section to analyze: {section}"
                    ),
                },
            ],
            "stream": False,
        }

        # files 구조를 넣어준다 (지식베이스), 필요하면 검색 결과도 함께
        # 실제 LLM API가 'files' 파라미터를 인식하도록 구성돼 있어야 합니다.
        # 혹은 message 내에 system 컨텍스트로 검색 결과를 실어줄 수도 있습니다.
        # 예시로 "files" key를 추가:
        if knowledge_files_data or search_results_text:
            section_payload["files"] = []
            # 지식베이스 파일
            if knowledge_files_data:
                section_payload["files"].append(
                    {
                        "type": "knowledge",
                        "knowledge_base_name": getattr(
                            selected_knowledge_base_info, "name", "Unknown KB"
                        ),
                        "files": knowledge_files_data,
                    }
                )
            # 웹 검색 결과
            if search_results_text:
                section_payload["files"].append(
                    {"type": "web_search", "content": search_results_text}
                )

        # 5) 최종 GPT 호출 (섹션 분석)
        result_response = await generate_chat_completion(
            request=__request__, form_data=section_payload, user=user
        )
        section_analysis_text = result_response["choices"][0]["message"]["content"]

        # 섹션별 결과 반환
        return f"--- [Section: {section}] ---\n{section_analysis_text}\n"

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __request__: Any,
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        """
        inlet: 메인 로직
        1) answer_plan 호출 -> report_mode 체크
        2) report_mode가 true라면, 각 TOC 항목마다 knowledge_plan -> 지식베이스/검색 -> gpt 분석
        3) report_mode가 false라면, 기존 else 로직 그대로 유지
        """
        try:
            user = Users.get_user_by_id(__user__["id"])
            messages = body["messages"]
            user_message = get_last_user_message(messages)

            # Step 1) 먼저 answer_plan 호출
            answer_plan_result = await self.answer_plan(body, __user__)
            payload = {
                "model": answer_plan_result["model"],
                "messages": [
                    {
                        "role": "system",
                        "content": answer_plan_result["system_prompt"],
                    },
                    {"role": "user", "content": answer_plan_result["prompt"]},
                ],
                "stream": False,
            }

            # (1-1) answer_plan GPT 호출
            response = await generate_chat_completion(
                request=__request__, form_data=payload, user=user
            )
            print(f"Answer Plan Response: {response}")

            content = response["choices"][0]["message"]["content"]
            answer_result = await self.parse_json_response(content)
            print(f"Answer Plan Result: {answer_result}")

            # Step 2) report_mode에 따라 분기
            if answer_result.get("report_mode"):
                # =========== report_mode == True ===========
                toc = answer_result.get("contents")
                print("Report mode is ============ true")
                print(f"Table of contents: {toc}")

                if not toc:
                    await self.emit_status(
                        __event_emitter__,
                        level="status",
                        message="Report mode is true, but no table of contents provided.",
                        done=True,
                    )
                else:
                    # TOC 각각을 병렬로 처리하여(gather) 지식베이스/웹검색 후 최종 GPT 호출
                    tasks = []
                    for section in toc:
                        tasks.append(
                            asyncio.create_task(
                                self._process_toc_section(
                                    section=section,
                                    user_message=user_message,
                                    user=user,
                                    __request__=__request__,
                                    __event_emitter__=__event_emitter__,
                                    __user__=__user__,
                                )
                            )
                        )

                    # 모든 섹션의 분석 결과를 병렬로 받아서 순서대로 합침
                    results = await asyncio.gather(*tasks)
                    final_merged_text = "\n".join(results)

                    # 처리 완료 상태 전송
                    await self.emit_status(
                        __event_emitter__,
                        level="status",
                        message="Report mode: sections have been processed in parallel (with knowledge_plan).",
                        done=True,
                    )

                    # 이후 사용자에게 전달될 최종 context_message
                    # "절대 요약하지 말고 섹션별로 정리해서 보여달라"
                    context_message = {
                        "role": "system",
                        "content": (
                            "당신은 ChatGPT, OpenAI가 개발한 대형 언어 모델입니다.\n"
                            "지금부터 아래 merged_text 내용을 **절대로 요약하지 말고**, "
                            "섹션별로 잘 구분하여 그대로 보여주십시오.\n\n"
                            f"merged_text:\n{final_merged_text}"
                        ),
                    }
                    body.setdefault("messages", []).insert(0, context_message)

                # report_mode == true에서는 여기서 body 리턴
                return body

            else:
                # =========== report_mode == False ===========
                print("Report mode is ============ false")
                knowledge_plan_result = await self.knowledge_plan(body, __user__)

                if knowledge_plan_result is None:
                    raise ValueError("Plan result is None")

                payload = {
                    "model": knowledge_plan_result["model"],
                    "messages": [
                        {
                            "role": "system",
                            "content": knowledge_plan_result["system_prompt"],
                        },
                        {"role": "user", "content": knowledge_plan_result["prompt"]},
                    ],
                    "stream": False,
                }

                selected_knowledge_base = None
                response = await generate_chat_completion(
                    request=__request__, form_data=payload, user=user
                )
                content = response["choices"][0]["message"]["content"]

                result = await self.parse_json_response(content)
                if result:
                    print(f"result: {result}")
                    selected_knowledge_base = result.get("id")
                    user_data = __user__.copy()
                    user_data.update(
                        {
                            "profile_image_url": "",
                            "last_active_at": 0,
                            "updated_at": 0,
                            "created_at": 0,
                        }
                    )
                    user_object = UserModel(**user_data)

                    if result.get("web_search_enabled"):
                        print("Web search required.")
                        await chat_web_search_handler(
                            __request__,
                            body,
                            {"__event_emitter__": __event_emitter__},
                            user_object,
                        )
                    else:
                        print("No web search required.")

                selected_knowledge_base_info = (
                    Knowledges.get_knowledge_by_id(selected_knowledge_base)
                    if selected_knowledge_base
                    else None
                )

                if selected_knowledge_base_info:
                    knowledge_file_ids = selected_knowledge_base_info.data["file_ids"]
                    knowledge_files = Files.get_file_metadatas_by_ids(
                        knowledge_file_ids
                    )
                    knowledge_dict = selected_knowledge_base_info.model_dump()
                    knowledge_dict["files"] = [
                        file.model_dump() for file in knowledge_files
                    ]
                    knowledge_dict["type"] = "collection"

                    body["files"] = body.get("files", []) + [knowledge_dict]

                    await self.emit_status(
                        __event_emitter__,
                        level="status",
                        message=f"Matching knowledge base found: {selected_knowledge_base_info.name}",
                        done=True,
                    )
                else:
                    await self.emit_status(
                        __event_emitter__,
                        level="status",
                        message="No matching knowledge base found.",
                        done=True,
                    )

                context_message = {
                    "role": "system",
                    "content": (
                        "You are ChatGPT, a large language model trained by OpenAI. "
                        "Please ensure that all your responses are presented in a clear and organized manner using "
                        "bullet points, numbered lists, headings, and other formatting tools to enhance readability "
                        "and user-friendliness. Additionally, please respond in the language used by the user "
                        "in their input."
                    ),
                }

                body.setdefault("messages", []).insert(0, context_message)
                return body

        except Exception as e:
            print(e)
            await self.emit_status(
                __event_emitter__,
                level="status",
                message=f"Error occurred while processing the request: {e}",
                done=True,
            )

            context_message = {
                "role": "system",
                "content": (
                    "You are ChatGPT, a large language model trained by OpenAI. "
                    "An error occurred during the request. Please proceed with caution."
                ),
            }
            body.setdefault("messages", []).insert(0, context_message)
            return body
