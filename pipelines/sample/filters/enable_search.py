from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any, Optional
from open_webui.utils.middleware import chat_web_search_handler
from open_webui.models.users import UserModel


class Filter:
    class Valves(BaseModel):
        status: bool = Field(default=True)


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

        
    def __init__(self):
        self.valves = self.Valves()

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __request__: Any,
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        try:
            user_data = __user__.copy()
            user_data.update({
                "profile_image_url": "",
                "last_active_at": 0,
                "updated_at": 0,
                "created_at": 0
            })

            user_object = UserModel(**user_data)

            if not body.get("features", {}).get("web_search", False):
                await self.emit_status(__event_emitter__, "info", "Web search enabled", True)
                await chat_web_search_handler(__request__, body, {"__event_emitter__": __event_emitter__}, user_object)
                
        except Exception as e:
            print(e)
        return body

