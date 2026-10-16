import datetime as dt
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from datetime import date


class GetUserDiaryStatsRequest(BaseModel):
    start_date: date = Field(
        description="Начало периода анализа дневника."
    )
    end_date: date = Field(
        description="Конец периода анализа дневника. Не может быть раньше start_date."
    )


class HabitType(str, Enum):
    """
    Модель, описывающая тип привычки.
    custom - привычка, добавленная пользователем,
    default - дефолтная привычка приложения
    """

    CUSTOM = "custom"
    DEFAULT = "default"


class Habit(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='allow')

    type: HabitType = Field(..., description="Тип привычки")
    name: Optional[str] = Field(
        None,
        description="Уникальное английское обозначение для дефолтной привычки. Для кастомной может быть null",
        max_length=63,
    )
    text: str = Field(..., description="Текстовое описание привычки", max_length=63)
    icon_url: Optional[str] = Field(
        None,
        description="URL иконки привычки",
        max_length=255
    )


class TimeThreshold(BaseModel):
    time: str = Field(..., description="Пороговое время в формате HH:MM")
    before_text: str = Field(..., description="Текст привычки с пометкой 'до'")
    after_text: str = Field(..., description="Текст привычки с пометкой 'после'")


class HabitWithTimeInfo(Habit):
    time_threshold: TimeThreshold | None = Field(
        None, description="Информация о временном пороге, если есть"
    )
    marked_yes_before: bool = Field(
        False, description="Была ли привычка выбрана до порогового времени"
    )
    marked_yes_after: bool = Field(
        False, description="Была ли привычка выбрана после порогового времени"
    )


class DiaryRecordBase(BaseModel):
    date: dt.date = Field(..., description="Дата записи в дневнике")


class UserDiaryRecordMeta(BaseModel):
    id: int = Field(..., description="Id записи в БД")
    created_at: dt.datetime = Field(..., description="Дата и время создания записи")
    updated_at: Optional[dt.datetime] = Field(None, description="Дата и время обновления записи")
    deleted_at: Optional[dt.datetime] = Field(None, description="Дата и время удаления записи")


class DailyHabits(DiaryRecordBase):
    habits: list[HabitWithTimeInfo] | None = Field(
        None, description="Список привычек и ритуалов. Может быть пустым", max_items=13
    )


class DaySatisfaction(str, Enum):
    DEFINITELY_SATISFIED = "definitely_satisfied"
    NOT_SURE = "not_sure"
    HAD_BETTER_DAYS = "had_better_days"


class UserDailyRates(DiaryRecordBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(..., description="Id пользователя из st_auth")
    sleep_rate: Optional[int] = Field(None, description="Оценка сна", gt=0, le=5)
    day_rate: Optional[int] = Field(None, description="Оценка продуктивности", gt=0, le=5)
    is_happy: Optional[bool] = Field(None, description="Оценка самочувствия")
    day_satisfaction: Optional[DaySatisfaction] = Field(None, description="Оценка удовлетворенности днем")
    energy_level: Optional[int] = Field(None, description="Оценка уровня энергии", gt=0, le=5)
    sleep_comment: Optional[str] = Field(None, description="Комментарий ко сну")


class UserDiaryRecord(UserDailyRates, UserDiaryRecordMeta, DailyHabits):
    model_config = ConfigDict(from_attributes=True)

    duration_qualitative_sleep_seconds: Optional[float] = Field(
        None, description="Суммарное время качественного сна"
    )
    amount_pillows: Optional[int] = Field(
        0, description="Количество подушек за заполнение дневника", ge=0
    )
