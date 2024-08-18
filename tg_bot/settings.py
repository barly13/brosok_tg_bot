from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


bot_token = '7472527637:AAE_WRIi7_jPHshtOTkIOk7EX-a7NtEyjbc'
bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


users_ids = [865615562]

