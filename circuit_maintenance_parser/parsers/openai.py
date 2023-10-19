"""OpenAI Parser."""
import os
import logging
import json
from typing import List, Optional

import openai

from circuit_maintenance_parser.parser import LLM

logger = logging.getLogger(__name__)


class OpenAIParser(LLM):
    """Notifications Parser powered by OpenAI ChatGPT."""

    def get_llm_response(self, content) -> Optional[List]:
        """Get LLM processing from OpenAI."""
        openai.api_key = os.getenv("OPENAI_TOKEN")
        openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        try:
            response = openai.ChatCompletion.create(
                model=openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": content,
                    },
                    {
                        "role": "user",
                        "content": self._llm_question,
                    },
                ],
            )
        except openai.error.InvalidRequestError as err:
            logger.error(err)
            return None

        logger.info("Used OpenAI tokens: %s", response["usage"])
        generated_text = response.choices[0].message["content"]
        logger.info("Response from LLM: %s", generated_text)
        try:
            return json.loads(generated_text)
        except ValueError as err:
            logger.error(err)
            return None

        return None
