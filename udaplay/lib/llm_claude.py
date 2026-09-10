import json
from typing import List, Optional, Dict, Any

import anthropic
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)

from lib.messages import AIMessage, BaseMessage, UserMessage
from lib.tooling import Tool


class ClaudeLLM:
    """
    Drop-in replacement for lib.llm.LLM that uses the Anthropic API.

    Translates between the course lib's OpenAI-shaped message/tool-call
    types and Anthropic's native format so the existing Agent state machine
    works without modification.
    """

    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        temperature: float = 0.0,
        tools: Optional[List[Tool]] = None,
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.client = anthropic.Anthropic(api_key=api_key)
        self.tools: Dict[str, Tool] = {t.name: t for t in (tools or [])}

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def _anthropic_tools(self) -> List[dict]:
        result = []
        for tool in self.tools.values():
            d = tool.dict()["function"]
            result.append({
                "name": d["name"],
                "description": d["description"],
                "input_schema": d["parameters"],
            })
        return result

    def _convert_messages(self, messages: List[BaseMessage]):
        """
        Convert course-lib messages to Anthropic format.

        Key differences:
        - System messages are extracted and passed separately
        - Consecutive ToolMessages get collapsed into a single user message
          containing tool_result blocks (Anthropic requirement)
        - AIMessages with tool_calls become assistant messages with tool_use blocks
        """
        system = None
        converted = []
        i = 0
        while i < len(messages):
            m = messages[i]

            if m.role == "system":
                system = m.content
                i += 1

            elif m.role == "user":
                converted.append({"role": "user", "content": m.content})
                i += 1

            elif m.role == "assistant":
                if m.tool_calls:
                    content = []
                    if m.content:
                        content.append({"type": "text", "text": m.content})
                    for tc in m.tool_calls:
                        content.append({
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.function.name,
                            "input": json.loads(tc.function.arguments),
                        })
                    converted.append({"role": "assistant", "content": content})
                else:
                    converted.append({"role": "assistant", "content": m.content or ""})
                i += 1

            elif m.role == "tool":
                # Group all consecutive ToolMessages into one user message
                tool_results = []
                while i < len(messages) and messages[i].role == "tool":
                    tm = messages[i]
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tm.tool_call_id,
                        "content": tm.content,
                    })
                    i += 1
                converted.append({"role": "user", "content": tool_results})

            else:
                i += 1

        return system, converted

    def invoke(self, input, response_format=None) -> AIMessage:
        if isinstance(input, str):
            messages_list = [UserMessage(content=input)]
        elif isinstance(input, BaseMessage):
            messages_list = [input]
        else:
            messages_list = list(input)

        system, converted = self._convert_messages(messages_list)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": converted,
        }
        if system:
            kwargs["system"] = system
        if self.tools:
            kwargs["tools"] = self._anthropic_tools()

        response = self.client.messages.create(**kwargs)

        text_content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_content = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ChatCompletionMessageToolCall(
                        id=block.id,
                        type="function",
                        function=Function(
                            name=block.name,
                            arguments=json.dumps(block.input),
                        ),
                    )
                )

        return AIMessage(
            content=text_content or None,
            tool_calls=tool_calls if tool_calls else None,
        )
