from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field 

class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(..., description="Уникальный id пользователя")
    user_uuid: UUID = Field(..., description="Уникальный uuid пользователя")
    email: str = Field(..., description="Адрес электронной почты")
    username: str = Field(..., description="Уникальный user name", max_length=63)
    fullname: Optional[str] = Field(None, description="Имя и фамилия", max_length=63)
    utc_offset: Optional[int] = Field(
        None, description="Смещение по времени относительно UTC в минутах"
    )
