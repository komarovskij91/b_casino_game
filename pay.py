import config
from aiogram.types import LabeledPrice
import json

from aiogram import Bot
bot = Bot(config.TG_BOT_TOKEN, parse_mode='html')

# from redis_aio import reupdata


import settings
import time
import random



# рандомный айди
def idrr0():
    rr = "AEIOUYBCDFGHJKLMNPQRSTVWXZaeiouybcdfghjklmnpqrstvwxz"
    return f"{int(time.time())}{random.choice(rr)}{random.choice(rr)}{random.choice(rr)}{random.choice(rr)}{random.choice(rr)}"



async def get_pay_up_slot(id_telega, ):
    up_one_slot = "up_one_slot"

    # box - box_cat_1

    amount = settings.shop[up_one_slot]["amount"]
    title = settings.shop[up_one_slot]["title"]["ru"]
    description = settings.shop[up_one_slot]["description"]["ru"]

    # разобрать что хотят купить в BOX
    id_pay_my = f"id_pay_my:{idrr0()}"

    try:

        prices = [LabeledPrice(label='XTR', amount=int(amount))]

        # Create invoice
        invoice_link = await bot.create_invoice_link(
            title=title,  # название продукта - бокс
            description=description,  # полное нахвание продукта
            provider_token='',
            currency='XTR',
            prices=prices,
            payload='stars-payment-payload'
        )

        print(invoice_link)  # ссылка на оплату

        pay_data = {
            "id_pay_my": id_pay_my,
            "id_telega": id_telega,
            "typ": up_one_slot,  # что купили
            "invoice_link": invoice_link,
            "amount": amount,
            "status_pay": ""
        }
        print("pay_data", pay_data)

        # Создали себе запись с - id_pay_my
        # await reupdata(id_pay_my, pay_data)

        return {
            "status": True,
            "payment_url": invoice_link,
            "id_pay_my": id_pay_my
        }

    except Exception as e:

        print(e)

        return {
            "status": False,
            "payment_url": "",
            "err": e
        }


async def get_pay_up_slot_1(id_telega, up_one_slot: str):
    """
    Создает invoice_link и возвращает данные для оплаты.
    id_telega — Telegram ID пользователя
    up_one_slot — ключ товара в settings.shop
    """

    # достаем параметры товара
    amount = settings.shop[up_one_slot]["amount"]
    title = settings.shop[up_one_slot]["title"]["ru"]
    description = settings.shop[up_one_slot]["description"]["ru"]

    # генерим свой id заказа
    id_pay_my = f"id_pay_my:{idrr0()}"

    try:
        prices = [LabeledPrice(label='XTR', amount=int(amount))]

        # payload — твой идентификатор заказа
        payload = json.dumps({
            "id_pay_my": id_pay_my,
            "sku": up_one_slot
        })

        # Create invoice
        invoice_link = await bot.create_invoice_link(
            title=title,
            description=description,
            provider_token='',  # для XTR пусто
            currency='XTR',
            prices=prices,
            payload=payload
        )

        # данные для хранения в базе
        pay_data = {
            "id_pay_my": id_pay_my,
            "id_telega": id_telega,
            "typ": up_one_slot,
            "invoice_link": invoice_link,
            "amount": amount,
            "status_pay": "PENDING",   # изначально ждем оплату
            "charge_id": None          # появится при successful_payment
        }

        print("pay_data", pay_data)

        # Сохрани запись в Redis/БД
        # await reupdata(id_pay_my, pay_data)

        return {
            "status": True,
            "payment_url": invoice_link,
            "id_pay_my": id_pay_my
        }

    except Exception as e:
        print("Ошибка при создании инвойса:", e)
        return {
            "status": False,
            "payment_url": "",
            "err": str(e)
        }


