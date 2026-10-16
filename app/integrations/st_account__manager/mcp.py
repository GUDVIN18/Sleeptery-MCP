import datetime as dt
from mcp.server import MCPServer
from app.include.logging_config import logger as log
from app.integrations.st_account__manager.tools import (
    get_user_profile,
)
from app.integrations.st_sleep.shemas.daily_stats import GetUserStatsRequest


class StAccountManagerMCP:
    def __init__(self, server: MCPServer):
        self.server = server
        self._register_tools()
        self._register_prompts()

    # Здесь можно добавить регистрацию конкретных инструментов для StSleepMCP
    def _register_tools(self):
        log.info(f"Начали собирать {self.__class__.__name__} tools")

        @self.server.tool()
        async def user_profile(
            user_id: int
        ):
            """Получить профиль пользователя.

            Вызывай инструмент, когда нужны сведения о пользователе
            для персонализации ответа.

            Аргументы:
                user_id: ID пользователя из st_auth.
            Возвращает профиль со всеми доступными сведениями о пользователе.
            """

            return await get_user_profile(user_id=user_id)

        

    # Здесь можно добавить регистрацию конкретных промптов для StSleepMCP
    def _register_prompts(self):
        log.info(f"Начали собирать {self.__class__.__name__} prompts")