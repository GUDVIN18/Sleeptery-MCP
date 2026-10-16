from app.include.config import config
from app.include.sender import AsyncSender
from app.include.logging_config import logger as log
from app.include.decorator import current_time
from app.integrations.st_sleep.shemas import (
    GetUserStatsRequest,
    SleepDailyExtendStats,
    SleepDetailDurationStats,
    SleepWeeklyExtendStats
)
import datetime as dt
from app.service import get_user_profile


def _to_user_datetime(value: dt.datetime, timezone: dt.timezone) -> dt.datetime:
    # Даты без tzinfo в ответе сервиса также хранятся в UTC.
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(timezone)


def _to_user_time(value: dt.time | None, timezone: dt.timezone) -> dt.time | None:
    if value is None:
        return None
    value_with_date = dt.datetime.combine(dt.date(2000, 1, 1), value)
    return _to_user_datetime(value_with_date, timezone).time()


@current_time
async def get_user_daily_stats(
    data: GetUserStatsRequest
) -> list[SleepDailyExtendStats]:
    async with AsyncSender() as client:
        response = await client.get(
            url=f"{config.ST_SLEEP_URL}/sleep/statistics/inner/daily-v3",
            headers={"Secret": f"{config.DOCKER_SECRET}"},
            timeout=3,
            params=data.model_dump(mode="json"),
        )
        if not response:
            return None
        user_profile = await get_user_profile(data.user_id)
        timezone = dt.timezone(dt.timedelta(minutes=user_profile.utc_offset or 0))

        stats = []
        for item in response:
            resp = SleepDailyExtendStats.model_validate(item)
            resp.sleep_stats.actual_sleep_start = _to_user_datetime(resp.sleep_stats.actual_sleep_start, timezone)
            resp.sleep_stats.actual_wakeup_time = _to_user_datetime(resp.sleep_stats.actual_wakeup_time, timezone)
            resp.sleep_pattern.planned_bedtime = _to_user_time(resp.sleep_pattern.planned_bedtime, timezone)
            resp.sleep_pattern.planned_wakeup_time = _to_user_time(resp.sleep_pattern.planned_wakeup_time, timezone)
            resp.average_wakeup_time = _to_user_time(resp.average_wakeup_time, timezone)

            for session in resp.sleep_sessions or []:
                session: SleepDetailDurationStats
                session.actual_sleep_start = _to_user_datetime(session.actual_sleep_start, timezone)
                session.actual_wakeup_time = _to_user_datetime(session.actual_wakeup_time, timezone)
                for phase in session.details or []:
                    phase.start_date = _to_user_datetime(phase.start_date, timezone)
                    phase.end_date = _to_user_datetime(phase.end_date, timezone)
            stats.append(resp)
        print(stats)
        return stats


@current_time
async def get_user_weekly_stats(
    data: GetUserStatsRequest
) -> list[SleepWeeklyExtendStats]:
    async with AsyncSender() as client:
        response = await client.get(
            url=f"{config.ST_SLEEP_URL}/sleep/statistics/inner/weekly-v2",
            headers={"Secret": f"{config.DOCKER_SECRET}"},
            timeout=3,
            params=data.model_dump(mode="json")
        )
        log.info(f"Получили ответ от сервера: {response}")
        if not response:
            return None
        user_profile = await get_user_profile(data.user_id)
        timezone = dt.timezone(dt.timedelta(minutes=user_profile.utc_offset or 0))

        stats = []
        for item in response:
            resp = SleepWeeklyExtendStats.model_validate(item)
            mean = resp.sleep_period_stats.mean_sleep_stats
            mean.start_time = _to_user_time(mean.start_time, timezone)
            mean.end_time = _to_user_time(mean.end_time, timezone)
            stats.append(resp)

        return stats






if __name__ == "__main__":
    import asyncio

    # Пример вызова функции
    asyncio.run(get_user_daily_stats(
        user_id=596,
        start_date=dt.date(2026, 9, 29),
        end_date=dt.date(2026, 9, 29)
    ))
