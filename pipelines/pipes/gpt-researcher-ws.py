from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import os
import time
import json
import asyncio
import websockets
from urllib.parse import urlparse
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("WebSocketClient")


class Pipeline:
    class Valves(BaseModel):
        websocket_url: str = "ws://127.0.0.1:8000/ws"

    def __init__(self):
        self.name = "연구 파이프라인"
        self.valves = self.Valves()
        pass

    async def websocket_stream_generator(self, user_message, model_id, messages, body):
        """웹소켓을 통해 데이터를 받아 스트림으로 전달하는 제너레이터 함수"""
        try:
            # 웹소켓 URL 파싱
            parsed_url = urlparse(self.valves.websocket_url)
            ws_host = parsed_url.netloc
            ws_path = parsed_url.path

            logger.info(f"웹소켓 연결 시도: {self.valves.websocket_url}")

            # 웹소켓 연결
            async with websockets.connect(
                self.valves.websocket_url, extra_headers={"Origin": f"http://{ws_host}"}
            ) as websocket:
                logger.info(f"웹소켓 연결 성공: {self.valves.websocket_url}")

                # 메시지 전송 - 'start {JSON}' 형식으로 변경
                request_data = {
                    "task": body.get("task", user_message),
                    "report_type": body.get("report_type", "research_report"),
                    "report_source": body.get("report_source", "web"),
                    "source_urls": body.get("source_urls", []),
                    "tone": body.get("tone", "Objective"),
                    "agent": body.get("agent", "Auto Agent"),
                    "query_domains": body.get("query_domains", []),
                    "language": body.get("language", "korean"),
                }

                # 'start {JSON}' 형식으로 요청 전송
                start_command = f"start {json.dumps(request_data)}"
                logger.info(f"웹소켓 요청 전송: {start_command[:100]}...")
                await websocket.send(start_command)
                logger.info("웹소켓 요청 전송 완료")

                # 응답 수신 및 전달
                response_count = 0
                while True:
                    logger.info("웹소켓 응답 대기 중...")
                    response = await websocket.recv()
                    response_count += 1

                    if response == "[DONE]":
                        logger.info("웹소켓 응답 완료 신호 [DONE] 수신")
                        yield b"data: [DONE]"
                        break

                    # 응답 로그 (너무 길면 일부만 출력)
                    log_response = response
                    if len(log_response) > 100:
                        log_response = log_response[:100] + "..."
                    logger.info(f"웹소켓 응답 #{response_count} 수신: {log_response}")

                    # 응답을 스트림 형식으로 변환하여 전달
                    try:
                        # 이미 JSON 형식이면 OpenAI 스트림 형식으로 변환
                        json_data = json.loads(response)
                        logger.info(
                            f"JSON 응답 처리 (키: {list(json_data.keys()) if isinstance(json_data, dict) else 'not a dict'})"
                        )

                        # 응답 데이터를 OpenAI 스트림 형식으로 변환
                        if (
                            isinstance(json_data, dict)
                            and "type" in json_data
                            and "output" in json_data
                        ):
                            # 연구 보고서 형식 응답 처리
                            content = json_data.get("output", "")
                            chunk = {
                                "id": f"chatcmpl-{int(time.time())}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model_id,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {"content": content},
                                        "finish_reason": None,
                                    }
                                ],
                            }
                            yield f"data: {json.dumps(chunk)}".encode("utf-8")
                        else:
                            # 일반 JSON 응답 처리
                            yield f"data: {json.dumps(json_data)}".encode("utf-8")
                    except json.JSONDecodeError:
                        # 일반 텍스트인 경우 스트림 형식으로 변환
                        logger.info("일반 텍스트 응답 처리")
                        chunk = {
                            "id": f"chatcmpl-{int(time.time())}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model_id,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": response},
                                    "finish_reason": None,
                                }
                            ],
                        }
                        yield f"data: {json.dumps(chunk)}".encode("utf-8")

                logger.info(f"웹소켓 통신 완료: 총 {response_count}개 응답 수신")

        except Exception as e:
            logger.error(f"웹소켓 오류 발생: {str(e)}", exc_info=True)
            error_chunk = {
                "id": f"error-{int(time.time())}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_id,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": f"웹소켓 오류: {str(e)}"},
                        "finish_reason": "error",
                    }
                ],
            }
            yield f"data: {json.dumps(error_chunk)}".encode("utf-8")
            yield b"data: [DONE]"

    def sync_websocket_generator(self, user_message, model_id, messages, body):
        """비동기 제너레이터를 동기 제너레이터로 변환하는 래퍼 함수"""
        # 새 이벤트 루프 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        logger.info(
            f"동기 웹소켓 제너레이터 시작: user_message={user_message}, model_id={model_id}"
        )

        # 비동기 제너레이터 가져오기
        async_gen = self.websocket_stream_generator(
            user_message, model_id, messages, body
        )

        try:
            # 비동기 제너레이터에서 다음 항목을 가져오는 코루틴
            async def get_next_item():
                try:
                    return await async_gen.__anext__()
                except StopAsyncIteration:
                    return None

            # 항목이 없을 때까지 반복
            item_count = 0
            while True:
                # 다음 항목 가져오기
                logger.info(f"다음 항목 가져오기 시도 #{item_count+1}")
                item = loop.run_until_complete(get_next_item())
                if item is None:
                    logger.info("더 이상 항목이 없음, 제너레이터 종료")
                    break
                item_count += 1
                logger.info(
                    f"항목 #{item_count} 반환: {item[:50] if isinstance(item, bytes) else str(item)[:50]}..."
                )
                yield item

            logger.info(f"동기 웹소켓 제너레이터 완료: 총 {item_count}개 항목 처리")

        finally:
            # 루프 닫기
            logger.info("이벤트 루프 종료")
            loop.close()

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:

        try:
            logger.info(
                f"파이프 함수 시작: user_message={user_message}, model_id={model_id}"
            )

            # 동기 제너레이터 사용
            logger.info("웹소켓 스트림 생성기 사용")
            return self.sync_websocket_generator(user_message, model_id, messages, body)

        except Exception as e:
            logger.error(f"파이프 함수 오류: {str(e)}", exc_info=True)
            return f"Error: {e}"
