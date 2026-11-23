from typing import Optional, Any
import datetime as dt
from asyncpg import DataError
from mcp.server import MCPServer
from app.include.logging_config import logger as log
from .tools import (
    get_database,
    get_tables,
    get_columns,
    execute_query
)
from app.integrations.st_diary.schemas import UserDiaryRecord


class StPostgreSQLMCP:
    def __init__(self, server: MCPServer):
        self.server = server
        self._register_tools()
        self._register_prompts()

    # Здесь можно добавить регистрацию конкретных инструментов для StSleepMCP
    def _register_tools(self):
        log.info(f"Начали собирать {self.__class__.__name__} tools")

        @self.server.tool(parse_docstring=True)
        async def get_db_sleeptery():
            """
                Получить список доступных баз sleeptery для будущего
                получения всех данных о пользователе.
                Возвращает имена доступных БД
            """
            return await get_database()


        @self.server.tool(parse_docstring=True)
        async def get_tables_db(database_name: str):
            """
                Получить имена таблиц в выбранной базе.

                Args:
                    database_name: Имя базы из результата get_database_sleeptery.
            """
            return await get_tables(
                database_name=database_name
            )


        @self.server.tool(parse_docstring=True)
        async def get_columns_db(
            database_name: str, 
            table_name: str
        ):
            """Получить имена и типы колонок таблицы схемы public перед составлением SQL.

            Args:
                database_name: Имя базы из результата get_database_sleeptery.
                table_name: Имя таблицы из результата get_tables_db, без префикса public.
            """
            return await get_columns(
                database_name=database_name, 
                table_name=table_name
            )


        @self.server.tool(parse_docstring=True)
        async def execute_query_db(
            database_name: str,
            query: str,
            values: dict[str, Any] | None = None,
        ):
            """Выполнить один SQL-запрос на чтение для проверки аккаунта sleeptery.

            Сначала узнай таблицы и колонки через инструменты БД. Выбирай только
            необходимые поля, фильтруй по идентификатору аккаунта и используй LIMIT.
            Возвращает список строк в виде словарей или объект с полем error.
            Пустой список означает, что совпадений нет. Изменение данных
            запрещено транзакцией READ ONLY.

            Args:
                database_name: Имя базы из результата get_database_sleeptery.
                query: SQL-запрос SELECT, в том числе WITH ... SELECT. Передавай значения пользователя через параметры :name.
                values: Значения именованных параметров без двоеточия в ключах, например {"email": "user@example.com"} для :email.
            """
            try:
                return await execute_query(
                    database_name=database_name,
                    query=query,
                    values=values,
                )
            except DataError:
                return {
                    "error": "invalid_query_value",
                    "hint": (
                        "Сверь тип и значение параметра с типом колонки. "
                        "Для даты или времени в ISO-строке явно приведи параметр "
                        "через text к типу колонки, например "
                        "CAST(CAST(:since AS text) AS timestamptz)."
                    ),
                }

        

    # Здесь можно добавить регистрацию конкретных промптов для StSleepMCP
    def _register_prompts(self):
        log.info(f"Начали собирать {self.__class__.__name__} prompts")