import asyncio
import logging

from database.db_manager import db_manager
from tg_bot.bot_manager import start_bot


async def main():
    db_manager.init('database')
    db_manager.start_app()

    await start_bot()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())


