import datetime as dt
from enum import Enum
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_serializer


class GetUserStatsRequest(BaseModel):
    user_id: int = Field(
        gt=0,
        description=(
            "ID пользователя Sleeptery. "
            "Бери из контекста пользователя, не придумывай."
        ),
    )

    start_date: dt.date = Field(
        description=(
            "Начало периода анализа сна. "
            "Дата строго в формате YYYY-MM-DD, например 2026-09-29."
        ),
    )

    end_date: dt.date = Field(
        description=(
            "Конец периода анализа сна. "
            "Дата строго в формате YYYY-MM-DD"
            "Строго Не может быть раньше start_date."
        ),
    )


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int = Field(..., description="Id пользователя из st_auth")
    user_uuid: UUID = Field(..., description="UUID пользователя из st_auth")

class DeviationType(str, Enum):
    """Тип отклонения от режима"""
    BEDTIME = "bedtime"
    WAKEUP = "wakeup"
    BOTH = "both"


class StartEndTime(BaseModel):
    model_config = ConfigDict(json_schema_mode_override="serialization")
    
    actual_sleep_start: dt.datetime = Field(
        ...,
        validation_alias="start_time",
        description=(
            "ФАКТИЧЕСКОЕ время начала сна — во сколько пользователь реально уснул. "
            "Не путать с плановым временем отхода ко сну bedtime_at."
        ),
    )

    actual_wakeup_time: dt.datetime = Field(
        ...,
        validation_alias="end_time",
        description=(
            "ФАКТИЧЕСКОЕ время окончания сна — во сколько пользователь реально проснулся. "
            "Не путать с плановым временем пробуждения wakeup_at."
        ),
    )

class SleepDurationStats(StartEndTime):
    duration_asleep_state_seconds: float = Field(0, description="Общее время сна")
    duration_awake_state_seconds: float = Field(0, description="Бодрствование")
    duration_light_sleep_state_seconds: float = Field(0, description="Легкий сон")
    duration_qualitative_sleep_seconds: float = Field(0, description="Качественный сон")
    duration_rem_sleep_state_seconds: float = Field(0, description="REM Быстрый сон")
    duration_deep_sleep_state_seconds: float = Field(0, description="DEEP Глубокий сон")


class SleepPattern(BaseModel):
    model_config = ConfigDict(json_schema_mode_override="serialization")

    bed_in_time: Optional[bool] = Field(None, description="Режим сна: лег ли вовремя")
    wake_in_time: Optional[bool] = Field(None, description="Режим сна: встал ли вовремя")
    planned_bedtime: Optional[dt.time] = Field(
        None,
        validation_alias="bedtime_at",
        description=(
            "Плановое время отхода ко сну. "
            "НЕ является фактическим временем засыпания."
        ),
    )

    planned_wakeup_time: Optional[dt.time] = Field(
        None,
        validation_alias="wakeup_at",
        description=(
            "Плановое время пробуждения. "
            "НЕ является фактическим временем пробуждения."
        ),
    )
    bedtime_deviation_seconds: Optional[float] = Field(None, description="Режим сна: отклонение фактического времени засыпания от запланированного")
    wakeup_deviation_seconds: Optional[float] = Field(None, description="Режим сна: отклонение фактического времени пробуждения от запланированного")


class PhaseType(str, Enum):
    """Тип отклонения от режима"""
    LIGHT = "light"
    DEEP = "deep"
    REM = "rem"
    AWAKE = "awake"
    UNKNOWN = "unknown"


class SleepPhase(BaseModel):
    type: PhaseType = Field(..., description="Тип фазы (light|deep|rem|awake)")
    start_date: dt.datetime = Field(..., description="Дата и время начала фазы")
    end_date: dt.datetime = Field(..., description="Дата и время конца фазы")
    duration_in_seconds: int = Field(..., description="Продолжительность фазы")


class SessionType(str, Enum):
    SLEEPRING = "sleepring"
    HEALTH = "health"
    OTHER = "other"
    MANUAL = "manual"


class SleepDetailDurationStats(SleepDurationStats):
    id: Optional[int] = Field(None, description="ID записи SleepteryRingSleepData в БД или None, если не SleepRing")
    type: Optional[SessionType] = Field(None, description="Тип устройства, который записал эту сессию")
    details: Optional[list[SleepPhase]] = Field(None, description="Фазы сна")


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


class SleepPhasesStats(BaseModel):
    duration_asleep_seconds: float = Field(0, description="Общее время сна")
    duration_qualitative_sleep_seconds: float = Field(0, description="Качественный сон")
    duration_awake_seconds: float = Field(0, description="Бодрствование")

    sleep_phases: Optional[SleepPhases] = Field(None, description="Фазы сна")


class SleepStats(StartEndTime, SleepPhasesStats, Rating):
    is_manual: bool = Field(False, description="Является ли данные о сне, внесенными вручную")

    awakenings_count: int = Field(0, description="Количество пробуждений за ночь", ge=0)
    sleep_amount_pillows: int = Field(..., description="Количество подушек, начисленных за сон", ge=0)


class SleepDailyExtendStats(UserInfo):
    id: int = Field(..., description="ID записи в базе данных")
    date: dt.date = Field(..., description="Выбранная дата")
    sleep_pattern: SleepPattern = Field(..., description="Режим сна")
    amount_pillows: int = Field(..., description="Количество подушек, начисленных за сон + режим", ge=0)
    sleep_stats: SleepStats = Field(..., description="Данные о сне")
    sleep_sessions: Optional[list[SleepDetailDurationStats]] = Field(None, description="Сессии сна с фазами")
    suspicious_deviation: bool = Field(False, description="Есть ли подозрительное отклонение")
    deviation_type: Optional[DeviationType] = Field(None, description="Тип отклонения")
    is_editable: bool = Field(False, description="Можно ли редактировать")
    average_wakeup_time: Optional[dt.time] = Field(None, description="Среднее время пробуждения за последние дни")

    # костыль для приложения, текущая версия на 11.2025 ломает график при пустом списке, в будущем убрать
    @model_serializer(mode='wrap')
    def convert_empty_list_to_none(self, serializer, info):
        data = serializer(self)
        if 'sleep_sessions' in data and isinstance(data['sleep_sessions'], list) and len(data['sleep_sessions']) == 0:
            data['sleep_sessions'] = None
        return data
