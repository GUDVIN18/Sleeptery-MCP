from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.mcp import MCPAdapter
from fastmcp.client.transports import StreamableHttpTransport
from functools import partial
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from app.include.config import config
from app.include.logging_config import logger as log
from pathlib import Path
import asyncio
import datetime as dt
import httpx
import json
import os
from zoneinfo import ZoneInfo


PROMPT_DIR = Path(__file__).resolve().parents[2] / "st_artificial_intelligence/app/sleep_ai/context/main"
SYSTEM_PROMPT = (PROMPT_DIR / "system.md").read_text(encoding="utf-8")
STYLE_PROMPT = (PROMPT_DIR / "style.md").read_text(encoding="utf-8")


async def generation_pipe(user_id: int, message: str):
    if not config.QWEN_API_KEY:
        raise ValueError("Укажи QWEN_API_KEY в .env")

    # Подключаемся к уже запущенному MCP v2 без локального прокси
    transport = StreamableHttpTransport(
        config.MCP_URL,
        httpx_client_factory=partial(httpx.AsyncClient, trust_env=False),
    )
    async with MCPAdapter(transport) as adapter:
        tools = await adapter.list_tools()
        mcp_prompts = await adapter.client.list_prompts()
        log.info(f"MCP подключён:\ntools={[tool.name for tool in tools]}\nprompts={[prompt.name for prompt in mcp_prompts]}")

    
        prompts = [
            await adapter.client.get_prompt_mcp(prompt.name)
            for prompt in mcp_prompts
        ]

        # from langchain_core.utils.function_calling import convert_to_openai_tool
        # for tool in tools:
        #     if tool.name == "user_daily_stats":
        #         openai_schema = convert_to_openai_tool(tool)

        #         log.info(
        #             "OpenAI schema:\n{}",
        #             json.dumps(
        #                 openai_schema,
        #                 ensure_ascii=False,
        #                 indent=2,
        #             ),
        #         )




        llm = ChatOpenAI(
            api_key=config.QWEN_API_KEY,
            base_url=os.getenv(
                "DASHSCOPE_API_BASE",
                "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            ),
            model=config.MODEL_SLEEP_AI,
            temperature=0.25,
            extra_body={"enable_thinking": False},
            timeout=60,
        ).bind_tools(tools)

        async def llm_response(state: MessagesState):
            log.debug("Последнее сообщение: {}", state["messages"][-1])
            response = await llm.ainvoke(state["messages"])
            log.info("Вызовы инструментов: {}", response.tool_calls)
            return {"messages": [response]}

        graph = StateGraph(MessagesState)
        # узлы
        graph.add_node("llm_response", llm_response)
        graph.add_node("tools", ToolNode(tools))
        # рёбра
        graph.add_edge(START, "llm_response")
        graph.add_conditional_edges("llm_response", tools_condition, {"tools": "tools", END: END})
        graph.add_edge("tools", "llm_response")
        app = graph.compile()

        today = dt.datetime.now(ZoneInfo("Europe/Moscow")).date().isoformat()
        prompt = f"""{SYSTEM_PROMPT}
{STYLE_PROMPT}

Инструкция по анализу данных из MCP сервера:
{prompts}

Пользователь: user_id={user_id}. Сегодня: 2026-10-07.
Данные сна получай через MCP, период выбирай по запросу пользователя.
история советов и база знаний не подключены — не выдумывай их.
Очень краткий ответ
"""
        result = await app.ainvoke(
            {"messages": [SystemMessage(content=prompt), HumanMessage(content=message)]},
            config={"recursion_limit": 12},
        )
        answer = result["messages"][-1].content
        log.success("Ответ агента: {}", answer)
        return answer


if __name__ == "__main__":
    asyncio.run(generation_pipe(
        user_id=596,
        message="Найди проблему в моем сне и сформируй четкий совет по улучшению сна. Проанализируй дневник сна и сон пользователя",
    ))
