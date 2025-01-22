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
    주어진 문자열 content에서 JSON 객체만 추출하여 dict로 반환한다.
    - '```json' 블록 제거
    - 작은따옴표(')를 큰따옴표(")로 변환
    - 정규식으로 { ... } 블록만 추출
    - 추출에 실패하면 None 반환
    """
    try:
        content = content.replace("```json", "").replace("```", "").strip()
        content = content.replace("'", '"')
        match = re.search(r"\{.*?\}", content, flags=re.DOTALL)
        if not match:
            return None
        content_json_str = match.group(0)
        return json.loads(content_json_str)
    except json.JSONDecodeError:
        return None


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

        knowledge_bases_list = "\n".join(
            [
                f"- ID: {getattr(knowledge_base, 'id', 'Unknown')}\n"
                f"  - Knowledge Base Name: {getattr(knowledge_base, 'name', 'Unknown')}\n"
                f"  - Description: {getattr(knowledge_base, 'description', 'Unknown')}\n"
                for knowledge_base in all_knowledge_bases
            ]
        )

        system_prompt = f"""You are a system that selects the most appropriate knowledge base for the user's query.
Below is a list of knowledge bases accessible by the user. 
Based on the user's prompt, return the most relevant knowledge base ID and name as JSON.

Available knowledge bases:
{knowledge_bases_list}

Return the result in the following JSON format (no extra keys, no explanations):
{{
    "id": <KnowledgeBaseID or null>,
    "name": <KnowledgeBaseName or null>
}}"""

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
            "model": "gpt-4o",
        }

    async def determine_web_search_needed(
        self, body: dict, __user__: Optional[dict]
    ) -> Optional[dict]:
        """
        사용자의 메시지를 바탕으로 웹 검색이 필요한지 여부만 별도로 판단한다.
        - 출력 예시:
            {
                "web_search_enabled": True or False
            }
        """
        messages = body["messages"]
        user_message = get_last_user_message(messages)

        system_prompt = """You are a system that determines if a web search is needed for the user's query.
If real-time or up-to-date information is essential (e.g., news, current events, etc.), set "web_search_enabled" to true. Otherwise, set it to false.

Return the result in the following JSON format:
{
    "web_search_enabled": boolean
}"""

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
            "model": "gpt-4o",
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
            kb_result = parse_json_content(kb_content)
            selected_knowledge_base = kb_result.get("id") if kb_result else None

            ###################################################################
            # 2) 웹 검색 필요 여부 판단
            ###################################################################
            ws_plan = await self.determine_web_search_needed(body, __user__)
            if ws_plan is None:
                raise ValueError("determine_web_search_needed result is None")

            ws_payload = {
                "model": ws_plan["model"],
                "messages": [
                    {"role": "system", "content": ws_plan["system_prompt"]},
                    {"role": "user", "content": ws_plan["prompt"]},
                ],
                "stream": False,
            }

            ws_response = await generate_chat_completion(
                request=__request__, form_data=ws_payload, user=user
            )
            ws_content = (
                ws_response["choices"][0]["message"]["content"] if ws_response else ""
            )
            ws_result = parse_json_content(ws_content)

            web_search_enabled = (
                ws_result.get("web_search_enabled") if ws_result else False
            )

            # 웹 검색 로직
            if web_search_enabled:
                print("Web search required.")
                await chat_web_search_handler(
                    __request__,
                    body,
                    {"__event_emitter__": __event_emitter__},
                    user_object,
                )
            else:
                print("No web search required.")

            ###################################################################
            # 선택된 Knowledge Base가 있으면 body에 추가
            ###################################################################
            selected_knowledge_base_info = (
                Knowledges.get_knowledge_by_id(selected_knowledge_base)
                if selected_knowledge_base
                else None
            )

            if selected_knowledge_base_info:
                knowledge_file_ids = selected_knowledge_base_info.data["file_ids"]
                knowledge_files = Files.get_file_metadatas_by_ids(knowledge_file_ids)
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

        body.setdefault("messages", []).insert(0, context_message)
        return body
