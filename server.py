import asyncio
from mcp.server import MCPServer
from app.include.logging_config import logger as log
from app.integrations import *
from sshtunnel import SSHTunnelForwarder
from sqlalchemy.engine import make_url
from app.include.config import config

# Создаём главный MCP сервер
server = MCPServer("Sleeptery AI MCP server")

# Регистрируем модули
StSleepMCP(server)
StDiaryMCP(server)
StPostgreSQLMCP(server)


async def log_registered_tools():
    tools = await server.list_tools()

    log.info(f"Зарегистрировано MCP tools: {len(tools)}")
    for tool in tools:
        log.info(f"  ✓ {tool.name}")



if __name__ == "__main__":
    with SSHTunnelForwarder(
        (config.PROD_IP, 22),
        ssh_username="root",
        ssh_pkey=config.SSH_KEY_PATH,
        remote_bind_address=("127.0.0.1", 8402),
    ) as tunnel:
        db_url = make_url(config.DB_AI_URL)

        config.DB_AI_URL = db_url.set(
            host="127.0.0.1",
            port=tunnel.local_bind_port,
        ).render_as_string(hide_password=False)

        log.info(
            f"SSH-туннель запущен: "
            f"127.0.0.1:{tunnel.local_bind_port} -> "
            f"{config.PROD_IP}:8402"
        )

        asyncio.run(log_registered_tools())

        log.info("Запускаем MCP сервер")

        server.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=8800,
        )
