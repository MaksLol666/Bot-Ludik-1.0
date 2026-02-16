import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from database import db
from handlers import (
    start, games, dice_duel, mines, lottery, profile, top, status,
    promo, business, donate, bonus, referral, admin, glc, daily_quests
)
from utils.promo_setup import create_start_promos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def on_startup(bot: Bot):
    logger.info("Запуск бота...")
    await db.connect()
    await create_start_promos()
    await daily_quests.init_quests_table()  # Добавить
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        lottery.draw_lottery, 
        'cron', 
        day_of_week='sun', 
        hour=20, 
        minute=0,
        args=[bot]
    )
    scheduler.start()
    
    logger.info("Бот запущен!")

async def on_shutdown():
    logger.info("Остановка бота...")
    await db.close()
    logger.info("Бот остановлен")

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(start.router)
    dp.include_router(games.router)
    dp.include_router(dice_duel.router)
    dp.include_router(mines.router)
    dp.include_router(lottery.router)
    dp.include_router(profile.router)
    dp.include_router(top.router)
    dp.include_router(status.router)
    dp.include_router(promo.router)
    dp.include_router(business.router)
    dp.include_router(donate.router)
    dp.include_router(bonus.router)
    dp.include_router(referral.router)
    dp.include_router(admin.router)
    dp.include_router(glc.router)
    dp.include_router(daily_quests.router)  # Добавить
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
