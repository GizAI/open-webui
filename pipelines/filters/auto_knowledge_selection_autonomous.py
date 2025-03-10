import json
import re
from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any, Optional

from open_webui.models.users import Users, UserModel
from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.misc import get_last_user_message
from open_webui.models.knowledge import Knowledges
from open_webui.models.files import Files
from open_webui.utils.middleware import chat_web_search_handler


def parse_json_content(content: str) -> Optional[dict]:
    """
    주어진 문자열에서 JSON 객체를 추출하고 dict로 변환합니다.
    - 문자열 전체가 '{...}'로 감싸져 있다면 직접 파싱을 시도합니다.
    - 아닐 경우, 정규표현식으로 첫 번째 JSON 객체를 추출하여 파싱 시도합니다.
    - 파싱에 실패하면 None을 반환합니다.
    - 필요 시(파싱 실패), 작은따옴표(')를 큰따옴표(")로 바꿔보는 시도도 합니다.
    """

    def try_load_json(json_str: str) -> Optional[dict]:
        """주어진 json_str을 파싱 시도하고 실패 시 None을 반환합니다."""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    content = content.strip()

    # "None"과 같이 JSON 아닌 특정 문자열 처리
    if content.lower() == "none":
        return None

    # 1) 직접 '{...}'로 감싸져 있는지 확인
    if content.startswith("{") and content.endswith("}"):
        parsed_data = try_load_json(content)
        if parsed_data is not None:
            return parsed_data

        # 파싱 실패 시, 작은따옴표를 큰따옴표로 치환 후 재시도
        content_single_to_double = content.replace("'", '"')
        parsed_data = try_load_json(content_single_to_double)
        if parsed_data is not None:
            return parsed_data

        return None

    # 2) 정규표현식으로 '{...}' 형태 추출
    match = re.search(r"\{.*?\}", content, flags=re.DOTALL)
    if not match:
        return None

    json_str = match.group(0)

    parsed_data = try_load_json(json_str)
    if parsed_data is not None:
        return parsed_data

    # 파싱 실패 시, 작은따옴표를 큰따옴표로 치환 후 재시도
    json_str_converted = json_str.replace("'", '"')
    parsed_data = try_load_json(json_str_converted)
    if parsed_data is not None:
        return parsed_data

    return None


class Filter:
    class Valves(BaseModel):
        status: bool = Field(default=True)
        auto_search_mode: bool = Field(default=False)
        plan_model: str = Field(default="o3-mini")

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

    async def select_knowledge_base(
        self, body: dict, __user__: Optional[dict]
    ) -> Optional[dict]:
        """
        사용자의 메시지를 바탕으로 적절한 Knowledge Base를 선택한다.
        - 출력 예시:
            {
                "id": <KnowledgeBaseID or null>,
                "name": <KnowledgeBaseName or null>
            }
        """
        messages = body["messages"]
        user_message = get_last_user_message(messages)

        all_knowledge_bases = Knowledges.get_knowledge_bases_by_user_id(
            __user__.get("id"), "read"
        )

        knowledge_bases_list = "\n\n".join(
            [
                f"--- Knowledge Base {index + 1} ---\n"
                f"ID: {getattr(knowledge_base, 'id', 'Unknown')}\n"
                f"Name: {getattr(knowledge_base, 'name', 'Unknown')}\n"
                f"Description: {getattr(knowledge_base, 'description', 'Unknown')}"
                for index, knowledge_base in enumerate(all_knowledge_bases)
            ]
        )

        system_prompt = f"""You are a system that selects the most appropriate knowledge bases for the user's query.
Below is a list of knowledge bases accessible by the user. 
Based on the user's prompt, return the 1-3 most relevant knowledge bases as an array. 
If no relevant knowledge bases are applicable, return an "None" without any explanation.

Available knowledge bases:
{knowledge_bases_list}

Return the result in the following JSON format (no extra keys, no explanations):
{{
    "selected_knowledge_bases": 
        [
            {{
                "id": <KnowledgeBaseID>,
                "name": <KnowledgeBaseName>
            }},
            ...
        ]
}}
"""

        prompt = (
            "History:\n"
            + "\n".join(
                [
                    f"{message['role'].upper()}: \"\"\"{message['content']}\"\"\""
                    for message in messages[::-1][:4]
                ]
            )
            + f"\nUser query: {user_message}"
        )

        return {
            "system_prompt": system_prompt,
            "prompt": prompt,
            "model": self.valves.plan_model,
        }

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __request__: Any,
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        try:
            # 유저 객체 보정
            user_data = __user__.copy() if __user__ else {}
            user_data.update(
                {
                    "profile_image_url": "",
                    "last_active_at": 0,
                    "updated_at": 0,
                    "created_at": 0,
                }
            )
            user_object = UserModel(**user_data)
            user = Users.get_user_by_id(__user__["id"]) if __user__ else None

            ###################################################################
            # 1) Knowledge Base 선택
            ###################################################################
            kb_plan = await self.select_knowledge_base(body, __user__)
            if kb_plan is None:
                raise ValueError("select_knowledge_base result is None")

            kb_payload = {
                "model": kb_plan["model"],
                "messages": [
                    {"role": "system", "content": kb_plan["system_prompt"]},
                    {"role": "user", "content": kb_plan["prompt"]},
                ],
                "stream": False,
            }
            kb_response = await generate_chat_completion(
                request=__request__, form_data=kb_payload, user=user
            )

            kb_content = (
                kb_response["choices"][0]["message"]["content"] if kb_response else ""
            )
            print("kb_content start: =================================")
            print(kb_content)
            print("kb_content end: =================================")

            if kb_content == "None":
                selected_knowledge_bases = []
            else:
                try:
                    kb_result = parse_json_content(kb_content)

                    selected_knowledge_bases = (
                        kb_result.get("selected_knowledge_bases", [])
                        if kb_result
                        else []
                    )
                except Exception as e:
                    print(e)
                    selected_knowledge_bases = []

            ###################################################################
            # 2) 웹 검색
            ###################################################################

            if self.valves.auto_search_mode:
                await chat_web_search_handler(
                    __request__,
                    body,
                    {"__event_emitter__": __event_emitter__},
                    user_object,
                )

            ###################################################################
            # 선택된 Knowledge Base가 있으면 body에 추가 (기존 files와 병합)
            ###################################################################

            selected_kb_names = []
            for selected_knowledge_base in selected_knowledge_bases:
                kb_id = selected_knowledge_base.get("id")
                kb_name = selected_knowledge_base.get("name")

                if kb_id and kb_name:
                    selected_kb_names.append(kb_name)
                    selected_knowledge_base_info = Knowledges.get_knowledge_by_id(kb_id)

                    if selected_knowledge_base_info:
                        knowledge_file_ids = selected_knowledge_base_info.data.get(
                            "file_ids", []
                        )
                        knowledge_files = Files.get_file_metadatas_by_ids(
                            knowledge_file_ids
                        )
                        knowledge_dict = selected_knowledge_base_info.model_dump()
                        knowledge_dict["files"] = [
                            file.model_dump() for file in knowledge_files
                        ]
                        knowledge_dict["type"] = "collection"

                        if "files" not in body:
                            body["files"] = []
                        body["files"].append(knowledge_dict)

            if selected_kb_names:
                await self.emit_status(
                    __event_emitter__,
                    level="status",
                    message=f"Matching knowledge bases found: {', '.join(selected_kb_names)}",
                    done=True,
                )
            else:
                await self.emit_status(
                    __event_emitter__,
                    level="status",
                    message="No matching knowledge base found.",
                    done=True,
                )

        except Exception as e:
            print(e)
            await self.emit_status(
                __event_emitter__,
                level="status",
                message=f"Error occurred while processing the request: {e}",
                done=True,
            )

        ###################################################################
        # 최종 시스템 메시지 삽입 (답변 형태 지침)
        ###################################################################
        context_message = {
            "role": "system",
            "content": (
                "You are ChatGPT, a large language model trained by OpenAI. "
                "Please ensure that all your responses are presented in a clear and organized manner using bullet points, numbered lists, headings, and other formatting tools to enhance readability and user-friendliness. "
                "Additionally, please respond in the language used by the user in their input. "
            ),
        }
        print("body start: =================================")
        print(body)
        print("body end: =================================")
        body.setdefault("messages", []).insert(0, context_message)
        return body
