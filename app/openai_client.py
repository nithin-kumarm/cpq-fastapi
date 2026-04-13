import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI

from app.cpq_client import CPQClient
from app.utils import summarize_parts_response, summarize_quote_response

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")

client = OpenAI(api_key=OPENAI_API_KEY)
cpq = CPQClient()


class OpenAIService:
    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing")

    def _tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "name": "search_parts",
                "description": "Search CPQ parts by part number.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "part_number": {
                            "type": "string",
                            "description": "Part number to search for, for example P05_12345",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 1,
                        },
                        "offset": {
                            "type": "integer",
                            "default": 0,
                        },
                        "pricebook": {
                            "type": "string",
                            "default": "_default_price_book",
                        },
                    },
                    "required": ["part_number"],
                    "additionalProperties": False,
                },
            },
            {
                "type": "function",
                "name": "get_quote_summary",
                "description": "Get a compact summary of a CPQ quote by transaction id.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction_id": {
                            "type": "string",
                            "description": "CPQ transaction id, for example 3227599515",
                        }
                    },
                    "required": ["transaction_id"],
                    "additionalProperties": False,
                },
            },
        ]

    async def chat(self, user_message: str) -> Dict[str, Any]:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "developer",
                    "content": (
                        "You are a CPQ assistant. "
                        "Choose the right tool for the user's request. "
                        "If the user asks for a part, use search_parts. "
                        "If the user asks for a quote summary, use get_quote_summary. "
                        "Return a concise, human-readable answer."
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            tools=self._tools(),
            tool_choice="auto",
        )

        while True:
            function_call = next(
                (item for item in response.output if getattr(item, "type", None) == "function_call"),
                None,
            )

            if function_call is None:
                return {"answer": response.output_text}

            args = json.loads(function_call.arguments or "{}")

            if function_call.name == "search_parts":
                cpq_raw = await cpq.search_parts(
                    part_number=args["part_number"],
                    limit=int(args.get("limit", 1)),
                    offset=int(args.get("offset", 0)),
                    pricebook=args.get("pricebook", "_default_price_book"),
                )
                tool_output = summarize_parts_response(cpq_raw)

            elif function_call.name == "get_quote_summary":
                cpq_raw = await cpq.get_quote_summary(args["transaction_id"])
                tool_output = summarize_quote_response(cpq_raw)

            else:
                raise ValueError(f"Unsupported tool call: {function_call.name}")

            response = client.responses.create(
                model=OPENAI_MODEL,
                previous_response_id=response.id,
                input=[
                    {
                        "type": "function_call_output",
                        "call_id": function_call.call_id,
                        "output": json.dumps(tool_output),
                    }
                ],
            )