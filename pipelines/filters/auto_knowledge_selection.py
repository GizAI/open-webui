"""
title: AutoTool Filter
author: open-webui
author_url: https://github.com/open-webui
funding_url: https://github.com/open-webui
version: 0.2.0
required_open_webui_version: 0.5.0
"""

from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any, Optional, Literal
import json
import re

# 업데이트된 임포트
from open_webui.models.users import Users
from open_webui.models.tools import Tools
from open_webui.models.models import Models
from open_webui.utils.chat import generate_chat_completion  # 경량 옵션 사용
from open_webui.utils.misc import get_last_user_message

from open_webui.models.knowledge import Knowledges
from open_webui.models.files import Files


class Filter:
    class Valves(BaseModel):
        status: bool = Field(default=True)
        pass

    def __init__(self):
        self.valves = self.Valves()
        pass

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __request__: Any, 
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        messages = body["messages"]
        user_message = get_last_user_message(messages)

        print("+++++++++++++++++++++++++++++++ start body +++++++++++++++++++++++++++++++")
        print(body)
        print("+++++++++++++++++++++++++++++++ start body +++++++++++++++++++++++++++++++")

        if self.valves.status:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "적절한 도구를 찾는 중...",
                        "done": False,
                    },
                }
            )

        all_knowledge_bases = Knowledges.get_knowledge_bases_by_user_id(
            __user__.get("id"), "read"
        )

        knowledge_bases_list = "\n".join(
            [
                f"- ID: {getattr(knowledge_base, 'id', 'Unknown')}\n - 지식베이스이름: {getattr(knowledge_base, 'name', 'Unknown')}\n - 설명: {getattr(knowledge_base, 'description', 'Unknown')}\n"
                for knowledge_base in all_knowledge_bases
            ]
        )

        system_prompt = f"""사용자 프롬프트를 바탕으로 사용자가 원하는 지식 베이스를 찾아주세요.
                        사용 가능한 지식 목록:
                        {knowledge_bases_list}
                        위 모델 중에서 사용자의 요구사항에 가장 적합한 지식을 선택해주세요.
                        답변은 꼭 JSON 형식으로  "id" : 지식ID  , "name" : 지식 이름  형식으로 선택한 모델 ID 와 이름만 반환하세요 다른 설명은 하지 마세요
                        적합한 지식이 없거나 연관성이 없는 경우는 꼭 시작을 선택 할 필요 없습니다. 그럴경우 None 을 반환하세요"""
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
        payload = {
            "model": body["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }

        selected_knowledge_base = None  # Initialize to None

        try:
            user = Users.get_user_by_id(__user__["id"])
            # 직접 후속 함수 사용으로 업데이트

            response = await generate_chat_completion(
                request=__request__, form_data=payload, user=user
            )

            content = response["choices"][0]["message"]["content"]

            # 함수 응답 파싱
            if content is not None:
                
                # 1. 코드 블록 제거
                content = content.replace("```json", "").replace("```", "").strip()
                # 2. 싱글 쿼테이션 → 더블 쿼테이션
                content = content.replace("'", '"')

                # 3. 객체 JSON 추출 시도
                pattern = r"\{.*?\}"  # 객체 형태의 JSON 검출용 정규식으로 수정
                match = re.search(pattern, content, flags=re.DOTALL)
                if match:
                    content = match.group(0)
                else:
                    content = None  # If no match found, set content to None

                if content is not None:
                    try:
                        result = json.loads(content)
                    except json.JSONDecodeError as e:
                        print(f"JSONDecodeError: {e}")
                        result = None

                    selected_knowledge_base = result.get("id") if isinstance(result, dict) else None

            # If content is None or JSON parsing failed, selected_knowledge_base remains None

            selected_knowledge_base_info = Knowledges.get_knowledge_by_id(selected_knowledge_base) if selected_knowledge_base else None

            # 딕셔너리 키로 접근
            if selected_knowledge_base_info:
                knowledge_file_ids = selected_knowledge_base_info.data['file_ids']

                # 파일 메타데이터 가져오기
                knowledge_files = Files.get_file_metadatas_by_ids(knowledge_file_ids)

                # KnowledgeModel 객체를 dict로 변환하여 JSON 직렬화 가능하게 함
                knowledge_dict = selected_knowledge_base_info.model_dump()
                # 'files' 속성 추가: FileMetadataResponse 객체를 dict로 변환
                knowledge_dict['files'] = [file.model_dump() for file in knowledge_files]
                knowledge_dict['type'] = 'collection'

                body["files"] = body.get("files", []) + [knowledge_dict]

                if self.valves.status:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": f"일치하는 지식 베이스 찾음: {selected_knowledge_base_info.name}",
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
                                "description": "일치하는 지식 베이스를 찾지 못했습니다.",
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
                            "description": f"요청 처리 중 오류 발생: {e}",
                            "done": True,
                        },
                    }
                )
            pass
   


        context_message = {
            "role": "system", 
            "content": "You are ChatGPT, a large language model trained by OpenAI. Please ensure that all your responses are presented in a clear and organized manner using bullet points, numbered lists, headings, and other formatting tools to enhance readability and user-friendliness."
        }
        body.setdefault("messages", []).insert(0, context_message)

             
        print("+++++++++++++++++++++++++++++++ end body +++++++++++++++++++++++++++++++")
        print(body)
        print("+++++++++++++++++++++++++++++++ end body +++++++++++++++++++++++++++++++")

        
        return body
