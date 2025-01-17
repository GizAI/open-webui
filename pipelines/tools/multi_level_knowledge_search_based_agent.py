import os
import requests
from datetime import datetime

from open_webui.models.knowledge import Knowledges


class Tools:
    def __init__(self):
        pass

    # Add your custom tools using pure Python code here, make sure to add type hints
    # Use Sphinx-style docstrings to document your tools, they will be used for generating tools specifications
    # Please refer to function_calling_filter_pipeline.py file from pipelines project for an example

    def get_user_name_and_email_and_id(self, __user__: dict = {}) -> str:
        """
        returns when user ask about the knowledge base
        """

        # Do not include :param for __user__ in the docstring as it should not be shown in the tool's specification
        # The session user object will be passed as a parameter when the function is called
        # The session user object will be passed as a parameter when the function is called
        knowledge_bases = Knowledges.get_knowledge_bases_by_user_id(
            __user__.get("id"), "read"
        )

        result = ""

        # Add knowledge base names to the result string
        if knowledge_bases:
            knowledge_base_names = [kb.name for kb in knowledge_bases]
            result += "\nKnowledge Bases: " + ", ".join(knowledge_base_names)
        else:
            result += "\nKnowledge Bases: None"

        return result
