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

    def process_search_result(self, result, valves):
        title_site = self.remove_emojis(result["title"])
        url_site = result["url"]
        snippet = result.get("content", "")

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

    def truncate_to_n_words(self, text, token_limit):
        tokens = text.split()
        truncated_tokens = tokens[:token_limit]
        return " ".join(truncated_tokens)


class Tools:
    class Valves(BaseModel):
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
        self.valves = self.Valves()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

    async def search_web(self, query: str) -> str:
        """
        Search the web and get the content of the relevant pages (JSON).
        """
        functions = HelpFunctions()
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
                        functions.process_search_result, result, self.valves
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
        functions = HelpFunctions()
        results_json = []

        try:
            response_site = requests.get(url, headers=self.headers, timeout=120)
            response_site.raise_for_status()
            html_content = response_site.text

            soup = BeautifulSoup(html_content, "html.parser")

            page_title = soup.title.string if soup.title else "No title found"
            page_title = unicodedata.normalize("NFKC", page_title.strip())
            page_title = functions.remove_emojis(page_title)
            title_site = page_title
            url_site = url
            content_site = functions.format_text(
                soup.get_text(separator=" ", strip=True)
            )

            truncated_content = functions.truncate_to_n_words(
                content_site, self.valves.PAGE_CONTENT_WORDS_LIMIT
            )

            result_site = {
                "title": title_site,
                "url": url_site,
                "content": truncated_content,
                "excerpt": functions.generate_excerpt(content_site),
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
        # Tools 인스턴스 (웹 검색 헬퍼)
        self.tools = Tools()

    async def on_startup(self):
        print(f"on_startup: {__name__}")

    async def on_shutdown(self):
        print(f"on_shutdown: {__name__}")

    async def on_valves_updated(self):
        print(f"on_valves_updated: {__name__}")

    ###########################################################################
    # 아래 부분: 검색 결과를 알아내는 헬퍼
    ###########################################################################
    async def search_web_helper(self, query: str) -> str:
        """
        Pipeline 내부에서 웹 검색을 호출할 수 있도록 만든 헬퍼 메서드.
        - Tools.search_web(query)를 직접 호출
        - 응답은 JSON 문자열 형태로 반환
        """
        search_results_json = await self.tools.search_web(query)
        return search_results_json

    ###########################################################################
    # OpenAI API 헬퍼
    ###########################################################################
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

    async def _agent_worker(
        self, 
        session: aiohttp.ClientSession, 
        role: str, 
        user_prompt: str,
        additional_messages: List[dict]
    ) -> str:
        """
        에이전트별로 서로 다른 system 프롬프트를 구성하여 병렬로 호출.
        role 매개변수를 통해 다른 에이전트가 될 수 있도록 설정.
        + 기존 messages(추가된 정보 포함)도 함께 전달
        """
        system_prompt = f"""당신은 {role} 분야의 전문 에이전트입니다.
이 사용자 요청에 대해, {role} 분야 관점에서 필요한 정보를 수집하기 위해 검색 및 분석/추론을 여러 단계 거쳐 최선의 답을 도출해보세요.
반드시 단계별 접근 방식으로 생각하고, 자세한 결론을 작성 하시오
"""

        # system 프롬프트 + 기존 messages + 이번 user_prompt를 합침
        merged_messages = [
            {"role": "system", "content": system_prompt},
            *additional_messages,
            {"role": "user", "content": user_prompt},
        ]

        data = await self._call_openai_chat(session, merged_messages)
        result = data["choices"][0]["message"]["content"]
        return result

    def _needs_multi_agents(self, user_message: str) -> bool:
        """
        간단한 로직으로 멀티 에이전트가 필요한지 여부를 판별하는 예시.
        (예: 메시지 길이가 길거나 특정 키워드가 있으면 멀티에이전트로 분기)
        """
        keywords = ["분석", "비교", "종합", "복합", "프로젝트", "연구", "보고"]
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
                agent_roles = ["검색", "분석", "요약"]  
                tasks = []
                for role in agent_roles:
                    tasks.append(
                        asyncio.create_task(
                            self._agent_worker(session, role, user_message, messages)
                        )
                    )
                
                # 병렬 실행 후 결과 수집
                results = await asyncio.gather(*tasks)
                
                # 중간결과를 취합하여 최종 요약을 구한다
                combined_content = "\n\n".join(
                    f"{agent_roles[i]} 에이전트 응답:\n{res}" for i, res in enumerate(results)
                )

                # 최종 요약/응답을 얻기 위해 다시 한 번 OpenAI에 요청
                final_system_prompt = """당신은 멀티 에이전트 시스템의 최종 종합 에이전트입니다.
아래 여러 에이전트의 응답을 종합하여, 사용자에게 줄 최종 답변을 자세하게 보기 좋게 포멧팅해서 답변하세요. 중요한 정보는 빠뜨리지 마세요.
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
        print("---------------------------------- message ----------------------------------")
        print(messages)
        print("---------------------------------- user_message ----------------------------------")
        print(user_message)
        print("---------------------------------- body ----------------------------------")
        print(body)
        
        return asyncio.run(self.pipe_async(user_message, model_id, messages, body))
