import asyncio
import logging
import sys
from typing import Any, Dict

import aiohttp
from aiogram import Bot, types
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.filters import CommandStart
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

API_TOKEN = '6742462911:AAFwa0T2m_i8sOi7dyagLQvOE0LvSYQCEbo'
TOKEN_DATA = {}
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


class LogIn(StatesGroup):
    email = State()
    password = State()


class ResetPassword(StatesGroup):
    old_password = State()
    new_password = State()


@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext) -> None:
    await state.set_state(LogIn.email)
    await message.answer(text="Enter your email")


@dp.message(LogIn.email)
async def handle_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await state.set_state(LogIn.password)
    await message.answer(text="Enter your password")


async def send_data(message: Message, data:  Dict[str, Any], url: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, json=data) as response:
            if response.status == 200:
                await message.answer(text="You logged in successfully")
                token = await response.json()
                TOKEN_DATA.update({"access_token": token["access_token"]})
            else:
                await message.answer(text="You logged in unsuccessfully")


@dp.message(LogIn.password)
async def handle_password(message: types.Message, state: FSMContext):
    data = await state.update_data(password=message.text)
    await state.clear()
    await send_data(message=message, data=data, url="http://127.0.0.1:8000/token/")


@dp.message(Command(commands=["reset_password"]))
async def reset_password(message: Message, state: FSMContext):
    await state.set_state(ResetPassword.old_password)
    await message.answer(text="Enter your old password")


@dp.message(ResetPassword.old_password)
async def handle_old_password(message: Message, state: FSMContext):
    await state.update_data(old_password=message.text)
    await state.set_state(ResetPassword.new_password)
    await message.answer(text="Enter your new password")


async def send_reset_data(message: Message, data: Dict[str, Any], url: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, json=data, headers={"x-token": TOKEN_DATA.get("access_token")}) as response:
            if response.status == 200:
                await message.answer(text="You are successfully changed a password")
            else:
                await message.answer(text="You are successfully changed a password")


@dp.message(ResetPassword.new_password)
async def handle_new_password(message: Message, state: FSMContext):
    data = await state.update_data(password=message.text)
    await state.clear()

    await send_reset_data(message=message, data=data, url="http://127.0.0.1:8000/reset_password/")


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
