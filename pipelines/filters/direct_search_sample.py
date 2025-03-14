from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any, Optional
from open_webui.utils.middleware import chat_web_search_handler
from open_webui.models.users import UserModel
from typing import Callable, Awaitable, Any, Optional, TypedDict, List, Dict, Union

from open_webui.routers.retrieval import process_web_search, SearchForm


class Doc(TypedDict):
    # 문서의 실제 내용
    content: str
    # 메타데이터 예시:
    # - source: 문서 출처 URL (예: "https://en.wikipedia.org/wiki/NewJeans")
    # - title: 문서 제목 (예: "NewJeans - Wikipedia") 
    # - language: 문서 언어 코드 (예: "en")
    metadata: Dict[str, Any]

class SearchResultWithDocs(TypedDict):
    status: bool
    collection_name: None
    # filenames: 검색 결과 URL 목록
    filenames: List[str]
    docs: List[Doc]
    loaded_count: int

class SearchResultWithoutDocs(TypedDict):
    status: bool
    collection_name: str
    filenames: List[str]
    loaded_count: int

SearchResult = Union[SearchResultWithDocs, SearchResultWithoutDocs]

async def web_search(request: any, query: str) -> SearchResult:
    request.app.state.config.BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL = True
    form_data = SearchForm(query=query)
    
    try:
        result = await process_web_search(request, form_data)
        return {
            "docs": result.get("docs", []),
            "name": query,
            "type": "web_search",
            "urls": result["filenames"],
        }
    except Exception as e:
        print(f"웹 검색 중 오류 발생: {str(e)}")
        return {
            "status": False,
            "collection_name": None,
            "filenames": [],
            "loaded_count": 0
        }


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

            result = await web_search(__request__, "Newjeans")
            
            print("############################################ start ##############################################")
            print(result)
            print(body)
            print("################################################ end #########################################")
            
            # "files" 키가 없으면 생성
            if "files" not in body:
                body["files"] = []
                
            # 결과 추가
            body["files"].append(result)
        except Exception as e:
            print(f"오류 발생: {str(e)}")
        return body

