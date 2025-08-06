"""OpenAI Parser."""

import json
import logging
import os
from typing import List, Optional

try:
    from openai import OpenAI  # type: ignore
except ImportError:
    _HAS_OPENAI = False
else:
    _HAS_OPENAI = True

from circuit_maintenance_parser.parser import LLM

logger = logging.getLogger(__name__)


class OpenAIParser(LLM):
    """Notifications Parser powered by OpenAI ChatGPT."""

    def get_llm_response(self, content) -> Optional[List]:
        """Get LLM processing from OpenAI."""
        if not _HAS_OPENAI:
            raise ImportError("openai extra is required to use OpenAIParser.")

        client = OpenAI(api_key=os.getenv("PARSER_OPENAI_API_KEY"))
        model = os.getenv("PARSER_OPENAI_MODEL", "gpt-3.5-turbo")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {  # type: ignore
                        "role": "system",
                        "content": self.llm_question,
                    },
                    {  # type: ignore
                        "role": "user",
                        "content": content,
                    },
                ],
            )

        # TODO: Maybe asking again about the generated response could refine it

        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.error(err)
            return None

        logger.info("Used OpenAI tokens: %s", response.usage)
        generated_text = response.choices[0].message.content
        logger.info("Response from LLM: %s", generated_text)
        try:
            return json.loads(generated_text)  # type: ignore
        except ValueError as err:
            logger.error(err)
            return None

        return None
