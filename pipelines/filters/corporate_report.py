#기업 분석 보고서
from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any, Optional
from typing import Callable, Awaitable, Any, Optional, TypedDict, List, Dict, Union
import json
import re

from open_webui.routers.retrieval import process_web_search, SearchForm
from open_webui.utils.middleware import chat_web_search_handler
from open_webui.models.users import UserModel
from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.misc import get_last_user_message
from open_webui.models.users import Users, UserModel

# JSON 추출 공통 함수
def extract_json_from_markdown(content: str) -> dict:
    """
    마크다운 형식의 문자열에서 JSON 객체를 추출합니다.
    
    Args:
        content (str): JSON을 포함한 마크다운 문자열
        
    Returns:
        dict: 추출된 JSON 객체, 추출 실패 시 빈 딕셔너리 반환
    """
    try:
        # ```json과 ``` 사이의 내용 추출
        json_match = re.search(r'```(?:json)?\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            # JSON 문자열을 객체로 변환
            return json.loads(json_str)
        else:
            # 일반 텍스트에서 JSON 형식 찾기 시도
            try:
                return json.loads(content)
            except:
                print("JSON 형식을 찾을 수 없습니다.")
                return {}
    except Exception as e:
        print(f"JSON 추출 중 오류 발생: {str(e)}")
        return {}


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

            
            user = Users.get_user_by_id(__user__["id"]) if __user__ else None

            messages = body["messages"]
            user_message = get_last_user_message(messages)

            # 사용자 질문 분석 →

            analysis_prompt = [
                {"role": "system", "content": """
                사용자가 요청한 기업 분석 질문을 분석하고 다음 정보를 JSON 형식으로 반환하세요:
                {
                    "company_name": "분석 대상 기업명",
                    "industry": "기업이 속한 산업 분야",
                    "analysis_focus": "재무분석, 경쟁력 분석, 시장 점유율, 성장성, 투자 가치 등 분석 초점",
                    "keywords": ["핵심", "키워드", "목록"],
                    "preferred_format": "보고서, 요약, 목록, 단계별 설명 등",
                    "complexity": "간단/중간/복잡 - 질문의 복잡성 수준",
                    "needs_search": true/false - 웹 검색이 필요한지 여부,
                    "needs_financial_data": true/false - 재무 데이터가 필요한지 여부,
                    "preliminary_search_keywords": ["키워드1", "키워드2", "..."] // 사전 웹 검색을 위한 키워드
                }
                
                만약 다음과 같은 경우에는 빈 객체({})만 반환하세요:
                1. 사용자의 질문에서 특정 기업명을 식별할 수 없는 경우
                2. 질문이 기업 분석이나 기업 리포트와 관련이 없는 경우
                3. 일반적인 대화나 인사말인 경우
                4. 기업 분석을 위한 충분한 정보가 제공되지 않은 경우
                5. 기업 분석이 아닌 다른 주제에 관한 질문인 경우
                
                """
                },
                {"role": "user", "content": f"다음 기업 분석 요청을 분석해주세요: {user_message}"}
            ]

            analysis_payload = {
                    "model": "o3-mini",
                    "messages": analysis_prompt,
                    "stream": False,
                }

            analysis_response = await generate_chat_completion(
                request=__request__,
                form_data=analysis_payload,
                user=user,
            )
            # analysis_response에서 content 추출
            content = analysis_response.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 공통 함수를 사용하여 JSON 객체 추출
            analysis_obj = extract_json_from_markdown(content)
            
            # 빈 객체인 경우 함수 종료
            if not analysis_obj or len(analysis_obj) == 0:
                await self.emit_status(
                    __event_emitter__,
                    level="status",
                    message="기업 분석을 위한 충분한 정보가 없습니다. 일반 대화 모드로 전환합니다.",
                    done=True,
                )
                return body
            

            websearch_keywords = analysis_obj.get("preliminary_search_keywords", [])

            # 웹 검색 결과를 저장할 리스트
            search_results = []
            
            # 각 키워드에 대한 웹 검색 수행 및 결과 저장
            for keyword in websearch_keywords:
                await self.emit_status(
                    __event_emitter__,
                    level="status",
                    message=f"키워드 '{keyword}'에 대한 웹 검색 중...",
                    done=False,
                )
                web_search_result = await web_search(__request__, keyword)
                search_results.append(web_search_result)
                
            # 검색 결과 취합
            combined_docs = []
            combined_urls = []
            
            for result in search_results:
                if "docs" in result:
                    combined_docs.extend(result.get("docs", []))
                if "urls" in result:
                    combined_urls.extend(result.get("urls", []))
                    
            # 중복 URL 제거
            combined_urls = list(dict.fromkeys(combined_urls))
            
            # 취합된 검색 결과
            combined_search_result = {
                "docs": combined_docs,
                "urls": combined_urls,
                "keywords": websearch_keywords,
                "type": "combined_web_search"
            }
            
            await self.emit_status(
                __event_emitter__,
                level="status",
                message="웹 검색 결과 취합 완료",
                done=True,
            )
            
            # 계획 생성을 위한 프롬프트 작성
            plan_prompt = [
                {"role": "system", "content": """
                당신은 기업 분석 계획을 수립하는 전문가입니다. 사용자의 기업 분석 요청과 초기 웹 검색 결과를 바탕으로 
                상세한 기업 분석 계획을 JSON 형식으로 작성해주세요:
                
                {
                    "analysis_plan": {
                        "company_name": "분석 대상 기업명",
                        "industry": "기업이 속한 산업 분야",
                        "main_question": "사용자의 주요 질문",
                        "analysis_sections": ["기업 개요", "산업 분석", "재무 분석", "경쟁사 분석", "SWOT 분석", "미래 전망", "투자 의견"],
                        "research_steps": [
                            {
                                "step": 1,
                                "description": "단계 설명 (예: 기업 기본 정보 수집)",
                                "search_queries": ["검색어 1", "검색어 2", ...],
                                "expected_outcomes": "이 단계에서 기대되는 결과"
                            },
                            ...
                        ],
                        "required_financial_data": ["매출액", "영업이익", "순이익", "부채비율", "ROE", ...],
                        "required_market_data": ["시장 규모", "시장 점유율", "경쟁사 현황", ...],
                        "information_gaps": ["현재 부족한 정보 1", "현재 부족한 정보 2", ...],
                        "estimated_completion_steps": 5
                    }
                }
                """
                },
                {"role": "user", "content": f"""
                기업 분석 요청: {user_message}
                
                초기 분석 결과: {json.dumps(analysis_obj, ensure_ascii=False)}
                
                초기 웹 검색 키워드: {websearch_keywords}

                초기 웹 검색 결과: {json.dumps(combined_search_result, ensure_ascii=False)}
                
                검색된 URL 수: {len(combined_urls)}
                검색된 문서 수: {len(combined_docs)}
                
                위 정보를 바탕으로 상세한 기업 분석 계획을 JSON 형식으로 작성해주세요.
                """}
            ]
            
            # 계획 생성 요청
            plan_payload = {
                "model": "o3-mini",
                "messages": plan_prompt,
                "stream": False,
            }
            
            await self.emit_status(
                __event_emitter__,
                level="status",
                message="연구 계획 생성 중...",
                done=False,
            )
            
            plan_response = await generate_chat_completion(
                request=__request__,
                form_data=plan_payload,
                user=user,
            )
            
            # 계획 응답에서 content 추출
            plan_content = plan_response.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # JSON 객체 추출
            research_plan = extract_json_from_markdown(plan_content)
            
            await self.emit_status(
                __event_emitter__,
                level="status",
                message="기업 분석 계획 생성 완료",
                done=True,
            )
            
            print("############################################ 기업 분석 계획 ##############################################")
            print(research_plan)
            print("################################################ 기업 분석 계획 끝 #########################################")

            # 분석 계획 스탭 별 상세 검색 및 개별 보고서 생성
            step_reports = []  # 각 스탭별 보고서를 저장할 리스트
            
            for step in research_plan.get("analysis_plan", {}).get("research_steps", []):
                step_number = step.get("step", "N/A")
                step_description = step.get("description", "")
                step_search_queries = step.get("search_queries", [])
                step_expected_outcomes = step.get("expected_outcomes", "")
                
                await self.emit_status(
                    __event_emitter__,
                    level="status",
                    message=f"기업 분석 계획 스탭 {step_number}에 대한 상세 검색 및 보고서 작성 시작...",
                    done=False,
                )
                
                # 각 스탭의 검색 결과 취합
                step_combined_docs = []
                step_combined_urls = []
                for query in step_search_queries:
                    await self.emit_status(
                        __event_emitter__,
                        level="status",
                        message=f"스탭 {step_number}: 키워드 '{query}' 웹 검색 중...",
                        done=False,
                    )
                    search_result = await web_search(__request__, query)
                    if search_result:
                        if "docs" in search_result:
                            step_combined_docs.extend(search_result.get("docs", []))
                        if "urls" in search_result:
                            step_combined_urls.extend(search_result.get("urls", []))
                
                # 중복 URL 제거
                step_combined_urls = list(dict.fromkeys(step_combined_urls))
                
                # 검색 결과의 요약 텍스트 생성 (docs의 content를 간단히 결합)
                combined_search_text = ""
                for doc in step_combined_docs:
                    combined_search_text += doc.get("content", "") + "\n"
                if step_combined_urls:
                    combined_search_text += "\n관련 URL: " + ", ".join(step_combined_urls)
                
                # 스탭별 보고서 생성을 위한 프롬프트 구성
                step_prompt = [
                    {
                        "role": "system",
                        "content": (
                            "당신은 기업 분석 보고서를 작성하는 전문가입니다. 아래의 정보를 바탕으로 해당 분석 단계에 대한 "
                            "상세 보고서를 작성해주세요. 보고서는 사실에 기반하여 객관적이고 자세하게 작성되어야 하며, "
                            "필요시 3000단어까지 허용됩니다. 재무 데이터, 시장 데이터, 경쟁사 정보 등은 최대한 정확한 수치와 "
                            "출처를 포함해주세요."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"""
기업명: {research_plan.get("analysis_plan", {}).get("company_name", "명시되지 않음")}
산업: {research_plan.get("analysis_plan", {}).get("industry", "명시되지 않음")}
분석 단계: {step_number}
단계 설명: {step_description}
검색 키워드: {step_search_queries}
예상 결과: {step_expected_outcomes}

[검색 결과 요약]
{combined_search_text}
                        """
                    }
                ]
                
                await self.emit_status(
                    __event_emitter__,
                    level="status",
                    message=f"기업 분석 계획 스탭 {step_number}에 대한 보고서 작성 중...",
                    done=False,
                )
                
                # LLM을 통해 스탭별 보고서 생성 요청
                step_report_response = await generate_chat_completion(
                    request=__request__,
                    form_data={
                        "model": "o3-mini",
                        "messages": step_prompt,
                        "stream": False,
                    },
                    user=user,
                )
                
                step_report_content = step_report_response.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # 개별 스탭 보고서 저장
                step_reports.append({
                    "step": step_number,
                    "report": step_report_content,
                })
                
                await self.emit_status(
                    __event_emitter__,
                    level="status",
                    message=f"기업 분석 계획 스탭 {step_number} 보고서 작성 완료",
                    done=True,
                )
            
            
            # 모든 스탭의 개별 보고서가 생성된 후 최종 종합 보고서 요청 프롬프트 생성
            combined_step_reports_text = ""
            for step_report in step_reports:
                combined_step_reports_text += f"분석 단계 {step_report['step']} 보고서:\n{step_report['report']}\n\n"
            
            final_report_prompt = [
                {
                    "role": "system",
                    "content": (
                        "당신은 기업 분석 종합 보고서를 작성하는 전문가입니다. 아래에 각 분석 단계에 대한 보고서가 있습니다. "
                        "이를 바탕으로 최종 기업 분석 종합 보고서를 작성해주세요. 보고서는 다음 구조를 따라야 합니다:\n\n"
                        "1. 요약(Executive Summary): 핵심 분석 결과와 투자 의견을 간략히 요약\n"
                        "2. 기업 개요: 기업의 역사, 사업 영역, 주요 제품/서비스, 경영진 등\n"
                        "3. 산업 분석: 기업이 속한 산업의 현황, 트렌드, 성장성, 규제 환경 등\n"
                        "4. 재무 분석: 매출, 이익, 성장률, 수익성, 부채비율 등 주요 재무지표 분석\n"
                        "5. 경쟁사 분석: 주요 경쟁사와의 비교, 시장 점유율, 경쟁 우위 요소 등\n"
                        "6. SWOT 분석: 강점, 약점, 기회, 위협 요소 분석\n"
                        "7. 미래 전망: 기업의 성장 전략, 신규 사업, 리스크 요소 등\n"
                        "8. 투자 의견: 투자 추천 여부, 목표 주가, 투자 리스크 등\n\n"
                        "보고서는 사실에 기반하여 객관적이고 상세하게 작성되어야 하며, 모든 수치와 주장에는 가능한 출처를 명시해주세요. "
                        "필요시 5000단어까지 허용됩니다."
                    )
                },
                {
                    "role": "user",
                    "content": f"""
사용자의 기업 분석 요청: {user_message}

기업명: {research_plan.get("analysis_plan", {}).get("company_name", "명시되지 않음")}
산업: {research_plan.get("analysis_plan", {}).get("industry", "명시되지 않음")}

기업 분석 계획 개요: {json.dumps(research_plan, ensure_ascii=False, indent=2)}

각 분석 단계별 보고서:
{combined_step_reports_text}

위 정보를 바탕으로 사용자의 기업 분석 요청에 대한 종합적이고 상세한 최종 기업 분석 보고서를 작성해주세요.
"""
                }
            ]
            print("############################################ final_report_prompt start ##############################################")
            print(final_report_prompt)
            print("################################################ final_report_prompt end #########################################")
            # 최종 보고서 요청 프롬프트를 body에 저장하여 후속 처리하도록 함
            body["messages"] = final_report_prompt
            
            await self.emit_status(
                __event_emitter__,
                level="status",
                message="최종 기업 분석 보고서 요청 프롬프트 생성 완료",
                done=True,
            )
            
                    
       
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            print(f"오류 상세 정보:")
            print(f"오류 유형: {type(e).__name__}")
            print(f"오류 발생 위치: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
            print(f"오류 상세 메시지: {str(e)}")
            
            # 스택 트레이스 출력
            import traceback
            print("스택 트레이스:")
            print(''.join(traceback.format_tb(e.__traceback__)))
            
        return body

