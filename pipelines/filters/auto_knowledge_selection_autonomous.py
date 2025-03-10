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

    async def parse_json_response(self, content: str) -> Optional[Any]:
        """
        Utility to parse JSON response from model output.
        더 강력한 JSON 파싱 기능 제공
        """
        if not content or not content.strip():
            return None

        try:
            # 1. 기본 정리: 코드블록, 따옴표 등 제거
            content = content.replace("```json", "").replace("```", "").strip()

            # 2. 단일 따옴표를 이중 따옴표로 변환 (JSON 표준)
            content = content.replace("'", '"')

            # 3. 중괄호 혹은 대괄호를 이용한 JSON 형태를 추출
            match = re.search(r"(\{.*\}|\[.*\])", content, flags=re.DOTALL)
            if match:
                content = match.group(0)
            else:
                # JSON 형태가 없으면 None 반환
                return None

            # 4. 잘못된 쉼표 처리 (배열이나 객체 끝에 있는 쉼표 제거)
            content = re.sub(r",\s*}", "}", content)
            content = re.sub(r",\s*\]", "]", content)

            # 5. 키에 따옴표가 없는 경우 추가 (예: {key: "value"} -> {"key": "value"})
            content = re.sub(r"([{,])\s*([a-zA-Z0-9_]+)\s*:", r'\1"\2":', content)

            # 6. 최종 파싱 시도
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}, Content: {content[:100]}...")

            # 7. 마지막 시도: 정규식으로 배열 형태 추출 (키워드 생성 등에 유용)
            if content.find("[") >= 0 and content.find("]") >= 0:
                try:
                    # 배열 내용만 추출
                    array_match = re.search(r"\[(.*)\]", content, flags=re.DOTALL)
                    if array_match:
                        array_content = array_match.group(1)
                        # 항목 추출 (따옴표로 둘러싸인 문자열)
                        items = re.findall(r'"([^"]*)"', array_content)
                        if items:
                            return items
                except Exception as e2:
                    print(f"Final regex extraction failed: {e2}")

            return None

    async def answer_plan(self, body: dict, __user__: Optional[dict]) -> Optional[dict]:
        """
        1) 사용자의 질의가 상세 보고서 형식(report_mode)을 요구하는지 판단
           - report_mode: boolean
           - contents: array of strings (목차)
        """
        messages = body["messages"]
        user_message = get_last_user_message(messages)

        # 보고서 모드를 판단하는 system_prompt를 최소화(체인오브띠록 노출 금지)
        system_prompt = (
            "You are a plan analyzer. Determine if the user's query needs a detailed, structured report.\n"
            "Return your answer in JSON only, like:\n"
            "{\n"
            '  "report_mode": true or false,\n'
            '  "contents": [ "Section A", "Section B", ... ] or null\n'
            "}\n"
            "If a report_mode is required, provide a minimal list of content sections under 'contents'.\n"
            "No further explanation."
        )

        # 최근 메시지 몇 개만 히스토리로 합쳐서 user prompt 구성
        prompt = (
            "Recent history:\n"
            + "\n".join(
                [
                    f"{message['role'].upper()}: {message['content']}"
                    for message in messages[::-1][:4]
                ]
            )
            + f"\nUser query: {user_message}"
        )

        return {
            "system_prompt": system_prompt,
            "prompt": prompt,
            "model": "o3-mini",
        }

    async def knowledge_plan(
        self,
        body: dict,
        __user__: Optional[dict],
    ) -> Optional[dict]:
        """
        2) 메시지(사용자 질의)에 대해 적절한 지식베이스 선택 & 웹 검색 필요 여부 판단
           - id (선택된 KnowledgeBase ID, 없으면 null)
           - name (선택된 KnowledgeBase 이름, 없으면 null)
           - web_search_enabled (bool)
        """
        messages = body["messages"]
        user_message = get_last_user_message(messages)

        # 유저에 연관된 지식베이스 목록
        all_knowledge_bases = Knowledges.get_knowledge_bases_by_user_id(
            __user__.get("id"), "read"
        )
        knowledge_bases_list = "\n".join(
            [
                f"- ID: {getattr(knowledge_base, 'id', 'Unknown')} / "
                f"Name: {getattr(knowledge_base, 'name', 'Unknown')} / "
                f"Description: {getattr(knowledge_base, 'description', 'Unknown')}"
                for knowledge_base in all_knowledge_bases
            ]
        )

        system_prompt = (
            "You are a knowledge selector. Below is a list of knowledge bases:\n"
            f"{knowledge_bases_list}\n\n"
            "Based on the user's query, choose the most relevant one or null.\n"
            "Also determine if a web search is needed. Return JSON:\n"
            "{\n"
            '  "id": string or null,\n'
            '  "name": string or null,\n'
            '  "web_search_enabled": boolean\n'
            "}\n"
            "No additional explanation."
        )

        return {
            "system_prompt": system_prompt,
            "prompt": user_message,
            "model": "o3-mini",
        }

    async def _generate_search_keywords(
        self, section_topic: str, user_message: str, __request__: Any, user: Any
    ) -> list:
        """
        섹션 주제에 맞는 검색 키워드를 자동 생성하기 위한 헬퍼 메서드.
        (체인오브띠록 없이, JSON 배열로만 반환되도록 유도)
        """
        system_prompt = (
            "You are a search keyword generator. Given the user's overall question and a section topic, "
            "generate a concise list of possible web search queries (keywords) in JSON array.\n"
            "No chain-of-thought, no extra text. Just JSON array of strings."
        )
        user_prompt = (
            f"User's question: {user_message}\n"
            f"Section topic: {section_topic}\n"
            'Return a JSON array, e.g. ["keyword1", "keyword2", ...].'
        )

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            payload = {
                "model": "o3-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            }

            try:
                resp = await generate_chat_completion(
                    request=__request__, form_data=payload, user=user
                )
                content = resp["choices"][0]["message"]["content"]
                parsed = await self.parse_json_response(content)

                if isinstance(parsed, list):
                    return parsed
                else:
                    # JSON 파싱은 성공했지만 결과가 리스트가 아닌 경우
                    # 더 명확한 지시를 포함하여 재시도
                    retry_count += 1
                    user_prompt = (
                        f"User's question: {user_message}\n"
                        f"Section topic: {section_topic}\n"
                        'Return ONLY a valid JSON array of strings, e.g. ["keyword1", "keyword2", ...]. '
                        "No explanations, just the JSON array."
                    )
                    continue
            except Exception as e:
                print(
                    f"Keyword generation error (attempt {retry_count+1}/{max_retries}): {e}"
                )
                retry_count += 1
                # 오류 발생 시 더 명확한 지시를 포함하여 재시도
                user_prompt = (
                    f"User's question: {user_message}\n"
                    f"Section topic: {section_topic}\n"
                    'Return ONLY a valid JSON array of strings, e.g. ["keyword1", "keyword2", ...]. '
                    "No explanations, no markdown, just the raw JSON array."
                )
                continue

        # 모든 재시도 실패 후 빈 배열 반환
        print(f"All {max_retries} attempts to generate keywords failed.")
        return []

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
        report_mode == True일 때, 각 TOC 항목을 순차적으로 처리:
        1) knowledge_plan -> 지식베이스/검색 필요 여부 판단
        2) 검색 필요시 -> 검색 키워드 자동 생성 -> 검색 -> 결과 취합
        3) 지식베이스가 있으면 해당 파일 목록 추출
        4) GPT로 섹션 분석
        5) 섹션별 분석 결과 반환
        """
        # 1) knowledge_plan
        temp_body = {
            "messages": [
                {"role": "user", "content": f"{user_message}\n\n[Section: {section}]"}
            ]
        }
        knowledge_plan_result = await self.knowledge_plan(temp_body, __user__)
        if knowledge_plan_result is None:
            return f"[No knowledge plan result for '{section}']"

        max_retries = 3
        retry_count = 0
        plan_parsed = None

        while retry_count < max_retries and plan_parsed is None:
            try:
                plan_payload = {
                    "model": "o3-mini",
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

                if plan_parsed is None:
                    # JSON 파싱 실패 시 더 명확한 지시를 포함하여 재시도
                    retry_count += 1
                    if retry_count < max_retries:
                        # 더 명확한 지시를 포함한 시스템 프롬프트로 업데이트
                        plan_payload["messages"][0]["content"] = (
                            knowledge_plan_result["system_prompt"]
                            + "\nIMPORTANT: Return ONLY valid JSON format. No explanations, no markdown."
                        )
                        print(
                            f"JSON parsing failed for section '{section}', retrying ({retry_count}/{max_retries})..."
                        )
                        continue
            except Exception as e:
                print(
                    f"Error processing section '{section}' (attempt {retry_count+1}/{max_retries}): {e}"
                )
                retry_count += 1
                if retry_count < max_retries:
                    continue
                else:
                    return f"[Error processing section '{section}' after {max_retries} attempts]"

        if plan_parsed is None:
            return f"[Failed to parse JSON response for section '{section}' after {max_retries} attempts]"

        selected_knowledge_base_id = None
        selected_knowledge_base_info = None
        web_search_required = False

        if plan_parsed:
            selected_knowledge_base_id = plan_parsed.get("id")
            web_search_required = plan_parsed.get("web_search_enabled", False)

        # 2) 웹 검색이 필요하다면, 섹션 주제에 맞는 검색 키워드 생성 후 검색 수행
        search_results_text = None
        if web_search_required:
            # 검색 키워드 생성
            keywords = await self._generate_search_keywords(
                section_topic=section,
                user_message=user_message,
                __request__=__request__,
                user=user,
            )
            if keywords:
                # 검색용 body 생성
                search_prompts = []
                for kw in keywords:
                    # 키워드별로 검색
                    search_prompts.append(f"Search keyword: {kw}")

                # 실제 검색 수행(키워드 여러 개를 일괄 검색 또는 각각 검색)
                # 여기서는 예시로 한꺼번에 검색하도록 구성
                combined_search_query = " OR ".join(keywords)
                search_body = {
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Search these keywords: {combined_search_query}",
                        }
                    ],
                    "model": "o3-mini",
                }

                await chat_web_search_handler(
                    __request__,
                    search_body,
                    {"__event_emitter__": __event_emitter__},
                    user,
                )

                # 검색 결과 취합
                web_search_results = []
                if "files" in search_body and search_body["files"]:
                    for file in search_body["files"]:
                        if file.get("type") == "web_search":
                            if "docs" in file:
                                for doc in file.get("docs", []):
                                    snippet = doc.get("content", "")
                                    url = doc.get("url", "")
                                    web_search_results.append(f"URL: {url}")
                                    web_search_results.append(f"Content: {snippet}")

                if web_search_results:
                    search_results_text = "\n".join(web_search_results)

        # 3) 지식베이스 파일
        knowledge_files_data = []
        if selected_knowledge_base_id:
            selected_knowledge_base_info = Knowledges.get_knowledge_by_id(
                selected_knowledge_base_id
            )
            if selected_knowledge_base_info:
                kb_file_ids = selected_knowledge_base_info.data["file_ids"]
                kb_files = Files.get_file_metadatas_by_ids(kb_file_ids)
                knowledge_files_data = [file.model_dump() for file in kb_files]

        # 4) 섹션 분석을 위한 최종 Payload
        #    (체인오브띠록 노출되지 않도록, '사용 가능한 참고자료'만 system 메시지에 담고, 분량 축소)
        context_parts = []
        if selected_knowledge_base_info and knowledge_files_data:
            context_parts.append(f"Knowledge Base: {selected_knowledge_base_info.name}")
            for file in knowledge_files_data:
                context_parts.append(f"File: {file.get('name', '')}")
                context_parts.append(f"{file.get('content', '')}")

        if search_results_text:
            context_parts.append("\nWeb Search Results:")
            context_parts.append(search_results_text)

        # 간결한 system 메시지
        system_context = (
            "You are a specialized report writer. Analyze the 'section' thoroughly using the available context.\n"
            "Provide a comprehensive and detailed analysis without summarizing. Include all relevant information and insights.\n"
            "Present your analysis in a well-structured format with clear sections and bullet points where appropriate.\n"
        )
        if context_parts:
            system_context += "\nRelevant context:\n" + "\n".join(context_parts)

        # 섹션 분석 결과 처리 시 재시도 로직
        max_analysis_retries = 2
        analysis_retry_count = 0
        section_analysis_text = None

        while (
            analysis_retry_count < max_analysis_retries
            and section_analysis_text is None
        ):
            try:
                section_payload = {
                    "model": "o3",
                    "messages": [
                        {"role": "system", "content": system_context},
                        {
                            "role": "user",
                            "content": f"Section topic: {section}\nUser's question:\n{user_message}\n\nProvide a comprehensive and detailed analysis of this section. Do not summarize or omit any important details. Include all relevant information, insights, and connections to the user's question.",
                        },
                    ],
                    "stream": False,
                }

                result_response = await generate_chat_completion(
                    request=__request__, form_data=section_payload, user=user
                )
                section_analysis_text = result_response["choices"][0]["message"][
                    "content"
                ]

                if not section_analysis_text or section_analysis_text.strip() == "":
                    # 응답이 비어있는 경우 재시도
                    analysis_retry_count += 1
                    if analysis_retry_count < max_analysis_retries:
                        print(
                            f"Empty analysis result for section '{section}', retrying ({analysis_retry_count}/{max_analysis_retries})..."
                        )
                        continue
                    else:
                        section_analysis_text = f"[Failed to generate analysis for section '{section}' after {max_analysis_retries} attempts]"
            except Exception as e:
                print(
                    f"Error analyzing section '{section}' (attempt {analysis_retry_count+1}/{max_analysis_retries}): {e}"
                )
                analysis_retry_count += 1
                if analysis_retry_count < max_analysis_retries:
                    continue
                else:
                    section_analysis_text = (
                        f"[Error analyzing section '{section}': {str(e)}]"
                    )

        return f"--- [Section: {section}] ---\n{section_analysis_text}\n\n"

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __request__: Any,
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        """
        메인 로직:
        1) answer_plan -> report_mode 판단
        2) report_mode == true -> TOC 각 섹션 처리(_process_toc_section)
        3) report_mode == false -> knowledge_plan + (web검색/지식베이스) -> 기본 답변
        """
        try:
            user = Users.get_user_by_id(__user__["id"])
            messages = body["messages"]
            user_message = get_last_user_message(messages)

            # 1) answer_plan
            answer_plan_result = await self.answer_plan(body, __user__)

            # JSON 파싱 재시도 로직
            max_retries = 3
            retry_count = 0
            answer_result = None

            while retry_count < max_retries and answer_result is None:
                try:
                    plan_payload = {
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

                    # answer_plan GPT 호출
                    response = await generate_chat_completion(
                        request=__request__, form_data=plan_payload, user=user
                    )
                    content = response["choices"][0]["message"]["content"]
                    answer_result = await self.parse_json_response(content)

                    if answer_result is None:
                        # JSON 파싱 실패 시 더 명확한 지시를 포함하여 재시도
                        retry_count += 1
                        if retry_count < max_retries:
                            # 더 명확한 지시를 포함한 시스템 프롬프트로 업데이트
                            plan_payload["messages"][0]["content"] = (
                                answer_plan_result["system_prompt"]
                                + "\nIMPORTANT: Return ONLY valid JSON format. No explanations, no markdown."
                            )
                            await self.emit_status(
                                __event_emitter__,
                                level="status",
                                message=f"JSON parsing failed, retrying ({retry_count}/{max_retries})...",
                                done=False,
                            )
                            continue
                except Exception as e:
                    print(
                        f"Error in answer_plan processing (attempt {retry_count+1}/{max_retries}): {e}"
                    )
                    retry_count += 1
                    if retry_count < max_retries:
                        await self.emit_status(
                            __event_emitter__,
                            level="status",
                            message=f"Error in processing, retrying ({retry_count}/{max_retries})...",
                            done=False,
                        )
                        continue
                    else:
                        await self.emit_status(
                            __event_emitter__,
                            level="error",
                            message=f"Failed to process after {max_retries} attempts",
                            done=True,
                        )
                        return body

            if answer_result is None:
                await self.emit_status(
                    __event_emitter__,
                    level="error",
                    message=f"Failed to parse JSON response after {max_retries} attempts",
                    done=True,
                )
                return body

            # 2) report_mode 여부 확인
            if answer_result and answer_result.get("report_mode") is True:
                toc = answer_result.get("contents") or []
                if not toc:
                    # 목차가 없으면 그대로 진행
                    await self.emit_status(
                        __event_emitter__,
                        level="status",
                        message="Report mode is true but no contents found.",
                        done=True,
                    )
                    return body
                else:
                    # TOC 순차 처리
                    results = []
                    for section in toc:
                        try:
                            result = await self._process_toc_section(
                                section=section,
                                user_message=user_message,
                                user=user,
                                __request__=__request__,
                                __event_emitter__=__event_emitter__,
                                __user__=__user__,
                            )
                            results.append(result)
                        except Exception as e:
                            print(f"Error processing section '{section}': {e}")
                            results.append(f"Error in section {section}: {e}")

                    final_merged_text = "\n".join(results)

                    # 보고서 모드 완결
                    await self.emit_status(
                        __event_emitter__,
                        level="status",
                        message="All sections processed (report_mode).",
                        done=True,
                    )

                    # 최종 보고서를 생성하기 위한 system 메시지(체인오브띠록 노출 없이)
                    context_message = {
                        "role": "system",
                        "content": (
                            "You are a professional technical writer. "
                            "Below is a merged analysis of all sections. "
                            "Please format it as a cohesive final report.\n\n"
                            f"{final_merged_text}\n\n"
                            "No chain-of-thought, just the final report. "
                            "Present in a user-friendly way, properly organized by section."
                            "Respond in the same language as the user's query."
                        ),
                    }

                    # 최종 마무리 메시지를 본문의 맨 앞에 삽입
                    body.setdefault("messages", []).insert(0, context_message)
                    return body

            else:
                # =========== report_mode == False ===========
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

                web_search_results = []
                if result:
                    selected_knowledge_base = result.get("id")
                    if result.get("web_search_enabled"):
                        # 검색 키워드 생성
                        keywords = await self._generate_search_keywords(
                            section_topic=user_message,
                            user_message=user_message,
                            __request__=__request__,
                            user=user,
                        )
                        if keywords:
                            combined_search_query = " OR ".join(keywords)
                            search_body = {
                                "messages": [
                                    {
                                        "role": "user",
                                        "content": f"Search these keywords: {combined_search_query}",
                                    }
                                ],
                                "model": "o3-mini",
                            }

                            await chat_web_search_handler(
                                __request__,
                                search_body,
                                {"__event_emitter__": __event_emitter__},
                                user,
                            )

                            if "files" in search_body and search_body["files"]:
                                for file in search_body["files"]:
                                    if file.get("type") == "web_search":
                                        if "docs" in file:
                                            for doc in file.get("docs", []):
                                                snippet = doc.get("content", "")
                                                url = doc.get("url", "")
                                                web_search_results.append(f"URL: {url}")
                                                web_search_results.append(
                                                    f"Content: {snippet}"
                                                )
                    else:
                        print("No web search required.")

                # 지식베이스 처리
                selected_knowledge_base_info = (
                    Knowledges.get_knowledge_by_id(selected_knowledge_base)
                    if selected_knowledge_base
                    else None
                )

                # System 메시지 생성
                context_parts = []
                if selected_knowledge_base_info:
                    kb_name = selected_knowledge_base_info.name
                    kb_file_ids = selected_knowledge_base_info.data["file_ids"]
                    kb_files = Files.get_file_metadatas_by_ids(kb_file_ids)

                    context_parts.append(f"Knowledge Base: {kb_name}")
                    for file in kb_files:
                        file_data = file.model_dump()
                        context_parts.append(
                            f"File: {file_data.get('name', 'Unknown')}"
                        )
                        context_parts.append(file_data.get("content", ""))

                    await self.emit_status(
                        __event_emitter__,
                        level="status",
                        message=f"Using knowledge base: {kb_name}",
                        done=True,
                    )
                else:
                    await self.emit_status(
                        __event_emitter__,
                        level="status",
                        message="No matching knowledge base found.",
                        done=True,
                    )

                if web_search_results:
                    context_parts.append("\nWeb Search Results:")
                    context_parts.extend(web_search_results)

                # 최종 system 메시지(체인오브띠록 최소화)
                if context_parts:
                    system_message_content = (
                        "You are a helpful assistant. Here is some reference information:\n"
                        + "\n".join(context_parts)
                        + "\nUse it to answer the user's query.\nNo chain-of-thought."
                        + "\nRespond in the same language as the user's query."
                    )
                else:
                    system_message_content = (
                        "You are a helpful assistant. No additional context is available.\n"
                        "Answer the user's query to the best of your ability.\nNo chain-of-thought."
                        + "\nRespond in the same language as the user's query."
                    )

                context_message = {
                    "role": "system",
                    "content": system_message_content,
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

            # fallback 메시지
            context_message = {
                "role": "system",
                "content": (
                    "You are a helpful assistant. An error occurred. "
                    "Proceed with your best effort. No chain-of-thought."
                    "Respond in the same language as the user's query."
                ),
            }
            body.setdefault("messages", []).insert(0, context_message)
            return body
