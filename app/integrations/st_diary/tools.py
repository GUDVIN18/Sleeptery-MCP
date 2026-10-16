from app.include.config import config
from app.include.sender import AsyncSender
from app.include.logging_config import logger as log
from app.include.decorator import current_time
from app.integrations.st_diary.schemas import GetUserDiaryStatsRequest, UserDiaryRecord
import datetime as dt


@current_time
async def get_user_diary_stats(
    user_id: int,
    start_date: dt.date,
    end_date: dt.date
) -> list[UserDiaryRecord]:
    async with AsyncSender() as client:
        response = await client.get(
            url=f"{config.ST_DIARY_URL}/diary/users/{user_id}/records",
            headers={"Secret": f"{config.DOCKER_SECRET}"},
            timeout=3,
            params=GetUserDiaryStatsRequest(
                start_date=start_date,
                end_date=end_date
            ).model_dump()
        )
        log.info(f"Получили ответ от сервера: {response}")
        return response

@current_time
async def get_user_goal(
    user_id: int,
    date: dt.date
):
    async with AsyncSender() as client:
        response = await client.get(
            url=f"{config.ST_DIARY_URL}/user-goal/inner/user/{user_id}",
            headers={"Secret": f"{config.DOCKER_SECRET}"},
            timeout=3,
            params={"date": date}
        )
        log.info(f"{user_id}: ST_DIARY: {response=}")

        if response:
            return response

        return "Цель не задана"