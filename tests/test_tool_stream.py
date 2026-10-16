"""Check tool arguments assembled from SSE fragments without calling Qwen."""

import json
import unittest

import httpx
from langchain_openai import ChatOpenAI


class ToolStreamTest(unittest.IsolatedAsyncioTestCase):
    async def test_date_split_before_last_digit(self):
        arguments = {
            "data": {
                "user_id": 596,
                "start_date": "2026-09-29",
                "end_date": "2026-09-29",
            }
        }
        raw = json.dumps(arguments)
        split_at = raw.rindex("9")
        parts = [raw[:split_at], raw[split_at:]]

        async def handle(request):
            self.assertTrue(json.loads(request.content)["stream"])
            events = []
            for index, part in enumerate(parts):
                call = {"index": 0, "function": {"arguments": part}}
                if index == 0:
                    call.update(id="call_test", type="function")
                    call["function"]["name"] = "user_daily_stats"
                events.append({
                    "id": "test", "object": "chat.completion.chunk",
                    "created": 0, "model": "qwen3.7-plus",
                    "choices": [{"index": 0, "delta": {"tool_calls": [call]},
                                 "finish_reason": None}],
                })
            events.append({
                "id": "test", "object": "chat.completion.chunk",
                "created": 0, "model": "qwen3.7-plus",
                "choices": [{"index": 0, "delta": {},
                             "finish_reason": "tool_calls"}],
            })
            body = "".join(f"data: {json.dumps(event)}\n\n" for event in events)
            return httpx.Response(
                200, content=body + "data: [DONE]\n\n",
                headers={"content-type": "text/event-stream"},
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            llm = ChatOpenAI(
                model="qwen3.7-plus", api_key="offline-test",
                base_url="https://example.invalid/v1", http_async_client=client,
                streaming=True,
            )
            response = await llm.ainvoke("test")
        self.assertEqual(response.tool_calls[0]["args"], arguments)
        self.assertEqual(response.invalid_tool_calls, [])


if __name__ == "__main__":
    unittest.main()
