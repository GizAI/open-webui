from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import os
import time
import json


class Pipeline:
    class Valves(BaseModel):
        pass

    def __init__(self):
        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, so that users can install multiple versions of the same pipeline.
        # The identifier must be unique across all pipelines.
        # The identifier must be an alphanumeric string that can include underscores or hyphens. It cannot contain spaces, special characters, slashes, or backslashes.
        # self.id = "openai_pipeline"
        self.name = "연구 파이프라인"
        self.valves = self.Valves()
        pass

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    def fake_stream_generator(self):
        """가짜 스트림 데이터를 생성하는 제너레이터 함수"""
        fake_responses = [
            {"id": "fake_id_1", "content": "안녕하세요!"},
            {"id": "fake_id_2", "content": "저는 가짜 AI 응답입니다."},
            {"id": "fake_id_3", "content": "이것은 테스트 데이터입니다."},
            {"id": "fake_id_4", "content": "0.5초 간격으로 데이터가 전송됩니다."},
            {"id": "fake_id_5", "content": "총 10초 동안 데이터가 전송됩니다."},
            {
                "id": "fake_id_6",
                "content": "이 데이터는 실제 API 호출 없이 생성됩니다.",
            },
            {"id": "fake_id_7", "content": "테스트 중입니다..."},
            {"id": "fake_id_8", "content": "곧 종료됩니다."},
            {"id": "fake_id_9", "content": "마지막 메시지입니다."},
            {"id": "fake_id_10", "content": "완료되었습니다!"},
        ]

        for i, response in enumerate(fake_responses):
            # 스트림 응답 형식을 모방
            chunk = {
                "id": f"chatcmpl-{response['id']}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "모델-테스트",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": response["content"]},
                        "finish_reason": (
                            "stop" if i == len(fake_responses) - 1 else None
                        ),
                    }
                ],
            }

            # 바이트 문자열로 변환하여 반환
            yield f"data: {json.dumps(chunk)}".encode("utf-8")

            # 0.5초 대기
            time.sleep(0.5)

        # 스트림 종료 신호
        yield b"data: [DONE]"

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        # This is where you can add your custom pipelines like RAG.
        print(f"pipe:{__name__}")

        print(messages)
        print(user_message)

        try:
            return self.fake_stream_generator()

        except Exception as e:
            return f"Error: {e}"
