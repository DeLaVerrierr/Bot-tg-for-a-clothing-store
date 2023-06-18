import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ContentTypes
from aiogram.utils import executor
import config
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Включаем логирование для получения информации об ошибках
logging.basicConfig(level=logging.INFO)

# Создаем объект бота С config.TOKEN я импортировал из файла config значение TOKEN
bot = Bot(token=config.TOKEN)

# Создаем объект диспетчера
dispatcher = Dispatcher(bot)
dispatcher.middleware.setup(LoggingMiddleware())




# pre checkout ответ должен быть до 10 сек
@dispatcher.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


# successful payment
@dispatcher.message_handler(content_types=ContentTypes.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    print('SUCCESSFUL PAYMENT:')
    payment_info = message.successful_payment.to_python()
    for k, v in payment_info.items():
        print(f"{k} = {v}")

    order_number = payment_info['invoice_payload']  # Получаем значение номера заказа из поля invoice_payload
    await bot.send_message('850931530', f"Покупатель оплатил заказ с номером {order_number}")

    await bot.send_message(message.chat.id,
                           f'Платеж на сумму {message.successful_payment.total_amount // 100}{message.successful_payment.currency} прошел успешно !!!')

# Функция, которая будет вызываться при получении команды /start
@dispatcher.message_handler(commands=['start'])
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
@dispatcher.message_handler(Text(equals="Узнать информацию о моем заказе"))
async def get_order_info(message: types.Message):
    await message.answer("Введите номер заказа:")


# Обрабатываем введенный номер заказа
@dispatcher.message_handler()
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
    if not order_number.isdigit():
        response_text = "Чтобы узнать информацию о вашем заказе, пожалуйста, введите номер заказа."
        await message.answer(response_text)
        return

#f"Сумма в рублях: {order_info['total']}\n"
#f"Сумма в bitcoin: {order_info['bitcoin_amount']}\n" \
#f"Метод оплаты: {order_info['payment_method']}\n" \
    response = requests.get(f'http://127.0.0.1:8000/get_order_info/{order_number}/')
    if response.status_code == 200:
        order_info = response.json()
        if 'recipient_name' in order_info:
            response_text = f"Информация о заказе {order_number}:\n" \
                            f"Имя: {order_info['recipient_name']}\n" \
                            f"Страна: {order_info['country']}\n" \
                            f"Номер телефона: ****{order_info['mobile_phone']}\n" \
                            f"Сумма: {order_info['total']} ₽\n"

            if order_info['DEVIL'] > 0:
                response_text += f"Футболка DEVIL: {order_info['DEVIL']} шт.\n"

            if order_info['BONES'] > 0:
                response_text += f"Футболка BONES: {order_info['BONES']} шт.\n"

            if order_info['LOVERS'] > 0:
                response_text += f"Футболка LOVERS: {order_info['LOVERS']} шт.\n"

            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton("Оплатить заказ", callback_data=f"pay_{order_number}"))

            await message.answer(response_text, reply_markup=keyboard)
        else:
            response_text = f"Заказ с номером {order_number} не существует."
            await message.answer(response_text)
    else:
        response_text = "Ошибка получения информации о заказе"
        await message.answer(response_text)


@dispatcher.callback_query_handler(lambda c: c.data.startswith('pay_'))
async def process_payment(callback_query: types.CallbackQuery):
    order_number = callback_query.data.split('_')[1]
    response = requests.get(f'http://127.0.0.1:8000/get_order_info/{order_number}/')
    if response.status_code == 200:
        order_info = response.json()
        if 'total' in order_info:
            price = types.LabeledPrice(label='Цена', amount=int(order_info['total']) * 100)
            await bot.send_invoice(
                chat_id=callback_query.message.chat.id,
                title='Покупка футболки GU',
                description='Оформление покупки',
                provider_token=config.PAYMENTS_TOKEN,
                currency='rub',
                photo_url='https://klike.net/uploads/posts/2020-06/1591254382_2.jpg',
                photo_width=416,
                photo_height=234,
                photo_size=416,
                is_flexible=False,
                prices=[price],
                start_parameter='order_buy',
                payload='test-invoice-payload'
            )
        else:
            await bot.send_message(callback_query.message.chat.id, f"Информация о заказе {order_number} недоступна.")
    else:
        await bot.send_message(callback_query.message.chat.id, "Ошибка получения информации о заказе")

def main():
    executor.start_polling(dispatcher, skip_updates=False)


if __name__ == '__main__':
    main()







