import os
import asyncio
import aiohttp
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel

###############################################################################
# 검색 관련 헬퍼 기능 
###############################################################################
import requests
from datetime import datetime
import json
from requests import get
from bs4 import BeautifulSoup
import concurrent.futures
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin
import re
import unicodedata
from pydantic import BaseModel, Field
import asyncio
from typing import Callable, Any


class HelpFunctions:
    def __init__(self):
        pass

    def get_base_url(self, url):
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return base_url

    def generate_excerpt(self, content, max_length=200):
        return content[:max_length] + "..." if len(content) > max_length else content

    def format_text(self, original_text):
        soup = BeautifulSoup(original_text, "html.parser")
        formatted_text = soup.get_text(separator=" ", strip=True)
        formatted_text = unicodedata.normalize("NFKC", formatted_text)
        formatted_text = re.sub(r"\s+", " ", formatted_text)
        formatted_text = formatted_text.strip()
        formatted_text = self.remove_emojis(formatted_text)
        return formatted_text

    def remove_emojis(self, text):
        return "".join(c for c in text if not unicodedata.category(c).startswith("So"))

    def truncate_to_n_words(self, text, token_limit):
        tokens = text.split()
        truncated_tokens = tokens[:token_limit]
        return " ".join(truncated_tokens)

    def process_search_result(self, result, valves):
 
        title_site = self.remove_emojis(result["title"])
        url_site = result["url"]
        snippet = result.get("content", "")

        # 무시할 사이트는 여기서 걸러냄
        if valves.IGNORED_WEBSITES:
            base_url = self.get_base_url(url_site)
            if any(
                ignored_site.strip() in base_url
                for ignored_site in valves.IGNORED_WEBSITES.split(",")
            ):
                return None

        try:
            response_site = requests.get(url_site, timeout=20)
            response_site.raise_for_status()
            html_content = response_site.text

            soup = BeautifulSoup(html_content, "html.parser")
            content_site = self.format_text(soup.get_text(separator=" ", strip=True))

            truncated_content = self.truncate_to_n_words(
                content_site, valves.PAGE_CONTENT_WORDS_LIMIT
            )

            return {
                "title": title_site,
                "url": url_site,
                "content": truncated_content,
                "snippet": self.remove_emojis(snippet),
            }

        except requests.exceptions.RequestException:
            return None


###############################################################################
# Searxng 웹 검색 헬퍼 
###############################################################################
class Searxng:
    def __init__(self, valves: BaseModel):
        """
        Pipeline의 Valves(검색 관련 옵션 포함)를 직접 받아와서 사용.
        """
        self.valves = valves
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            )
        }
        self.functions = HelpFunctions()

    async def search_web(self, query: str) -> str:
        """
        Search the web and get the content of the relevant pages (JSON).
        """
        search_engine_url = self.valves.SEARXNG_ENGINE_API_BASE_URL

        # Ensure RETURNED_SCRAPPED_PAGES_NO does not exceed SCRAPPED_PAGES_NO
        if self.valves.RETURNED_SCRAPPED_PAGES_NO > self.valves.SCRAPPED_PAGES_NO:
            self.valves.RETURNED_SCRAPPED_PAGES_NO = self.valves.SCRAPPED_PAGES_NO

        params = {
            "q": query,
            "format": "json",
            "number_of_results": self.valves.RETURNED_SCRAPPED_PAGES_NO,
        }

        try:
            resp = requests.get(
                search_engine_url, params=params, headers=self.headers, timeout=120
            )
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            limited_results = results[: self.valves.SCRAPPED_PAGES_NO]

        except requests.exceptions.RequestException as e:
            return json.dumps({"error": str(e)})

        results_json = []
        if limited_results:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        self.functions.process_search_result, result, self.valves
                    )
                    for result in limited_results
                ]
                for future in concurrent.futures.as_completed(futures):
                    result_json = future.result()
                    if result_json:
                        try:
                            json.dumps(result_json)
                            results_json.append(result_json)
                        except (TypeError, ValueError):
                            continue
                    # 결과를 너무 많이 가져오지 않도록 제한
                    if len(results_json) >= self.valves.RETURNED_SCRAPPED_PAGES_NO:
                        break

            results_json = results_json[: self.valves.RETURNED_SCRAPPED_PAGES_NO]

        return json.dumps(results_json, ensure_ascii=False)

    async def get_website(self, url: str) -> str:
        """
        Simple web scrape of a given URL (returns JSON).
        """
        results_json = []

        try:
            response_site = requests.get(url, headers=self.headers, timeout=120)
            response_site.raise_for_status()
            html_content = response_site.text

            soup = BeautifulSoup(html_content, "html.parser")

            page_title = soup.title.string if soup.title else "No title found"
            page_title = unicodedata.normalize("NFKC", page_title.strip())
            page_title = self.functions.remove_emojis(page_title)
            title_site = page_title
            url_site = url
            content_site = self.functions.format_text(
                soup.get_text(separator=" ", strip=True)
            )

            truncated_content = self.functions.truncate_to_n_words(
                content_site, self.valves.PAGE_CONTENT_WORDS_LIMIT
            )

            result_site = {
                "title": title_site,
                "url": url_site,
                "content": truncated_content,
                "excerpt": self.functions.generate_excerpt(content_site),
            }

            results_json.append(result_site)

        except requests.exceptions.RequestException as e:
            results_json.append(
                {
                    "url": url,
                    "content": f"Failed to retrieve the page. Error: {str(e)}",
                }
            )

        return json.dumps(results_json, ensure_ascii=False)


###############################################################################
# 메인 파이프라인 클래스
###############################################################################
class Pipeline:
    """
    멀티 에이전트 파이프라인 예시 코드:
    1) messages에서 사용자 요청(user_message)와 연관 있는 정보만 추출하고 정리
    2) user_message + 정리된정보 를 GPT에 전달 -> 멀티 에이전트 필요 여부("예"/"아니오") 판단
    3) 멀티 에이전트가 필요한 경우:
        - 검색 에이전트: 연관 추가 검색어(JSON 배열) 추천받음 -> 병렬 검색
        - 정리 에이전트: 검색 결과까지 종합하여 최종 답변
    4) 필요 없다면 단일 에이전트 로직으로 즉시 응답
    """

    class Valves(BaseModel):
        # OpenAI 관련
        OPENAI_API_BASE_URL: str = "https://api.openai.com/v1"
        OPENAI_API_KEY: str = ""
        MODEL: str = "gpt-4o-mini"

        # Searxng(검색) 관련
        SEARXNG_ENGINE_API_BASE_URL: str = Field(
            default="http://45.132.75.98:8089/search",
            description="The base URL for Search Engine",
        )
        IGNORED_WEBSITES: str = Field(
            default="",
            description="Comma-separated list of websites to ignore",
        )
        RETURNED_SCRAPPED_PAGES_NO: int = Field(
            default=3,
            description="The number of Search Engine Results to Parse",
        )
        SCRAPPED_PAGES_NO: int = Field(
            default=5,
            description="Total pages scapped. Ideally greater than one of the returned pages",
        )
        PAGE_CONTENT_WORDS_LIMIT: int = Field(
            default=5000,
            description="Limit words content for each page.",
        )
        CITATION_LINKS: bool = Field(
            default=False,
            description="If True, (previously) used for custom citations with links",
        )

    def __init__(self):
        self.name = "Web Search Pipeline"
        # 외부 환경변수 등에 따라 유연하게 설정값 주입
        self.valves = self.Valves(
            **{
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "your-openai-api-key-here"),
                "MODEL": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            }
        )

        # Searxng 인스턴스화 시점에 Pipeline의 Valves(검색 관련 옵션 등)를 넘겨주어 사용
        self.searxng = Searxng(self.valves)

    async def on_startup(self):
        print(f"on_startup: {__name__}")

    async def on_shutdown(self):
        print(f"on_shutdown: {__name__}")

    async def on_valves_updated(self):
        print(f"on_valves_updated: {__name__}")

    ###########################################################################
    # 검색 헬퍼
    ###########################################################################
    async def search_web_helper(self, query: str) -> str:
        """
        Pipeline 내부에서 웹 검색을 호출할 수 있도록 만든 헬퍼 메서드.
        - Searxng.search_web(query)를 직접 호출
        - 응답은 JSON 문자열 형태로 반환
        """
        search_results_json = await self.searxng.search_web(query)
        return search_results_json

    ###########################################################################
    # GPT 호출 헬퍼
    ###########################################################################
    async def _call_openai_chat(self, session: aiohttp.ClientSession, messages: List[dict], stream: bool = False):
        """
        OpenAI ChatCompletion API를 호출하는 헬퍼 함수
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

    ###########################################################################
    # (1) messages 중 필요한 항목만 추출하여 요약(정리)하는 함수
    ###########################################################################
    async def _filter_and_summarize_messages(
        self,
        session: aiohttp.ClientSession,
        user_message: str,
        messages: List[dict]
    ) -> str:
        """
        주어진 messages 중 user_message와 직접적으로 연관 있는 부분만 추출 & 간단 요약
        요약된 텍스트(예: consolidated_context)를 문자열 형태로 리턴
        """
        # 간단한 system 프롬프트 예시
        system_prompt = """당신은 비서 역할입니다.
사용자의 최종 질문(user_message)과 관련이 있는 messages만 골라서 추출하세요
불필요하거나 관련 없는 메시지는 제외하세요. 요약하지 마세요
출력은 '정리된 텍스트' 형태의 자연어로만 주세요. 
"""
        # user_message와 messages 내용을 합쳐서 GPT에 보냄
        merged_prompt = (
            f"사용자 최종 질문:\n{user_message}\n\n"
            f"기존 메시지들:\n{messages}\n\n"
            "이 둘을 비교해, 사용자 질문과 직접 연관된 메시지만 간단 요약해줘."
        )
        input_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": merged_prompt},
        ]

        data = await self._call_openai_chat(session, input_messages)
        summarized = data["choices"][0]["message"]["content"].strip()
        return summarized

    ###########################################################################
    # (2) 멀티 에이전트 필요 여부 판단
    ###########################################################################
    async def _ask_multi_agent_needed(
        self,
        session: aiohttp.ClientSession,
        user_message: str,
        consolidated_context: str
    ) -> bool:
        """
        user_message + consolidated_context를 종합하여 
        '최신 웹 검색 필요 + 보고서 형태/종합 판단이 필요한지' 여부를 GPT에게 물어봄.
        답변은 "예" 또는 "아니오"만 출력.
        """
        system_prompt = """당신은 판단 에이전트입니다.
사용자의 질문이 복합적 분석, 최신 정보(웹 검색) 필요, 보고서 형태 요구 등을 포함한다면 "1" 
단순 답변이면 "0" 만 출력하세요.
답변은 반드시 한 글자(예 또는 아니오)가 아닌, 숫자(1 또는 0)만 출력합니다.
"""
        user_prompt = (
            f"사용자 질문:\n{user_message}\n\n"
            f"정리된 메시지:\n{consolidated_context}\n\n"
            "멀티 에이전트가 필요한가? (1/0 으로만 답변)"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        data = await self._call_openai_chat(session, messages)
        answer = data["choices"][0]["message"]["content"].strip()

        if "1" in answer:
            return True
        else:
            return False

    ###########################################################################
    # (3-1) 검색 에이전트 -> 추가 검색어 추천
    ###########################################################################
    async def _search_agent_suggest_keywords(
        self,
        session: aiohttp.ClientSession,
        user_message: str,
        consolidated_context: str
    ) -> List[str]:
        """
        검색 에이전트: 사용자 프롬프트 + 정리된 정보를 바탕으로
        '아주 중요한 추가 검색어'를 JSON 배열 형태로 반환받음.
        예: ["키워드1", "키워드2"] 
        """
        system_prompt = """당신은 검색 에이전트입니다.
사용자 질문과 관련된 '추가 검색어'를 찾아야 합니다.
최신 정보를 얻기 위해 필요한 키워드나 구체적 검색어를 1~3개 정도 추천해 주세요.
출력은 반드시 ["검색어1", "검색어2", ...] 형태의 JSON 배열로만 주세요. 다른 말은 하지 마세요.
"""
        user_prompt = (
            f"사용자 질문:\n{user_message}\n\n"
            f"정리된 메시지:\n{consolidated_context}\n\n"
            "중요한 추가 검색어들만 JSON 배열로 알려줘."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        data = await self._call_openai_chat(session, messages)
        keywords_str = data["choices"][0]["message"]["content"].strip()

        # JSON 파싱 시도
        try:
            suggested_keywords = json.loads(keywords_str)
            if isinstance(suggested_keywords, list):
                return suggested_keywords
            else:
                return []
        except:
            return []

    ###########################################################################
    # (3-2) 정리 에이전트 -> 검색 결과와 기존 맥락 종합 최종 답변
    ###########################################################################
    async def _summary_agent_final_answer(
        self,
        session: aiohttp.ClientSession,
        user_message: str,
        consolidated_context: str,
        search_results_list: List[str],
    ) -> str:
        """
        정리 에이전트: 
        - user_message + consolidated_context + (병렬 검색결과)를 모두 종합해서 최종 답변을 만듦
        - search_results_list는 각 검색어에 대한 JSON 결과 문자열들의 목록
        """
        # 각 검색 키워드 결과를 순회하며 요약
        combined_search_summary = ""
        for idx, sr_json in enumerate(search_results_list):
            combined_search_summary += f"\n\n[검색 {idx+1} 결과] {sr_json}"

        system_prompt = """당신은 종합 정리 에이전트입니다.
아래 자료(사용자 질문, 정리된 메시지, 검색 결과)를 종합하여 
가장 최적의 답변을 자세히 작성해 주세요.
"""
        user_prompt = (
            f"사용자 질문:\n{user_message}\n\n"
            f"정리된 메시지:\n{consolidated_context}\n\n"
            f"검색 결과:\n{combined_search_summary}\n\n"
            "위 정보를 모두 종합해서 최종 답변을 작성해주세요."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        data = await self._call_openai_chat(session, messages)
        final_answer = data["choices"][0]["message"]["content"].strip()
        return final_answer

    ###########################################################################
    # 멀티 에이전트 파이프라인 메인 로직
    ###########################################################################
    async def pipe_async(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        1) messages에서 user_message와 관련있는 부분만 요약(consolidated_context)
        2) user_message + consolidated_context -> GPT에게 물어봐서 멀티 에이전트 필요 여부 판단("1"/"0")
        3) 필요하다면(1) -> 검색 에이전트로 추가 키워드 추천 -> 병렬 검색 -> 정리 에이전트로 최종 답변
           아니면(0) -> 기존 단일 에이전트 로직(직접 OpenAI 호출)
        """
        print(f"pipe_async: {__name__}")

        # 불필요한 key 제거
        for key in ["user", "chat_id", "title"]:
            body.pop(key, None)

        async with aiohttp.ClientSession() as session:
            # (1) messages 필터링 및 요약
            consolidated_context = await self._filter_and_summarize_messages(
                session, user_message, messages
            )
            print("\n[DEBUG] consolidated_context:\n", consolidated_context)

            # (2) 멀티 에이전트가 필요한지 여부 판단
            is_multi_needed = await self._ask_multi_agent_needed(
                session, user_message, consolidated_context
            )
            print(f"[DEBUG] Multi-agent needed? -> {is_multi_needed}")

            if is_multi_needed:
                print("[INFO] 멀티 에이전트 로직 시작")

                # (3-1) 검색 에이전트 -> 추가 검색어 추천
                suggested_keywords = await self._search_agent_suggest_keywords(
                    session, user_message, consolidated_context
                )
                print("[DEBUG] suggested_keywords:", suggested_keywords)

                # 해당 추천 검색어 각각에 대해 병렬로 웹 검색
                search_tasks = []
                for kw in suggested_keywords:
                    search_tasks.append(
                        asyncio.create_task(self.search_web_helper(kw))
                    )
                search_results_list = await asyncio.gather(*search_tasks)

                # (3-2) 정리 에이전트 -> 최종 종합
                final_answer = await self._summary_agent_final_answer(
                    session,
                    user_message,
                    consolidated_context,
                    search_results_list,
                )
                return final_answer
            else:
                # 단일 에이전트 로직: 그냥 GPT 한 번 호출로 끝낸다고 가정
                print("[INFO] 단일 에이전트 로직")
                # 기존 messages + user_message 를 활용하여 바로 API 호출
                modified_messages = [
                    {
                        "role": "system",
                        "content": "당신은 단일 에이전트입니다. 사용자 질문에 간단히 답하세요."
                    },
                    {"role": "assistant", "content": f"정리된 메시지: {consolidated_context}"},
                    {"role": "user", "content": user_message},
                ]
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
