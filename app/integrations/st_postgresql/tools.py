from typing import Any
from st_bases.db import DBConnPool
from app.include.config import config
from app.include.logging_config import logger as log


async def get_database():
    async with DBConnPool().isolated_connection(
        db_url=config.DB_AI_URL
    ) as conn:        
        response = await conn.fetch_all(
            query="""
                SELECT datname AS database_name
                FROM pg_database
                WHERE datistemplate = false
                    AND has_database_privilege(datname, 'CONNECT')
                    AND datallowconn = true
                    AND datname LIKE 'st_%'
                ORDER BY datname;
            """
        )
        log.success(f"Доступные базы данных: {[row['database_name'] for row in response]}")
        return f"Доступные базы данных: {[row['database_name'] for row in response]}"


async def get_tables(
        database_name: str
    ):
    async with DBConnPool().isolated_connection(
        database_name=database_name,
        db_url=config.DB_AI_URL
    ) as conn:
        response = await conn.fetch_all(
            query="""
                SELECT
                    table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                    AND table_name NOT LIKE '%yoyo%'
                ORDER BY table_name;
            """,
            values={})
        log.success(f"Доступные таблицы в базе {database_name}: {[row['table_name'] for row in response]}")
        return f"Доступные таблицы в базе {database_name}: {[row['table_name'] for row in response]}"


async def get_columns(
        database_name: str, 
        table_name: str
    ):
    async with DBConnPool().isolated_connection(
        database_name=database_name,
        db_url=config.DB_AI_URL
    ) as conn:
        response = await conn.fetch_all(
            query="""
                SELECT
                    table_name,
                    column_name,
                    data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND table_name = :table_name
                ORDER BY ordinal_position;
            """,
            values={"table_name": table_name}
        )
        log.success(f"Поулчили список колонок в {database_name}/{table_name}")
        return [{
                "column_name": row["column_name"], 
                "data_type": row["data_type"]
            } for row in response]



async def execute_query(
    database_name: str,
    query: str,
    values: dict[str, Any] | None = None,
):
    async with DBConnPool().isolated_connection(
        database_name=database_name,
        db_url=config.DB_AI_URL
    ) as conn:
        async with conn.transaction(readonly=True):
            log.success(f"Сформировали запрос: {query=}, {values=}")
            response = await conn.fetch_all(query=query, values=values)
            return [dict(row) for row in response]
