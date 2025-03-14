import os
from typing import List, Union, Generator, Iterator, Optional
from pprint import pprint
import requests
import json
import warnings
from pydantic import BaseModel, Field

# Uncomment to disable SSL verification warnings if needed.
# warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class Pipeline:
    class Valves(BaseModel):     
        DIFY_API_URL: str = ""
        DIFY_API_KEY: str = ""
       
    def __init__(self):
        self.name = "Dify Agent Pipeline(Chatflow)"
        self.valves = self.Valves()
        
        self.valves = self.Valves(
            **{"DIFY_API_URL": os.getenv("DIFY_API_URL", "http://45.132.75.98:8082/v1/chat-messages"),
               "DIFY_API_KEY": os.getenv("DIFY_API_URL", "app-aLGVqEGXm2PsTmfmKAHyw3Px")}
        )


        self.api_request_stream = True  # Dify support stream
        self.verify_ssl = True
        self.debug = False
        print(self.valves.DIFY_API_URL)
        print(self.valves.DIFY_API_KEY)
        

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup: {__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is shutdown.
        print(f"on_shutdown: {__name__}")
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        # This function is called before the OpenAI API request is made.
        # You can modify the form data before it is sent to the OpenAI API.
        print(f"inlet: {__name__}")
        if self.debug:
            print(f"inlet: {__name__} - body:")
            pprint(body)
            print(f"inlet: {__name__} - user:")
            pprint(user)
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        # This function is called after the OpenAI API response is completed.
        # You can modify the messages after they are received from the OpenAI API.
        print(f"outlet: {__name__}")
        if self.debug:
            print(f"outlet: {__name__} - body:")
            pprint(body)
            print(f"outlet: {__name__} - user:")
            pprint(user)
        return body

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe: {__name__}")

        if self.debug:
            print(f"pipe: {__name__} - received message from user: {user_message}")

        # Set response mode Dify API parameter
        response_mode = "streaming" if self.api_request_stream else "blocking"

        # Prepare headers and data for the API request
        headers = {
            "Authorization": f"Bearer {self.valves.DIFY_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "inputs": {},
            "response_mode": response_mode,
            "query": user_message,
            "user": body["user"]["email"],
            "conversation_id": ""
        }

        try:
            response = requests.post(
                self.valves.DIFY_API_URL,
                headers=headers,
                json=data,
                stream=self.api_request_stream,
                verify=self.verify_ssl,
            )
        except requests.RequestException as e:
            yield f"Workflow request failed with exception: {e}"
            return

        if response.status_code == 200:
            # Initialize a buffer to accumulate the answer parts
            answer_buffer = ""

            for line in response.iter_lines():
                if line:
                    try:
                        # Remove 'data: ' prefix and parse JSON
                        decoded_line = line.decode("utf-8").strip()
                        if decoded_line.startswith("data:"):
                            json_str = decoded_line.replace("data: ", "", 1)
                            json_data = json.loads(json_str)
                            
                            event = json_data.get("event")
                            
                            if event == "message":
                                # Extract the 'answer' part and yield it
                                answer_part = json_data.get("answer", "")
                                answer_buffer += answer_part
                                yield answer_part
                            
                            elif event == "message_end":
                                # Optionally, you can perform actions when the message ends
                                if self.debug:
                                    pprint(json_data)
                                # If you want to yield the complete answer at the end, uncomment below:
                                # yield answer_buffer
                            
                            # Handle other events if necessary
                            elif self.debug:
                                print(f"Received event: {event}")
                                pprint(json_data.get("data", {}))
                                
                    except json.JSONDecodeError:
                        print(f"Failed to parse JSON: {line}")
        else:
            yield f"Workflow request failed with status code: {response.status_code}"
