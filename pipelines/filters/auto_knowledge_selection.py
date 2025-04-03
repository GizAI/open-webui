import json
import re
import traceback
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any, Optional

from open_webui.models.users import Users, UserModel
from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.misc import get_last_user_message
from open_webui.models.knowledge import Knowledges
from open_webui.models.files import Files
from open_webui.utils.middleware import chat_web_search_handler


# 로깅 설정
LOG_DIR = "/data/conting/logs/auto_knowledge_selection"
os.makedirs(LOG_DIR, exist_ok=True)

# 로거 설정
logger = logging.getLogger("auto_knowledge_selection")
logger.setLevel(logging.DEBUG)

# 콘솔 핸들러 설정
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter("[%(name)s] %(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

# 일반 로그 파일 핸들러 설정 (날짜별 로그 파일 및 로테이션)
log_file = os.path.join(LOG_DIR, f"auto_kb_{datetime.now().strftime('%Y%m%d')}.log")
file_handler = RotatingFileHandler(
    log_file, 
    maxBytes=10*1024*1024,  # 10MB
    backupCount=30,         # 최대 30개 백업 파일 유지
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_format)
logger.addHandler(file_handler)

# 오류 전용 로그 파일 핸들러 설정
error_log_file = os.path.join(LOG_DIR, f"auto_kb_error_{datetime.now().strftime('%Y%m%d')}.log")
error_file_handler = RotatingFileHandler(
    error_log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=30,         # 최대 30개 백업 파일 유지
    encoding='utf-8'
)
error_file_handler.setLevel(logging.ERROR)
error_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
error_file_handler.setFormatter(error_format)
logger.addHandler(error_file_handler)

# 커스텀 에러 로깅 함수 정의
def log_error(request_id, e, error_info=None, additional_info=None):
    """
    오류 정보를 상세하게 기록하는 함수
    """
    error_message = f"[{request_id}] 예외 발생: {e}"
    logger.error(error_message)
    
    if error_info:
        logger.error(f"[{request_id}] 상세 오류 정보:\n{error_info}")
    
    if additional_info:
        logger.error(f"[{request_id}] 추가 정보: {additional_info}")
    
    # NoneType 오류인 경우 더 자세한 정보 출력
    if "'NoneType' object has no attribute 'get'" in str(e):
        logger.error(f"[{request_id}] NoneType 오류 특별 진단 시작 ---------------")
        
        # 호출 스택 추적 정보 추가
        stack_trace = traceback.format_exc()
        frame_info = []
        for i, line in enumerate(stack_trace.splitlines()):
            if "File " in line:
                frame_info.append(line.strip())
        
        if frame_info:
            logger.error(f"[{request_id}] 호출 스택 정보:")
            for frame in frame_info:
                logger.error(f"[{request_id}]   {frame}")
        
        logger.error(f"[{request_id}] NoneType 오류 특별 진단 종료 ---------------")


def parse_json_content(content: str) -> Optional[dict]:
    """
    주어진 문자열에서 JSON 객체를 추출하고 dict로 변환합니다.
    - 문자열 전체가 '{...}'로 감싸져 있다면 직접 파싱을 시도합니다.
    - 아닐 경우, 정규표현식으로 첫 번째 JSON 객체를 추출하여 파싱 시도합니다.
    - 파싱에 실패하면 None을 반환합니다.
    - 필요 시(파싱 실패), 작은따옴표(')를 큰따옴표(")로 바꿔보는 시도도 합니다.
    """

    def try_load_json(json_str: str) -> Optional[dict]:
        """주어진 json_str을 파싱 시도하고 실패 시 None을 반환합니다."""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    content = content.strip()

    # "None"과 같이 JSON 아닌 특정 문자열 처리
    if content.lower() == "none":
        return None

    # 1) 직접 '{...}'로 감싸져 있는지 확인
    if content.startswith("{") and content.endswith("}"):
        parsed_data = try_load_json(content)
        if parsed_data is not None:
            return parsed_data

        # 파싱 실패 시, 작은따옴표를 큰따옴표로 치환 후 재시도
        content_single_to_double = content.replace("'", '"')
        parsed_data = try_load_json(content_single_to_double)
        if parsed_data is not None:
            return parsed_data

        return None

    # 2) 정규표현식으로 '{...}' 형태 추출
    match = re.search(r"\{.*?\}", content, flags=re.DOTALL)
    if not match:
        return None

    json_str = match.group(0)

    parsed_data = try_load_json(json_str)
    if parsed_data is not None:
        return parsed_data

    # 파싱 실패 시, 작은따옴표를 큰따옴표로 치환 후 재시도
    json_str_converted = json_str.replace("'", '"')
    parsed_data = try_load_json(json_str_converted)
    if parsed_data is not None:
        return parsed_data

    return None


class Filter:
    class Valves(BaseModel):
        status: bool = Field(default=True)
        auto_search_mode: bool = Field(default=False)
        plan_model: str = Field(default="o3-mini")

    def __init__(self):
        self.valves = self.Valves()
        logger.info("Auto Knowledge Selection 필터 초기화됨")

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

    async def select_knowledge_base(
        self, body: dict, __user__: Optional[dict]
    ) -> Optional[dict]:
        """
        사용자의 메시지를 바탕으로 적절한 Knowledge Base를 선택한다.
        - 출력 예시:
            {
                "id": <KnowledgeBaseID or null>,
                "name": <KnowledgeBaseName or null>
            }
        """
        messages = body["messages"]
        user_message = get_last_user_message(messages)
        logger.debug(f"사용자 메시지: {user_message}")

        all_knowledge_bases = Knowledges.get_knowledge_bases_by_user_id(
            __user__.get("id"), "read"
        )
        logger.debug(f"사용자의 Knowledge Base 개수: {len(all_knowledge_bases)}")

        knowledge_bases_list = "\n\n".join(
            [
                f"--- Knowledge Base {index + 1} ---\n"
                f"ID: {getattr(knowledge_base, 'id', 'Unknown')}\n"
                f"Name: {getattr(knowledge_base, 'name', 'Unknown')}\n"
                f"Description: {getattr(knowledge_base, 'description', 'Unknown')}"
                for index, knowledge_base in enumerate(all_knowledge_bases)
            ]
        )

        system_prompt = f"""You are a system that selects the most appropriate knowledge bases for the user's query.
Below is a list of knowledge bases accessible by the user. 
Based on the user's prompt, return the 1-3 most relevant knowledge bases as an array. 
If no relevant knowledge bases are applicable, return an "None" without any explanation.

Available knowledge bases:
{knowledge_bases_list}

Return the result in the following JSON format (no extra keys, no explanations):
{{
    "selected_knowledge_bases": 
        [
            {{
                "id": <KnowledgeBaseID>,
                "name": <KnowledgeBaseName>
            }},
            ...
        ]
}}
"""

        prompt = (
            "History:\n"
            + "\n".join(
                [
                    f"{message['role'].upper()}: \"\"\"{message['content']}\"\"\""
                    for message in messages[::-1][:4]
                ]
            )
            + f"\nUser query: {user_message}"
        )

        return {
            "system_prompt": system_prompt,
            "prompt": prompt,
            "model": self.valves.plan_model,
        }

    async def determine_web_search_needed(
        self, body: dict, __user__: Optional[dict]
    ) -> Optional[dict]:
        """
        사용자의 메시지를 바탕으로 웹 검색이 필요한지 여부만 별도로 판단한다.
        - 출력 예시:
            {
                "web_search_enabled": True or False
            }
        """
        messages = body["messages"]
        user_message = get_last_user_message(messages)
        logger.debug(f"웹 검색 필요 여부 판단을 위한 사용자 메시지: {user_message}")

        system_prompt = """You are a system that determines if a web search is needed for the user's query.

Consider the following when making your decision:
1. If the query relates to real-time or up-to-date information, including recurring events 
   (e.g., a presidential inauguration, annual shareholder meetings, quarterly earnings reports, 
   product launches, or company announcements), enable a web search to ensure the most recent 
   occurrence is addressed.

2. If the query is not about historical facts, assume most questions benefit from incorporating 
   the latest information available through a web search.

3. Particularly for questions regarding business or economic topics—such as company or 
   industry trends, corporate information, related public figures, government policies, 
   taxes, new technologies, and other fast-changing subjects—web search is strongly recommended 
   to ensure accuracy and freshness of data.

4. For general or everyday prompts that may require current information (e.g., weather updates, recent news, live events), enable a web search.

5. Strive to make human-like judgments to ensure your decision aligns with the user's intent 
   and the context of the question.

6. If the user's query is not clear, return "None" without any explanation.

Return the result in the following JSON format:
{
    "web_search_enabled": boolean
}"""

        prompt = (
            "History:\n"
            + "\n".join(
                [
                    f"{message['role'].upper()}: \"\"\"{message['content']}\"\"\""
                    for message in messages[::-1][:4]
                ]
            )
            + f"\nUser query: {user_message}"
        )

        return {
            "system_prompt": system_prompt,
            "prompt": prompt,
            "model": self.valves.plan_model,
        }

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __request__: Any,
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        request_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + str(id(__request__))[-6:]
        logger.info(f"[{request_id}] inlet 함수 시작")
        
        try:
            logger.debug(f"[{request_id}] body: {body}")
            if __user__ is None:
                logger.warning(f"[{request_id}] __user__ 객체가 None입니다.")
            else:
                logger.debug(f"[{request_id}] __user__ ID: {__user__.get('id')}")
            
            # 유저 객체 보정
            if __user__ is None:
                user_data = {}
                user = None
            else:
                user_data = __user__.copy()
                user_data.update(
                    {
                        "profile_image_url": "",
                        "last_active_at": 0,
                        "updated_at": 0,
                        "created_at": 0,
                    }
                )
                user = Users.get_user_by_id(__user__["id"])
                logger.debug(f"[{request_id}] 조회된 user 객체: {user}")
                
            user_object = UserModel(**user_data)
            logger.debug(f"[{request_id}] 생성된 user_object: {user_object}")

            ###################################################################
            # 1) Knowledge Base 선택
            ###################################################################
            logger.info(f"[{request_id}] Knowledge Base 선택 시작")
            kb_plan = await self.select_knowledge_base(body, __user__)
            if kb_plan is None:
                logger.warning(f"[{request_id}] select_knowledge_base 결과가 None입니다")
                raise ValueError("select_knowledge_base result is None")

            logger.debug(f"[{request_id}] kb_plan: {kb_plan}")
            kb_payload = {
                "model": kb_plan["model"],
                "messages": [
                    {"role": "system", "content": kb_plan["system_prompt"]},
                    {"role": "user", "content": kb_plan["prompt"]},
                ],
                "stream": False,
            }
            
            logger.info(f"[{request_id}] LLM 호출: Knowledge Base 선택")
            kb_response = await generate_chat_completion(
                request=__request__, form_data=kb_payload, user=user
            )

            if kb_response is None:
                logger.warning(f"[{request_id}] kb_response가 None입니다")
                kb_content = ""
            else:
                logger.debug(f"[{request_id}] kb_response: {kb_response}")
                kb_content = kb_response["choices"][0]["message"]["content"] if kb_response else ""
            
            logger.debug(f"[{request_id}] kb_content: {kb_content}")

            if kb_content == "None":
                selected_knowledge_bases = []
                logger.info(f"[{request_id}] 선택된 Knowledge Base가 없습니다.")
            else:
                try:
                    kb_result = parse_json_content(kb_content)
                    logger.debug(f"[{request_id}] 파싱된 kb_result: {kb_result}")

                    if kb_result is None:
                        logger.warning(f"[{request_id}] kb_result 파싱 결과가 None입니다")
                        selected_knowledge_bases = []
                    else:
                        selected_knowledge_bases = kb_result.get("selected_knowledge_bases", [])
                        logger.debug(f"[{request_id}] selected_knowledge_bases: {selected_knowledge_bases}")
                except Exception as e:
                    error_info = traceback.format_exc()
                    log_error(
                        request_id, 
                        e, 
                        error_info, 
                        f"파싱 대상 문자열: {kb_content[:200]}..."
                    )
                    selected_knowledge_bases = []

            ###################################################################
            # 2) 웹 검색 필요 여부 판단
            ###################################################################
            logger.debug(f"[{request_id}] 웹 검색 모드 상태: {self.valves.auto_search_mode}")
            if self.valves.auto_search_mode:
                logger.info(f"[{request_id}] 웹 검색 필요 여부 판단 시작")
                ws_plan = await self.determine_web_search_needed(body, __user__)
                if ws_plan is None:
                    logger.warning(f"[{request_id}] determine_web_search_needed 결과가 None입니다")
                    raise ValueError("determine_web_search_needed result is None")

                ws_payload = {
                    "model": ws_plan["model"],
                    "messages": [
                        {"role": "system", "content": ws_plan["system_prompt"]},
                        {"role": "user", "content": ws_plan["prompt"]},
                    ],
                    "stream": False,
                }

                logger.info(f"[{request_id}] LLM 호출: 웹 검색 필요 여부 판단")
                ws_response = await generate_chat_completion(
                    request=__request__, form_data=ws_payload, user=user
                )

                if ws_response is None:
                    logger.warning(f"[{request_id}] ws_response가 None입니다")
                    ws_content = ""
                else:
                    logger.debug(f"[{request_id}] ws_response: {ws_response}")
                    ws_content = ws_response["choices"][0]["message"]["content"] if ws_response else ""
                
                logger.debug(f"[{request_id}] ws_content: {ws_content}")
                ws_result = parse_json_content(ws_content)
                logger.debug(f"[{request_id}] 파싱된 ws_result: {ws_result}")

                if ws_result is None:
                    logger.warning(f"[{request_id}] ws_result 파싱 결과가 None입니다")
                    web_search_enabled = False
                else:
                    web_search_enabled = ws_result.get("web_search_enabled", False)
                    logger.debug(f"[{request_id}] web_search_enabled 값: {web_search_enabled}")

                if isinstance(web_search_enabled, str):
                    web_search_enabled = web_search_enabled.lower() in ["true", "yes"]
                    logger.debug(f"[{request_id}] web_search_enabled 문자열 변환 후: {web_search_enabled}")

                if web_search_enabled:
                    logger.info(f"[{request_id}] 웹 검색 실행")
                    await chat_web_search_handler(
                        __request__,
                        body,
                        {"__event_emitter__": __event_emitter__},
                        user_object,
                    )
                else:
                    logger.info(f"[{request_id}] 웹 검색이 필요하지 않습니다.")

            ###################################################################
            # 선택된 Knowledge Base가 있으면 body에 추가 (기존 files와 병합)
            ###################################################################
            logger.info(f"[{request_id}] 선택된 Knowledge Base 처리 시작, 개수: {len(selected_knowledge_bases)}")
            selected_kb_names = []
            for selected_knowledge_base in selected_knowledge_bases:
                logger.debug(f"[{request_id}] 처리 중인 Knowledge Base: {selected_knowledge_base}")
                if not isinstance(selected_knowledge_base, dict):
                    logger.warning(f"[{request_id}] selected_knowledge_base가 딕셔너리가 아닙니다: {type(selected_knowledge_base)}")
                    continue
                    
                kb_id = selected_knowledge_base.get("id")
                kb_name = selected_knowledge_base.get("name")
                logger.debug(f"[{request_id}] kb_id: {kb_id}, kb_name: {kb_name}")

                if kb_id and kb_name:
                    selected_kb_names.append(kb_name)
                    logger.debug(f"[{request_id}] Knowledge Base 정보 조회: {kb_id}")
                    selected_knowledge_base_info = Knowledges.get_knowledge_by_id(kb_id)
                    logger.debug(f"[{request_id}] 조회된 Knowledge Base 정보: {selected_knowledge_base_info}")

                    if selected_knowledge_base_info:
                        logger.debug(f"[{request_id}] Knowledge Base 파일 정보 처리")
                        if not hasattr(selected_knowledge_base_info, 'data') or selected_knowledge_base_info.data is None:
                            logger.warning(f"[{request_id}] selected_knowledge_base_info.data가 없거나 None입니다")
                            continue
                            
                        knowledge_file_ids = selected_knowledge_base_info.data.get("file_ids", [])
                        logger.debug(f"[{request_id}] knowledge_file_ids: {knowledge_file_ids}")
                        knowledge_files = Files.get_file_metadatas_by_ids(knowledge_file_ids)
                        logger.debug(f"[{request_id}] knowledge_files 개수: {len(knowledge_files)}")
                        knowledge_dict = selected_knowledge_base_info.model_dump()
                        knowledge_dict["files"] = [file.model_dump() for file in knowledge_files]
                        knowledge_dict["type"] = "collection"

                        if "files" not in body:
                            body["files"] = []
                        body["files"].append(knowledge_dict)
                        logger.debug(f"[{request_id}] body['files'] 개수: {len(body['files'])}")

            if selected_kb_names:
                kb_names_str = ', '.join(selected_kb_names)
                logger.info(f"[{request_id}] 선택된 Knowledge Base 이름: {kb_names_str}")
                await self.emit_status(
                    __event_emitter__,
                    level="status",
                    message=f"Matching knowledge bases found: {kb_names_str}",
                    done=True,
                )

        except Exception as e:
            error_info = traceback.format_exc()
            log_error(request_id, e, error_info)
            
            # NoneType 오류인 경우 더 자세한 정보 출력
            if "'NoneType' object has no attribute 'get'" in str(e):
                logger.error(f"[{request_id}] NoneType 오류 상세 분석:")
                logger.error(f"[{request_id}] __user__: {__user__}")
                if __user__ is not None:
                    logger.error(f"[{request_id}] __user__ 타입: {type(__user__)}")
                    logger.error(f"[{request_id}] __user__ 키: {__user__.keys() if hasattr(__user__, 'keys') else 'No keys method'}")
                
            await self.emit_status(
                __event_emitter__,
                level="status",
                message=f"추가 할 지식베이스가 없습니다.",
                done=True,
            )

        ###################################################################
        # 최종 시스템 메시지 삽입 (답변 형태 지침)
        ###################################################################
        logger.info(f"[{request_id}] 최종 시스템 메시지 삽입")
        context_message = {
            "role": "system",
            "content": (
                "You are a multidisciplinary expert with contextual adaptation capabilities. You possess deep expertise in the following fields: project management, psychology, economics, design, marketing, and engineering. You are able to use this knowledge in an integrated manner while adapting your approach to the specific needs of each request.\n\n"
                
                "The user is seeking high-level expertise to answer their questions or help them with their professional and personal projects. Each request may require a different level of depth, communication style, and analytical framework.\n\n"
                
                "Basic Structure for All Responses:\n"
                "1. Begin by precisely understanding the request, asking clarifying questions if necessary.\n"
                "2. Adapt your depth level according to the context (quick response or in-depth analysis).\n"
                "3. Use clear and accessible language, avoiding corporate jargon unless relevant.\n"
                "4. Check the logical consistency of your response before finalizing it.\n"
                "5. End with a bullet-point summary of the essential elements to remember.\n\n"
                
                "Analytical Approach (to apply as relevant):\n"
                "- Leverage your interdisciplinary expertise (PM, psychology, economics, design, marketing, engineering).\n"
                "- Cite relevant references when they strengthen your point (e.g., Ries, 2011; McKinsey, 2021).\n"
                "- After each analysis, check your logic against recognized theoretical frameworks (Gibson, 2022).\n"
                "- Highlight any contradictions or tensions in the analysis.\n"
                "- Use recognized analytical frameworks when appropriate (RICE, OKRs, Double Diamond, etc.).\n"
                "- Identify potentially problematic assumptions using data or logic.\n\n"
                
                "Response Enrichment (to use selectively):\n"
                "- Illustrate your points with concrete and concise anecdotes.\n"
                "- Integrate relevant academic knowledge by explaining it simply.\n"
                "- Propose alternative scenario simulations when it helps decision-making.\n"
                "- Present the advantages and disadvantages of different options when a decision needs to be made.\n"
                "- Structure complex points in narrative form to facilitate understanding.\n\n"
                
                "Contextual Adaptation:\n"
                "- Keep in memory the objectives and constraints mentioned previously in the conversation.\n"
                "- If the user seems stressed, acknowledge it and suggest concrete steps to move forward.\n"
                "- Maintain consistency in the terminology used unless requested otherwise.\n"
                "- Follow a continuous improvement process by taking into account user feedback.\n"
                "- Keep track of recurring topics to allow for further exploration later.\n\n"
                
                "Output Format:\n"
                "1. A direct answer to the main question\n"
                "2. A structured analysis using relevant techniques\n"
                "3. Concrete examples or illustrations if appropriate\n"
                "4. A final bullet-point summary\n"
                "5. Follow-up or further exploration suggestions if relevant\n\n"
                
                "**IMPORTANT: Additionally, please respond in the language used by the user in their input.**"
            ),
        }
        
        body.setdefault("messages", []).insert(0, context_message)
        logger.info(f"[{request_id}] inlet 함수 종료")

        await self.emit_status(
                    __event_emitter__,
                    level="status",
                    message="답변을 준비중입니다. 잠시만 기다려 주세요",
                    done=False,
                )
        return body
