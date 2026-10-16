import datetime as dt
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int = Field(..., description="Id пользователя из st_auth")
    user_uuid: UUID = Field(..., description="UUID пользователя из st_auth")


class SleepRating(str, Enum):
    """Оценки качества фаз сна"""
    GOOD = "хорошо"
    POOR = "так себе"

    @classmethod
    def get_rating_color(cls, rating: Optional["SleepRating"]) -> str:
        """Возвращает цвет для рейтинга фазы сна"""
        if rating == cls.GOOD:
            return "#4CAF50"  # Зеленый
        elif rating == cls.POOR:
            return "#F44336"  # Красный
        else:
            return "#9E9E9E"  # Серый

    @classmethod
    def from_phases(cls, ratings: list[str]) -> Optional[str]:
        """
        Определяет общий рейтинг сна на основе рейтингов фаз
        """
        ratings = [r for r in ratings if r is not None]
        if not ratings:
            return None

        if cls.GOOD in ratings:
            return cls.GOOD

        return cls.POOR


class SleepPhaseRate(BaseModel):
    light_sleep_rating: Optional[SleepRating] = Field(None, description="Оценка легкого сна")
    deep_sleep_rating: Optional[SleepRating] = Field(None, description="Оценка глубокого сна")
    rem_sleep_rating: Optional[SleepRating] = Field(None, description="Оценка REM-сна")


class SleepMeans(SleepPhaseRate):
    mean_duration_asleep_state_seconds: Optional[float] = Field(0, description="Общее время сна")
    mean_duration_awake_state_seconds: Optional[float] = Field(0, description="Бодрствование")
    mean_duration_light_sleep_state_seconds: Optional[float] = Field(0, description="Легкий сон")
    mean_duration_qualitative_sleep_seconds: Optional[float] = Field(0, description="Качественный сон")
    mean_duration_rem_sleep_state_seconds: Optional[float] = Field(0, description="REM Быстрый сон")
    mean_duration_deep_sleep_state_seconds: Optional[float] = Field(0, description="DEEP Глубокий сон")
    mean_duration_manual_sleep_seconds: Optional[float] = Field(0, description="Среднее время ручного сна")
    mean_start_time: Optional[dt.time] = Field(None, description="Среднее время начала сна")
    mean_end_time: Optional[dt.time] = Field(None, description="Среднее время конца сна")
    mean_start_time_deviation_seconds: Optional[int] = Field(
        0, description="Среднее отклонение времени отхода ко сну для вычисления mean_start_time",
    )
    mean_end_time_deviation_seconds: Optional[int] = Field(
        0, description="Среднее отклонение времени просыпания для вычисления mean_end_time",
    )
    num_sleeps: Optional[int] = Field(0, description="Количество снов, участвовавших в подсчете средних")
    duration_asleep_state_seconds: Optional[float] = Field(0, description="Суммарное время сна")
    duration_qualitative_sleep_seconds: Optional[float] = Field(0, description="Суммарное время качественного сна")
    awakenings_count: int = Field(0, description="Количество пробуждений за ночь", ge=0)


class SleepPillows(BaseModel):
    amount_pillows: int = Field(..., description="Количество подушек, начисленных за сон + режим", ge=0)
    light_sleep_pillows: Optional[int] = Field(None, description="Количество подушек за легкий сон", ge=0)
    deep_sleep_pillows: Optional[int] = Field(None, description="Количество подушек за глубокий сон", ge=0)
    rem_sleep_pillows: Optional[int] = Field(None, description="Количество подушек за REM-сон", ge=0)


class SleepWeeklyStats(SleepMeans, UserInfo, SleepPillows):
    num_of_week: int = Field(..., description="Номер недели")
    start_date: dt.date = Field(..., description="Дата начала недели")
    end_date: dt.date = Field(..., description="Дата конца недели")


class SleepMonthlyStats(SleepMeans, UserInfo, SleepPillows):
    start_date: dt.date = Field(..., description="Дата начала месяца")
    end_date: dt.date = Field(..., description="Дата конца месяца")


class SleepWeeklyStatsFromDB(SleepWeeklyStats):
    id: int = Field(..., description="Id записи в базе данных")
    created_at: dt.datetime = Field(..., description="Дата создания записи")
    updated_at: Optional[dt.datetime] = Field(None, description="Дата обновления записи")


class SleepMonthlyStatsFromDB(SleepMonthlyStats):
    id: int = Field(..., description="Id записи в базе данных")
    created_at: dt.datetime = Field(..., description="Дата создания записи")
    updated_at: Optional[dt.datetime] = Field(None, description="Дата обновления записи")


class Rating(BaseModel):
    rating_text: Optional[str] = Field(None, description="Текстовая оценка")
    rating_color: str = Field("#9E9E9E", description="Цвет для отображения рейтинга")


class SleepPhaseDetail(Rating):
    duration_seconds: float = Field(0, description="Продолжительность фазы в секундах")
    amount_pillows: Optional[int] = Field(None, description="Количество подушек за эту фазу", ge=0)


class SleepPhases(BaseModel):
    light_sleep: Optional[SleepPhaseDetail] = Field(None, description="Легкий сон")
    deep_sleep: Optional[SleepPhaseDetail] = Field(None, description="Глубокий сон")
    rem_sleep: Optional[SleepPhaseDetail] = Field(None, description="REM-сон")


    @classmethod
    def from_period(cls, stats: SleepMonthlyStatsFromDB | SleepWeeklyStatsFromDB) -> 'SleepPhases':
        light_sleep = None
        if stats.mean_duration_light_sleep_state_seconds > 0:
            light_sleep = SleepPhaseDetail(
                duration_seconds=stats.mean_duration_light_sleep_state_seconds,
                amount_pillows=stats.light_sleep_pillows if stats.light_sleep_pillows else None,
                rating_text=stats.light_sleep_rating.value if stats.light_sleep_rating else None,
                rating_color=SleepRating.get_rating_color(stats.light_sleep_rating)
            )

        deep_sleep = None
        if stats.mean_duration_deep_sleep_state_seconds > 0:
            deep_sleep = SleepPhaseDetail(
                duration_seconds=stats.mean_duration_deep_sleep_state_seconds,
                amount_pillows=stats.deep_sleep_pillows if stats.deep_sleep_pillows else None,
                rating_text=stats.deep_sleep_rating.value if stats.deep_sleep_rating else None,
                rating_color=SleepRating.get_rating_color(stats.deep_sleep_rating)
            )

        rem_sleep = None
        if stats.mean_duration_rem_sleep_state_seconds > 0:
            rem_sleep = SleepPhaseDetail(
                duration_seconds=stats.mean_duration_rem_sleep_state_seconds,
                amount_pillows=stats.rem_sleep_pillows if stats.rem_sleep_pillows else None,
                rating_text=stats.rem_sleep_rating.value if stats.rem_sleep_rating else None,
                rating_color=SleepRating.get_rating_color(stats.rem_sleep_rating)
            )
        return cls(
            light_sleep=light_sleep,
            deep_sleep=deep_sleep,
            rem_sleep=rem_sleep
        )


class SleepPhasesStats(BaseModel):
    duration_asleep_seconds: float = Field(0, description="Общее время сна")
    duration_qualitative_sleep_seconds: float = Field(0, description="Качественный сон")
    duration_awake_seconds: float = Field(0, description="Бодрствование")

    sleep_phases: Optional[SleepPhases] = Field(None, description="Фазы сна")


class MeanSleepStats(SleepPhasesStats):
    start_time: Optional[dt.time] = Field(None, description="Время начала сна")
    end_time: Optional[dt.time] = Field(None, description="Время конца сна")
    duration_manual_sleep_seconds: Optional[float] = Field(0, description="Время ручного сна")

    @classmethod
    def from_period(cls, stats: SleepMonthlyStatsFromDB | SleepWeeklyStatsFromDB) -> 'MeanSleepStats':
        return  cls(
            duration_asleep_seconds=stats.mean_duration_asleep_state_seconds,
            duration_awake_seconds=stats.mean_duration_awake_state_seconds,
            duration_qualitative_sleep_seconds=stats.mean_duration_qualitative_sleep_seconds,
            duration_manual_sleep_seconds=stats.mean_duration_manual_sleep_seconds,
            start_time=stats.mean_start_time,
            end_time=stats.mean_end_time,
            sleep_phases=SleepPhases.from_period(stats) if stats.duration_qualitative_sleep_seconds > 0 else None,
        )


class SleepPeriodStats(BaseModel):
    num_sleeps: Optional[int] = Field(0, description="Количество снов, участвовавших в подсчете средних")

    mean_sleep_stats: MeanSleepStats = Field(..., description="Средние значения данных о снах")

    duration_asleep_seconds: Optional[float] = Field(0, description="Суммарное время сна")
    duration_qualitative_sleep_seconds: Optional[float] = Field(0, description="Суммарное время качественного сна")
    awakenings_count: int = Field(0, description="Количество пробуждений", ge=0)

    amount_pillows: int = Field(..., description="Количество подушек, начисленных за сон + режим", ge=0)

    @classmethod
    def from_period(cls, stats: SleepMonthlyStatsFromDB | SleepWeeklyStatsFromDB) -> 'SleepPeriodStats':
        return cls(
            num_sleeps=stats.num_sleeps,
            mean_sleep_stats=MeanSleepStats.from_period(stats),
            duration_asleep_seconds=stats.duration_asleep_state_seconds,
            duration_qualitative_sleep_seconds=stats.duration_qualitative_sleep_seconds,
            awakenings_count=stats.awakenings_count,
            amount_pillows=stats.amount_pillows,
        )


class SleepPeriodExtendStats(UserInfo):
    id: int = Field(..., description="ID записи в базе данных")
    start_date: dt.date = Field(..., description="Дата начала периода")
    end_date: dt.date = Field(..., description="Дата конца периода")
    sleep_period_stats: SleepPeriodStats = Field(..., description="Данные о снах за период")

    @classmethod
    def from_period(cls, stats: SleepMonthlyStatsFromDB | SleepWeeklyStatsFromDB) -> 'SleepPeriodExtendStats':
        return cls(
            id=stats.id,
            user_id=stats.user_id,
            user_uuid=stats.user_uuid,
            start_date=stats.start_date,
            end_date=stats.end_date,
            sleep_period_stats=SleepPeriodStats.from_period(stats),
        )


class SleepWeeklyExtendStats(SleepPeriodExtendStats):
    num_of_week: int = Field(..., description="Номер недели")

    @classmethod
    def from_period(cls, stats: SleepWeeklyStatsFromDB) -> 'SleepWeeklyExtendStats':
        return cls(
            num_of_week=stats.num_of_week,
            **SleepPeriodExtendStats.from_period(stats).model_dump(),
        )
