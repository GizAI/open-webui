"""
title: Example Action
author: open-webui
author_url: https://github.com/open-webui
funding_url: https://github.com/open-webui
version: 0.1.0
required_open_webui_version: 0.3.9
"""

from pydantic import BaseModel, Field
from typing import Optional, Union, Generator, Iterator

import os
import requests
import asyncio


class Action:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()
        pass

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Optional[dict]:
        print(f"action:{__name__}")

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "action", "done": False},
                }
            )
            await asyncio.sleep(1)
            await __event_emitter__(
                {
                    "type": "action",
                    "data": {"action": "submit_prompt", "prompt": "OK"},
                }
            )
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "action done", "done": True},
                }
            )
