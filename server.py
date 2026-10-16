import asyncio
from mcp.server import MCPServer
from app.include.logging_config import logger as log
from app.integrations import *


# Создаём главный MCP сервер
server = MCPServer("Sleeptery AI MCP server")

# Регистрируем модули
StSleepMCP(server)
StDiaryMCP(server)
# StAccountManagerMCP(server)


async def log_registered_tools():
    tools = await server.list_tools()

    log.info(f"Зарегистрировано MCP tools: {len(tools)}")
    for tool in tools:
        log.info(f"  ✓ {tool.name}")


if __name__ == "__main__":
    asyncio.run(log_registered_tools())

    log.info("Запускаем MCP сервер")
    server.run(
        transport="streamable-http",
        host="localhost",
        port=8800,
    )