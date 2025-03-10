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
            default="deep",
            description="The type of report to generate",
        )
        language: str = Field(
            default="korean",
            description="The language to use for the research report",
        )
        deep_research_breadth: int = Field(
            default=4,
            description="Number of parallel research paths at each level",
        )
        deep_research_depth: int = Field(
            default=2,
            description="How many levels deep to explore",
        )
        deep_research_concurrency: int = Field(
            default=4,
            description="Maximum number of concurrent research operations",
        )
        total_words: int = Field(
            default=4000,
            description="Total words in the generated report",
        )

    def __init__(self) -> None:
        self.valves = self.Valves()
        self.name: str = "GPT Researcher Pipeline(Deep)"
        self.researcher: GPTResearcher = None

    def _set_api_keys(self) -> None:

        os.environ["OPENAI_API_KEY"] = self.valves.openai_api_key
        os.environ["TAVILY_API_KEY"] = self.valves.tavily_api_key

    def _set_deep_research_config(self) -> None:
        """Deep Research 설정을 환경 변수에 설정하는 메서드"""
        os.environ["DEEP_RESEARCH_BREADTH"] = str(self.valves.deep_research_breadth)
        os.environ["DEEP_RESEARCH_DEPTH"] = str(self.valves.deep_research_depth)
        os.environ["DEEP_RESEARCH_CONCURRENCY"] = str(
            self.valves.deep_research_concurrency
        )
        os.environ["TOTAL_WORDS"] = str(self.valves.total_words)

    async def conduct_research(self, query: str) -> str:
        self._set_api_keys()
        self._set_deep_research_config()

        try:
            self.researcher = GPTResearcher(
                query=query,
                report_type=self.valves.report_type,
                language=self.valves.language,
            )
            await self.researcher.conduct_research()
            report = await self.researcher.write_report()

            return report
        except Exception as e:
            return f"연구 수행 중 오류가 발생했습니다: {str(e)}"

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[Dict[str, Any]],
        body: Dict[str, Any],
    ) -> str:
        return asyncio.run(self.conduct_research(user_message))
