import httpx
from typing import Optional
from app.include.logging_config import logger as log


class AsyncSender:
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        log.info("Инициализация AsyncSender")
        if self.client is None:
            self.client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        log.info("Закрытие AsyncSender")
        await self.client.aclose()
        self.client = None

    async def get(
            self, 
            url: str, 
            params: Optional[dict] = None, 
            headers: Optional[dict] = None,
            timeout: Optional[int] = None,
            **kwargs):
        if self.client is None:
            raise RuntimeError("AsyncSender client is not initialized.")
        response = await self.client.get(
            url, 
            params=params, 
            headers=headers, 
            timeout=timeout,
            **kwargs)
        response.raise_for_status()
        return response.json()

    async def post(
            self, 
            url: str, 
            data: Optional[dict] = None, 
            headers: Optional[dict] = None,
            timeout: Optional[int] = None,
            **kwargs
        ):
        if self.client is None:
            raise RuntimeError("AsyncSender client is not initialized.")
        response = await self.client.post(
            url, 
            json=data, 
            headers=headers, 
            timeout=timeout,
            **kwargs
        )
        response.raise_for_status()
        return response.json()