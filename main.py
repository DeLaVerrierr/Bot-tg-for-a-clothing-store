import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Включаем логирование для получения информации об ошибках
logging.basicConfig(level=logging.INFO)

# Создаем объект бота
bot = Bot(token='6271392217:AAHV50k3yWCPsj0rTEF6yoJkvTXJvVXjaQU')

# Создаем объект диспетчера
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Функция, которая будет вызываться при получении команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    # Создаем список кнопок
    buttons = [
        [KeyboardButton("Узнать информацию о моем заказе")],
        [KeyboardButton("О боте")],
        [KeyboardButton(text="Есть вопросы? Свяжитесь со мной", url="https://t.me/de_la_verrier")]
    ]

    # Создаем объект ReplyKeyboardMarkup и передаем ему список кнопок
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)

    await message.answer("Привет! Я бот сайта GU.com.", reply_markup=reply_markup)

# Функция, которая будет вызываться при получении текстового сообщения
@dp.message_handler(Text(equals="Узнать информацию о моем заказе"))
async def get_order_info(message: types.Message):
    await message.answer("Введите номер заказа:")

# Обрабатываем введенный номер заказа
@dp.message_handler()
async def process_order_number(message: types.Message):
    order_number = message.text
    if order_number == "О боте":
        response_text = "Этот бот является частью сайта GU.com. Он предназначен для обработки заказов и оплаты. " \
                        "Вы можете использовать кнопку 'Узнать информацию о моем заказе' для получения информации " \
                        "о вашем заказе по номеру. Приятного использования!"
        await message.answer(response_text)
        return
    if order_number == 'Есть вопросы? Свяжитесь со мной':
        response_text = 'https://t.me/de_la_verrier'
        await message.answer(response_text)
        return
    if order_number == 'Бейби фокс':
        response_text = 'Самый самый бейби фокс это' \
                        'https://t.me/lunxkitty'
        await message.answer(response_text)
        return
    if not order_number.isdigit():
        response_text = "Чтобы узнать информацию о вашем заказе, пожалуйста, введите номер заказа."
        await message.answer(response_text)
        return

    response = requests.get(f'http://127.0.0.1:8000/get_order_info/{order_number}/')
    if response.status_code == 200:
        order_info = response.json()
        if 'recipient_name' in order_info:
            response_text = f"Информация о заказе {order_number}:\n" \
                            f"Имя: {order_info['recipient_name']}\n" \
                            f"Страна: {order_info['country']}\n" \
                            f"Номер телефона: ****{order_info['mobile_phone']}\n" \
                            f"Метод оплаты: {order_info['payment_method']}\n" \
                            f"Сумма в bitcoin: {order_info['bitcoin_amount']}\n" \
                            f"Сумма в рублях: {order_info['total_rubles']}\n" \
                            f"Сумма в долларах: {order_info['total']}\n"
            await message.answer(response_text)
        else:
            response_text = f"Заказ с номером {order_number} не существует."
            await message.answer(response_text)
    else:
        response_text = "Ошибка получения информации о заказе"
        await message.answer(response_text)

def main():
    executor.start_polling(dp, skip_updates=True)

if __name__ == '__main__':
    main()
