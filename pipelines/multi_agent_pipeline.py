import os
import asyncio
import aiohttp
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel

class Pipeline:
    """
    멀티 에이전트 파이프라인 예시 코드:
    - 사용자 프롬프트를 기반으로 멀티 에이전트 사용 여부를 판단
    - 필요한 경우 에이전트 병렬 호출 (웹 요청)
    - 모든 결과를 종합하여 최종 결과만 반환
    """

    class Valves(BaseModel):
        OPENAI_API_BASE_URL: str = "https://api.openai.com/v1"
        OPENAI_API_KEY: str = ""
        MODEL: str = "gpt-4o-mini"

    def __init__(self):
        self.name = "MultiAgent Parallel Pipeline"
        self.valves = self.Valves(
            **{
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "your-openai-api-key-here"),
                "MODEL": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            }
        )

    async def on_startup(self):
        print(f"on_startup: {__name__}")

    async def on_shutdown(self):
        print(f"on_shutdown: {__name__}")

    async def on_valves_updated(self):
        print(f"on_valves_updated: {__name__}")

    async def _call_openai_chat(self, session: aiohttp.ClientSession, messages: List[dict], stream: bool = False):
        """
        OpenAI ChatCompletion API를 호출하는 헬퍼 함수
        (stream 모드의 처리는 간단화를 위해 생략/혹은 필요에 따라 구현)
        """
        headers = {
            "Authorization": f"Bearer {self.valves.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.valves.MODEL,
            "messages": messages,
            "temperature": 0.7,
        }
        url = f"{self.valves.OPENAI_API_BASE_URL}/chat/completions"

        async with session.post(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data

    async def _agent_worker(self, session: aiohttp.ClientSession, role: str, user_prompt: str) -> str:
        """
        에이전트별로 서로 다른 system 프롬프트를 구성하여 병렬로 호출.
        role 매개변수를 통해 다른 에이전트가 될 수 있도록 설정.
        """
        system_prompt = f"""당신은 {role} 분야의 전문 에이전트입니다.
이 사용자 요청에 대해, {role} 분야 관점에서 필요한 정보를 수집하기 위해 웹검색 및 분석/추론을 여러 단계 거쳐 최선의 답을 도출해보세요.
반드시 단계별 접근 방식으로 생각하고, 자세한 결론을 작성 하시오
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        data = await self._call_openai_chat(session, messages)
        # OpenAI의 ChatCompletion 응답 중 어시스턴트 메시지 추출
        result = data["choices"][0]["message"]["content"]
        return result

    def _needs_multi_agents(self, user_message: str) -> bool:
        """
        간단한 로직으로 멀티 에이전트가 필요한지 여부를 판별하는 예시.
        (예: 메시지 길이가 길거나 특정 키워드가 있으면 멀티에이전트로 분기)
        """
        keywords = ["분석", "비교", "종합", "복합", "프로젝트", "연구","보고"]
        if any(keyword in user_message for keyword in keywords) or len(user_message) > 30:
            return True
        return False

    async def pipe_async(
        self,
        user_message: str,
        model_id: str,   # (더 이상 사용되지 않지만 시그니처 유지)
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        멀티에이전트 로직을 수행하는 파이프라인의 핵심 메서드 (비동기 버전).
        내부에서 사용자 프롬프트를 분석해서 멀티 에이전트가 필요한 경우
        여러 에이전트를 병렬로 호출하고 결과를 종합해 최종 답변을 생성합니다.
        """
        print(f"pipe_async: {__name__}")

        # 멀티 에이전트 필요 여부 판단
        use_multi_agents = self._needs_multi_agents(user_message)
        
        async with aiohttp.ClientSession() as session:
            if use_multi_agents:
                # 여러 에이전트를 병렬 호출
                print("[INFO] 멀티 에이전트 로직 시작")
                agent_roles = ["검색", "분석", "요약"]  # 예시로 3개
                tasks = []
                for role in agent_roles:
                    tasks.append(asyncio.create_task(self._agent_worker(session, role, user_message)))
                
                # 병렬 실행 후 결과 수집
                results = await asyncio.gather(*tasks)
                
                # 중간결과를 취합하여 최종 요약을 구한다
                combined_content = "\n\n".join(
                    f"{agent_roles[i]} 에이전트 응답:\n{res}" for i, res in enumerate(results)
                )

                # 최종 요약/응답을 얻기 위해 다시 한 번 OpenAI에 요청
                # messages 파라미터를 사용하여, 기존 대화 히스토리를 활용할 수도 있음
                final_system_prompt = """당신은 멀티 에이전트 시스템의 최종 종합 에이전트입니다.
아래 여러 에이전트의 응답을 종합하여, 사용자에게 줄 최종 답변을 완성하세요.
가능하면 간결하게 요약하되, 중요한 정보는 빠뜨리지 마세요.
"""
                final_messages = [
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": combined_content},
                ]
                final_data = await self._call_openai_chat(session, final_messages)
                final_answer = final_data["choices"][0]["message"]["content"]
                return final_answer
            else:
                # 단일 에이전트(기존 로직) 사용 예시
                print("[INFO] 단일 에이전트 로직")
                # 기존 messages + user_message 를 활용하여 바로 API 호출
                modified_messages = [
                    *messages,
                    {"role": "user", "content": user_message},
                ]

                # 불필요한 key 제거
                for key in ["user", "chat_id", "title"]:
                    body.pop(key, None)
                
                data = await self._call_openai_chat(session, modified_messages, body.get("stream", False))
                single_answer = data["choices"][0]["message"]["content"]
                return single_answer

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        asyncio.run()을 통해 비동기 함수(pipe_async)를 동기처럼 동작시키는 래퍼.
        """
        return asyncio.run(self.pipe_async(user_message, model_id, messages, body))
