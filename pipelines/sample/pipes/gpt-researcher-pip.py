from typing import List, Union, Generator, Iterator, Dict, Any
from pydantic import BaseModel, Field
from gpt_researcher import GPTResearcher
import asyncio
import os


class Pipeline:
    class Valves(BaseModel):
        """파이프라인 설정을 위한 밸브 클래스"""

        openai_api_key: str = ""
        tavily_api_key: str = ""
        report_type: str = Field(
            default="research_report",
            description="The type of report to generate",
        )
        language: str = Field(
            default="korean",
            description="The language to use for the research report",
        )

    def __init__(self) -> None:
        """파이프라인 초기화"""
        self.valves = self.Valves()
        self.name: str = "GPT Researcher Pipeline"
        self.researcher: GPTResearcher = None

    async def on_startup(self) -> None:
        """서버 시작 시 호출되는 메서드"""
        print(f"Starting GPT Researcher Pipeline: {__name__}")

    async def on_shutdown(self) -> None:
        """서버 종료 시 호출되는 메서드"""
        print(f"Shutting down GPT Researcher Pipeline: {__name__}")

    async def inlet(self, body: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """요청 전처리 메서드"""
        print(f"Processing inlet request: {__name__}")
        return body

    async def outlet(
        self, body: Dict[str, Any], user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """응답 후처리 메서드"""
        print(f"Processing outlet response: {__name__}")
        return body

    def _set_api_keys(self) -> None:
        """API 키를 환경 변수에 설정하는 메서드"""
        if self.valves.openai_api_key:
            os.environ["OPENAI_API_KEY"] = self.valves.openai_api_key

        if self.valves.tavily_api_key:
            os.environ["TAVILY_API_KEY"] = self.valves.tavily_api_key

    async def conduct_research(self, query: str) -> Dict[str, Any]:
        """
        주어진 쿼리에 대한 연구를 수행하는 메서드

        Args:
            query (str): 연구할 주제 또는 질문

        Returns:
            Dict[str, Any]: 연구 결과, 소스, 컨텍스트 및 비용 정보를 포함한 딕셔너리
        """
        try:
            # API 키를 환경 변수에 설정
            self._set_api_keys()

            self.researcher = GPTResearcher(
                query=query,
                report_type=self.valves.report_type,
                language=self.valves.language,
            )
            research_result = await self.researcher.conduct_research()
            report = await self.researcher.write_report()

            return {
                "report": report,
                "sources": self.researcher.get_source_urls(),
                "context": self.researcher.get_research_context(),
                "costs": self.researcher.get_costs(),
            }
        except Exception as e:
            return {"error": str(e)}

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[Dict[str, Any]],
        body: Dict[str, Any],
    ) -> Union[str, Generator, Iterator]:
        """
        파이프라인의 주요 처리 메서드

        Args:
            user_message (str): 사용자의 연구 요청 메시지
            model_id (str): 사용할 모델 ID
            messages (List[Dict[str, Any]]): 이전 메시지 기록
            body (Dict[str, Any]): 요청 본문

        Returns:
            str: 포맷팅된 연구 결과
        """
        print(f"Processing research request: {__name__}")

        # API 키를 환경 변수에 설정
        self._set_api_keys()

        research_results = asyncio.run(self.conduct_research(user_message))

        if "error" in research_results:
            return f"연구 중 오류가 발생했습니다: {research_results['error']}"

        return f"""연구 결과:

{research_results['report']}

참고 소스:
{', '.join(research_results['sources'])}

비용 정보:
{research_results['costs']}
"""
