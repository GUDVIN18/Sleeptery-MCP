import datetime as dt
from typing import List
from mcp.server import MCPServer
from app.include.logging_config import logger as log
from app.integrations.st_sleep.tools import (
    get_user_daily_stats,
    get_user_weekly_stats
)
from app.integrations.st_sleep.shemas import (
    GetUserStatsRequest,
    SleepDailyExtendStats,
    SleepWeeklyExtendStats
)


class StSleepMCP:
    def __init__(self, server: MCPServer):
        self.server = server
        self._register_tools()
        self._register_prompts()

    # Здесь можно добавить регистрацию конкретных инструментов для StSleepMCP
    def _register_tools(self):
        log.info(f"Начали собирать {self.__class__.__name__} tools")

        @self.server.tool()
        async def user_daily_stats(
            data: GetUserStatsRequest
        ) -> list[SleepDailyExtendStats]:
            """
            Получить ежедневную статистику сна пользователя за выбранный период.

            Используй инструмент, когда для ответа необходимы фактические данные
            о сне пользователя: продолжительность и структура сна, фазы сна,
            пробуждения, сравнение дней или выявление закономерностей.

            Выбирай период в соответствии с вопросом пользователя.
            Для анализа одного дня используй одинаковые start_date и end_date.

            Основывай выводы только на полученных данных.
            Не придумывай отсутствующие показатели и не интерпретируй
            отсутствующие значения как нулевые.

            Если результат пустой, это означает только отсутствие записей
            сна за выбранный период.
            """
            
            return await get_user_daily_stats(
                data=data
            )


        @self.server.tool()
        async def user_weekly_stats(
            data: GetUserStatsRequest
        ) -> List[SleepWeeklyExtendStats]:
            """
            Получить общую недельную статистику пользователя за указанный период.

            Вызывай её, когда нужна общая статистика за неделю:
            для обзора, сводки, анализа.

            Определяй пользователя и период из запроса и доступного контекста.
            Если необходимых данных недостаточно, уточни их у пользователя.
            Не придумывай идентификатор пользователя или даты.
            """
            
            return await get_user_weekly_stats(
                data=data
            )

    # Здесь можно добавить регистрацию конкретных промптов для StSleepMCP
    def _register_prompts(self):
        log.info(f"Начали собирать {self.__class__.__name__} prompts")

        @self.server.prompt()
        async def analyze_daily_stats() -> str:
            """Инструкция по анализу данных из daily_stats"""
            return """
                Проанализируй данные сна пользователя за последнюю ночь.

                При анализе обращай внимание в следующем порядке:

                1. ОБЩАЯ ПРОДОЛЖИТЕЛЬНОСТЬ СНА
                - оцени duration_asleep_seconds;
                - учитывай duration_awake_seconds;
                - не путай время нахождения в постели с фактическим временем сна.

                2. РЕЖИМ СНА
                - сравни actual_sleep_start с planned_bedtime;
                - сравни actual_wakeup_time с planned_wakeup_time;
                - учитывай bedtime_deviation_seconds и wakeup_deviation_seconds;
                - используй bed_in_time и wake_in_time как дополнительные признаки соблюдения режима.

                3. КАЧЕСТВО И СТРУКТУРА СНА
                - оцени duration_qualitative_sleep_seconds;
                - проанализируй продолжительность light, deep и REM сна;
                - учитывай готовые rating_text фаз, если они присутствуют;
                - не делай вывод по одной фазе изолированно — оцени сон целиком.

                4. НЕПРЕРЫВНОСТЬ СНА
                - учитывай awakenings_count и duration_awake_seconds;
                - большое количество пробуждений или длительное бодрствование может указывать
                    на фрагментированный сон.

                5. ВРЕМЯ ПРОБУЖДЕНИЯ
                - сравни actual_wakeup_time с average_wakeup_time;
                - значительное отличие от обычного времени пользователя учитывай как изменение режима.

                6. СЕССИИ И ФАЗЫ
                - если доступны sleep_sessions/details, используй их для понимания структуры ночи,
                    последовательности фаз, пробуждений и отдельных сессий сна;
                - учитывай тип источника данных и is_manual.

                7. АНОМАЛИИ
                - обращай внимание на suspicious_deviation и deviation_type;
                - проверяй аномалию по фактическим временам и отклонениям, а не только по флагу.

                Сначала оцени сон в целом, затем выдели 1–3 наиболее значимых фактора,
                которые могли ухудшить или улучшить его.

                Не делай медицинских диагнозов и не утверждай причинно-следственную связь,
                если данные показывают только возможную зависимость.
                Не перегружай ответ второстепенными показателями.
            """
