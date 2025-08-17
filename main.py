import asyncio
from aiogram import Bot, Dispatcher, Router

class TGBot:
    def __init__(self, router: Router) -> None:
       token = '8283069945:AAGE67y1hIfmClH2Vtf6rLKRkzDMUiwqRIE'
       self.bot = Bot(token)
       self.dp = Dispatcher()
       self.dp.include_router(router)

    async def update_bot(self, update: dict) -> None:
        await self.dp.feed_raw_update(self.bot, update)
        await self.bot.session.close()

    async def set_webhook(self):
        webhook_url = 'https://dera-dun.vercel.app/'
        await self.bot.set_webhook(webhook_url)
        await self.bot.session.close()
