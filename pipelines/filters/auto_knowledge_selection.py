from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any, Optional
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

    async def plan(self, body: dict, __user__: Optional[dict]) -> Optional[dict]:
        messages = body["messages"]
        user_message = get_last_user_message(messages)

        print("+++++++++++++++++++++++++++++++ start body +++++++++++++++++++++++++++++++")
        print(body)
        print("+++++++++++++++++++++++++++++++ start body +++++++++++++++++++++++++++++++")

        all_knowledge_bases = Knowledges.get_knowledge_bases_by_user_id(
            __user__.get("id"), "read"
        )

        knowledge_bases_list = "\n".join(
            [
                f"- ID: {getattr(knowledge_base, 'id', 'Unknown')}\n - Knowledge Base Name: {getattr(knowledge_base, 'name', 'Unknown')}\n - Description: {getattr(knowledge_base, 'description', 'Unknown')}\n"
                for knowledge_base in all_knowledge_bases
            ]
        )

        system_prompt = f"""Based on the user's prompt, please find the knowledge base that the user desires.
Available knowledge bases:
{knowledge_bases_list}
Please select the most suitable knowledge base from the above list that best fits the user's requirements.
Ensure that your response is in JSON format with only the \"id\" : KnowledgeID and \"name\" : Knowledge Name fields. Do not provide any additional explanations.
If there is no suitable or relevant knowledge base, do not select any. In such cases, return None."""

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
            "model": body["model"],
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

            
            search_result = None  
            
            user_data = __user__.copy()
            user_data.update({
                "profile_image_url": "",
                "last_active_at": 0,
                "updated_at": 0,
                "created_at": 0
            })

            user_object = UserModel(**user_data)

            if not body.get("features", {}).get("web_search", False):
                search_result = await chat_web_search_handler(__request__, body, {"__event_emitter__": __event_emitter__}, user_object)

            if search_result is not None:
                print("+++++++++++++++++++++++++++++++ search_result +++++++++++++++++++++++++++++++")
                print(search_result)
                print("+++++++++++++++++++++++++++++++ search_result +++++++++++++++++++++++++++++++")
              
               
            else:
                print("No search result was retrieved.")

            plan_result = await self.plan(body, __user__)

            if plan_result is None:
                raise ValueError("Plan result is None")

            payload = {
                "model": plan_result["model"],
                "messages": [
                    {"role": "system", "content": plan_result["system_prompt"]},
                    {"role": "user", "content": plan_result["prompt"]},
                ],
                "stream": False,
            }

            selected_knowledge_base = None
            user = Users.get_user_by_id(__user__["id"])

            response = await generate_chat_completion(
                request=__request__, form_data=payload, user=user
            )

            content = response["choices"][0]["message"]["content"]

            if content:
                content = content.replace("```json", "").replace("```", "").strip()
                content = content.replace("'", '"')
                match = re.search(r"\{.*?\}", content, flags=re.DOTALL)
                if match:
                    content = match.group(0)
                else:
                    content = None

                if content:
                    try:
                        result = json.loads(content)
                        selected_knowledge_base = result.get("id") if isinstance(result, dict) else None
                    except json.JSONDecodeError as e:
                        print(f"JSONDecodeError: {e}")

            selected_knowledge_base_info = Knowledges.get_knowledge_by_id(selected_knowledge_base) if selected_knowledge_base else None

            if selected_knowledge_base_info:
                knowledge_file_ids = selected_knowledge_base_info.data['file_ids']
                knowledge_files = Files.get_file_metadatas_by_ids(knowledge_file_ids)
                knowledge_dict = selected_knowledge_base_info.model_dump()
                knowledge_dict['files'] = [file.model_dump() for file in knowledge_files]
                knowledge_dict['type'] = 'collection'

                body["files"] = body.get("files", []) + [knowledge_dict]

                if self.valves.status:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": f"Matching knowledge base found: {selected_knowledge_base_info.name}",
                                "done": True,
                            },
                        }
                    )
            else:
                if self.valves.status:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "No matching knowledge base found.",
                                "done": True,
                            },
                        }
                    )
        except Exception as e:
            print(e)
            if self.valves.status:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Error occurred while processing the request: {e}",
                            "done": True,
                        },
                    }
                )

        context_message = {
            "role": "system", 
            "content": (
                "You are ChatGPT, a large language model trained by OpenAI. "
                "Please ensure that all your responses are presented in a clear and organized manner using bullet points, numbered lists, headings, and other formatting tools to enhance readability and user-friendliness. "
                "Additionally, please respond in the language used by the user in their input."
            )
        }
        body.setdefault("messages", []).insert(0, context_message)

        print("+++++++++++++++++++++++++++++++ end body +++++++++++++++++++++++++++++++")
        print(body)
        print("+++++++++++++++++++++++++++++++ end body +++++++++++++++++++++++++++++++")

        return body
