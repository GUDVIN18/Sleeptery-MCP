from app.include.config import config
from app.include.sender import AsyncSender
from app.include.logging_config import logger as log
from app.include.decorator import current_time
from app.integrations.st_account__manager.schemas import UserProfile


@current_time
async def get_user_profile(user_id: int):
    async with AsyncSender() as client:
        response = await client.get(
            url=f"{config.ST_ACCOUNT_MANAGER_URL}/user/profile/inner",
            headers={"Secret": f"{config.DOCKER_SECRET}"},
            timeout=3,
            params={
                'user_id': user_id
            }
        )
        log.info(f"Получили ответ от сервера: {response}")
        return UserProfile.model_validate(response)
