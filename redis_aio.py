import redis.asyncio as aioredis

import json
import motor.motor_asyncio
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple


from datetime import datetime, timedelta
import random
import inspect
import re

import aiohttp
from gen_top import build_top_snapshot, compare_leagues
import requests

from collections import Counter

from aiogram import Bot
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, PreCheckoutQuery, ContentType, LabeledPrice
import config
bot = Bot(config.TG_BOT_TOKEN, parse_mode='html')

##### Файлы
import settings
import langs
from test import gen_item

import os
from func import power_chek, get_strongest_style, pick_nearby_rival, hype_phrase, lose_phrase, get_damage_bonus
import test
import json
import math
import random
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


from pay import get_pay_up_slot



# from gen_spin import generate_plinko_scenario, start_data
from gen_spin_2 import generate_plinko_scenario, start_data


redis_url = os.getenv("REDIS_URL")
if not redis_url:
    # Строка подключения
    redis_url = "redis://default:jkPaytVZkLjHBynAueZtgJHNSKTYYVYX@switchback.proxy.rlwy.net:42148"
    print("конект через публик")
else:
    print("Коннект через приватку к редис")

# Создаем объект Redis
client_redis = aioredis.from_url(redis_url)



# рандомный айди
def idrr0():
    rr = "AEIOUYBCDFGHJKLMNPQRSTVWXZaeiouybcdfghjklmnpqrstvwxz"
    return f"{int(time.time())}{random.choice(rr)}{random.choice(rr)}{random.choice(rr)}{random.choice(rr)}{random.choice(rr)}"






# запрос на новые подарки
async def post_request_get_gift(id_telega, user_name):
    url = "https://fastapigift-production.up.railway.app/v1"
    print(f"Отправили запрос на получение подарков для {id_telega}, {user_name}")

    try:
        id_telega_int = int(id_telega)
    except ValueError:
        print("Ошибка: id_telega должен быть числом")
        return None

    payload = {
        "method": "test2",
        "call_started": "call_started",
        "params": {
            "username": f"{user_name}",
            "id_telega": f"{id_telega}"
        },
        "qhc": ""
    }


    print("Отправка запроса на:", url)
    print("Данные запроса:", payload)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, ssl=False) as response:  # ← ssl=False отключает проверку
                if response.status == 200:
                    data = await response.json()
                    print("Успешный ответ:", data)
                    return data
                else:
                    print(f"Ошибка: HTTP {response.status}")
                    return None
    except Exception as e:
        print("Ошибка при запросе:", e)
        return None


async def reupdata(key, data):
    await client_redis.set(
        key,
        json.dumps(data, ensure_ascii=False)  # кириллица сохраняется читаемо
    )

# взять с базы что-то
async def redata(key):

    try:
        # data = await json.loads(client_redis.get(key).decode())
        data = await client_redis.get(key)

        data = json.loads(data.decode())
    except Exception as ex:
        # print(f"reupdata - , key {key}", ex)
        data = None
    return data


async def del_key(id_key):
    dd = await client_redis.delete(id_key)
    print(dd)



# дата реги для тереншена
async def data_reg(id_telega):
    # # Получение всех ID пользователей из "коллекции"
    # user_ids = await client_redis.smembers(f"data_reg:{today_date}")  # Вернет set
    # all_users = []
    # # Итерация по всем пользователям
    # for user_id in user_ids:
    #     # user_data = client.get(f"user:{user_id.decode()}")
    #     all_users.append(json.loads(user_id))  # Декодируем JSON

    today_date = time.strftime("%Y-%m-%d", time.localtime(time.time()))
    await client_redis.sadd(f"data_reg:{today_date}", id_telega)


# Создать нового человека
async def rega_new_user(id_telegram, data=None):

    if data == {} or None:
        data = {
            "username": None,
            "first_name": None,
            'last_name': None,
            'language_code': "en",
            "ref": None
        }

    if int(id_telegram) > 0:

        user = await redata(f"user:{id_telegram}")

        if user != None:
            print(f"есть уже {id_telegram}")

            return user

        else:

            nuser = 0
            nuser = settings.new_user.copy()

            nuser["id_telega"] = id_telegram
            nuser["data_reg"] = time.time()

            if "first_name" in data:
                nuser["first_name"] = data["first_name"]

            else:
                nuser["first_name"] = None

            if "last_name" in data:
                nuser["last_name"] = data["last_name"]
            else:
                nuser["last_name"] = None

            if "username" in data:
                nuser["username"] = data["username"]
            else:
                nuser["username"] = None

            if "language_code" in data:
                nuser["lang"] = data["language_code"]
            else:
                nuser["lang"] = "en"

            if "is_premium" in data:
                nuser["prem"] = data["is_premium"]
            else:
                nuser["prem"] = None

            if "ref" in data:
                nuser["ref"] = data["ref"]
            else:
                nuser["ref"] = None

            # проверка на реф

            # создали персанажа
            # вставить
            await reupdata(f"user:{id_telegram}", nuser)

            print("ok _ Зарегали нового человека", id_telegram, data)

            user = await redata(f"user:{id_telegram}")

            mess = "ЕЕЕ"
            try:
                await bot.send_message(id_telegram, mess)
            except:
                print("не смогли отправить сообщение")


            return user



# Проверка новых параметров
async def chek_new_param(id_telegram, user_data):

    for new_param in settings.new_user:
        if new_param not in user_data:
            user_data[new_param] = settings.new_user[new_param]
            print(f"добавили для {id_telegram} - {new_param}", settings.new_user[new_param])

    await reupdata(f"user:{id_telegram}", user_data)

    return user_data




async def update_login_streak(id_telega):

    """
    Обновляет дневной стрик посещений игрока.
    Если день тот же — ничего не меняем.
    Если вчера — +1 к стрику.
    Если пропущено >=1 дня — сброс до 1.
    """

    key = f"user:{id_telega}"
    user = await redata(key)

    now_ts = time.time()
    now_date = datetime.utcfromtimestamp(now_ts).date()
    last_ts = float(user.get("day_time") or 0)

    # Первый вход
    if last_ts <= 0:
        user["day"] = 1
        user["day_time"] = now_ts
        await reupdata(key, user)
        return {"status": "first_visit"}

    last_date = datetime.utcfromtimestamp(last_ts).date()
    delta_days = (now_date - last_date).days

    if delta_days == 0:
        # Тот же день
        user["day_time"] = now_ts
        status = "same_day"
    elif delta_days == 1:
        # Заход подряд
        user["day"] += 1

        user["day_time"] = now_ts
        status = "continued"

    else:
        # Пропуск
        user["day"] = 1
        user["day_time"] = now_ts
        status = "reset"

    await reupdata(key, user)

    # reset и first_visit - показываем табличку с инфой о первом дне
    # continued - Заход подряд - показываем сколько чего получает


    return {"status": status}




def seconds_until_new_year() -> int:
    # Текущая метка времени
    now = time.time()
    # Целевая дата: 1 января 2026, 00:00:00
    new_year = datetime(2026, 1, 1, 0, 0, 0).timestamp()
    # Разница в секундах
    return int(new_year - now)

################################################################################################
async def chek_test():
    pass

async def test_while():
    # print("запустили test_while")
    while True:
        # print(f"ok")
        await asyncio.sleep(5)


async def chek_test():
    # Параллельный запуск двух асинхронных функций
    await asyncio.gather(
        test_while() # сюда потом еще подкл функции ,
        # auto_farm()
    )


# для получения с фронта
def user_data_chek(data):

    dd = {}

    if "id" in data["user"]:
        dd["id"] = data["user"]["id"]

    if "first_name" in data["user"]:
        dd["first_name"] = data["user"]["first_name"]

    if "last_name" in data["user"]:
        dd["last_name"] = data["user"]["last_name"]

    if "username" in data["user"]:
        dd["username"] = data["user"]["username"]

    if "language_code" in data["user"]:
        dd["language_code"] = data["user"]["language_code"]

    if "is_premium" in data["user"]:
        dd["is_premium"] = data["user"]["is_premium"]

    if "id" in data["user"]:
        dd["id"] = data["user"]["id"]

    if "start_param" in data:
        dd["ref"] = data["start_param"]

    return dd


def user_data_rega(data):

    dd = {}
    if "id" in data:
        dd["id"] = data["id"]

    if "first_name" in data:
        dd["first_name"] = data["first_name"]

    if "last_name" in data:
        dd["last_name"] = data["last_name"]

    if "last_name" in data:
        dd["last_name"] = data["last_name"]

    if "username" in data:
        dd["username"] = data["username"]

    if "language_code" in data:
        dd["language_code"] = data["language_code"]

    if "is_premium" in data:
        dd["is_premium"] = data["is_premium"]

    if "ref" in data:
        dd["ref"] = data["ref"]

    return dd





###########

async def get_star_transactions(limit=50, offset=0):
    """Сырой ответ Telegram Bot API getStarTransactions"""
    resp = await bot.request("getStarTransactions", {"limit": limit, "offset": offset})
    return resp or {}


async def peek_star_transactions(limit=20, offset=0):
    """Удобный вид для глаз — только основные поля"""
    resp = await get_star_transactions(limit, offset)
    out = []
    for tx in resp.get("transactions", []):
        out.append({
            "id": tx.get("id"),
            "amount": tx.get("amount"),
            "date": tx.get("date"),
            "readable_time": __import__("time").strftime("%Y-%m-%d %H:%M:%S", __import__("time").localtime(tx.get("date") or 0)),
            "is_income": tx.get("is_income"),
            "direction": tx.get("direction"),
            "source": tx.get("source") or tx.get("title") or tx.get("provider"),
        })

    dd = {
        "count": len(out),
        "list": out
    }

    return dd


# Выставить счет
async def get_pay(id_telega, many):

    shop = {
        "ru": {
            "title": "Пополнить баланс",
            "description": f"Пополнить баланс на {many} Stars"
        },
        "en": {
            "title": "Top up balance",
            "description": f"Top up your balance with {many} Stars"
        }
    }

    # user = await redata(f"user:{id_telega}")
    # lang = user["lang"]

    lang = "ru"
    title = shop[lang]["title"]
    description = shop[lang]["description"]

    # разобрать что хотят купить в BOX
    id_pay_my = f"id_pay_my:{id_telega}:{idrr0()}"

    try:

        prices = [LabeledPrice(label='XTR', amount=int(many))]

        # Create invoice
        invoice_link = await bot.create_invoice_link(
            title=title,  # название продукта - бокс
            description=description,  # полное нахвание продукта
            provider_token='',
            currency='XTR',
            prices=prices,
            payload=id_pay_my
        )

        # print(invoice_link)  # ссылка на оплату

        # форматируем в нужный вид
        formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        pay_data = {
            "id_pay_my": id_pay_my,
            "id_telega": id_telega,
            "typ": "typ",  # что купили
            "invoice_link": invoice_link,
            "amount": many,
            "status_pay": "",
            "payload": id_pay_my,
            "time": f'{datetime.now().strftime("%Y-%m-%d %H:%M")}',
        }
        print("pay_data", pay_data)

        # Создали себе запись с - id_pay_my
        await reupdata(id_pay_my, pay_data)

        return {
            "status": True,
            "payment_url": invoice_link,
            "payload": id_pay_my
        }

    except Exception as e:

        print(e)

        return {
            "status": False,
            "payment_url": "",
            "err": e
        }


# проверка платежа
async def chek_pay(id_pay_my):
    def extract_user_id(key: str) -> int:
        """
        Из строки вида 'id_pay_my:310410518:1759164859kHaor'
        возвращает 310410518 как int.
        """
        parts = key.split(":")
        if len(parts) >= 3:
            return int(parts[1])  # второй элемент — user_id
        raise ValueError("Неверный формат ключа")

    data = await redata(id_pay_my)
    id_telegram = extract_user_id(id_pay_my)
    # print("id_telegram", id_telegram)
    # print("data", data)

    typ = data["typ"]

    # проверяем полачен ли платеж
    dd_status_pay = await stars_payments(id_pay_my)
    if dd_status_pay["status"] == True:

        # выдаем то что надо выдать
        user = await redata(f"user:{id_telegram}")
        user["stars"] += dd_status_pay["amount"]
        await reupdata(f"user:{id_telegram}", user)

        dd = {
            "title": {
                "ru": "Успех",
                "en": "Success"
            },
            "description": {
                "ru": f"Ваш баланс успешно пополнен на {dd_status_pay['amount']} Starts",
                "en": f"Your balance has been successfully topped up with {dd_status_pay['amount']} Starts"
            }

        }

        print(dd)

        return dd

    if dd_status_pay["status"] == "pay":
        dd = {
            "title": {
                "ru": "Уже был оплачен!",
                "en": "Already paid"
            },
            "description": {
                "ru": f"Счет уже был оплачен ранее",
                "en": f"The bill has already been paid earlier."
            }

        }

        # print(dd)
        return dd

    if dd_status_pay["status"] == False:
        dd = {
            "title": {
                "ru": "Не оплачен",
                "en": "Not paid"
            },
            "description": {
                "ru": f"Счет на оплачен",
                "en": f"The invoice has been paid."
            }

        }

        # print(dd)
        return dd


    dd = {
        "status": "oooo =("
    }

    return dd


# дать то что надо после покупки
async def purchase(id_telegram, typ):


    user = await redata(f"user:{id_telegram}")

    dd = {
        "status": "",
        "mess": "",
        "typ": ""
    }

    if typ == "up_one_slot":

        # print("start", user["lvl_grade"])
        try:
            idx = settings.ll.index(user["lvl_grade"])
        except ValueError:
            return False  # если такого слова нет
        if idx + 1 < len(settings.ll):
            user["lvl_grade"] = settings.ll[idx + 1]
            # print("fin", user["lvl_grade"])
            await reupdata(f"user:{id_telegram}", user)

            dd["status"] = True
            dd["typ"] = typ
            dd["mess"] = "Прокачали слот на +1"
            dd["now"] = user["lvl_grade"]

            return dd

        return False  # если это был последний

    if typ == "up_liga_slot":
        # print("start", user["lvl_grade"])

        # разбираем, например tree_3 -> league=tree, tier=3
        league, tier = user["lvl_grade"].split("_")

        # если лига не найдена — вернём как есть
        if league not in settings.LEAGUE_SEQUENCE:
            return user["lvl_grade"]
        idx = settings.LEAGUE_SEQUENCE.index(league)

        # если diamond — остаёмся на diamond
        if idx == len(settings.LEAGUE_SEQUENCE) - 1:
            return user["lvl_grade"]
        next_league = settings.LEAGUE_SEQUENCE[idx + 1]

        user["lvl_grade"] = f"{next_league}_{tier}"
        # print("fin", user["lvl_grade"])
        await reupdata(f"user:{id_telegram}", user)

        dd["status"] = True
        dd["typ"] = typ
        dd["mess"] = "Прокачали все слоты на +1"
        dd["now"] = f"{next_league}_{tier}"


        return dd

    if typ == "change_slot":

        user_pay_id_gift = await redata(f"user_pay_id_gift:{id_telegram}")

        id_gift_ = user_pay_id_gift["id_gift"]
        new_style_ = user_pay_id_gift["new_style"]

        gift = await redata(id_gift_)

        if new_style_ in settings.user_style:
            gift["new_style"] = new_style_
            await reupdata(id_gift_, gift)
            user = await redata(f"user:{id_telegram}")
            for ii in settings.user_slot:
                if user[ii]:
                    if id_gift_ == user[ii]["id"]:
                        user[ii] = None
            await reupdata(f"user:{id_telegram}", user)

            # print(ff)

            dd["status"] = True
            dd["typ"] = typ
            dd["mess"] = "Дали новую стихию"
            dd["now"] = new_style_

            return dd

    if typ == "skin":
        user = await redata(f"user:{id_telegram}")
        user["super_pepe"] = True
        await reupdata(f"user:{id_telegram}", user)

        dd["status"] = True
        dd["typ"] = typ
        dd["mess"] = "Super PEPE"
        dd["now"] = "Super PEPE"

        return dd

    if typ == "off_advertising":
        user = await redata(f"user:{id_telegram}")
        user["ads_off"] = True
        await reupdata(f"user:{id_telegram}", user)

        dd["status"] = True
        dd["typ"] = typ
        dd["mess"] = "Off ADS"
        dd["now"] = "Off ADS"

        return dd


    return False


async def stars_payments(payload=None):
    limit_offset = await redata(f"limit_offset")
    if limit_offset == None:
        limit_offset = {
            "limit": 20,
            "offset": 0
        }
        await reupdata("limit_offset", limit_offset)
        limit_offset = await redata(f"limit_offset")


    # начинаем с 0
    limit = limit_offset["limit"]  # Сколько на странице
    offset = limit_offset["offset"]  # Страница

    data_pay = await redata(payload)
    print(data_pay)

    if data_pay["status_pay"] == "":
        pass

    if data_pay["status_pay"] == "pay":

        dd = {
            "status": "pay",
            "mess": "уже был Оплачен"
        }
        # print(dd)
        return dd


    mm = 0

    list_pay = []

    while True:

        dd = await peek_star_transactions(limit, offset)
        new_data = dd
        # print(dd["count"])
        mm += dd["count"]

        # просто просмотр данных
        for i in dd["list"]:
            # print(i["readable_time"], i["source"]["invoice_payload"])
            list_pay.append(i["source"]["invoice_payload"])

        # если ранво 0 - то смотрим предыдущую папку и там ищием платеж
        if dd["count"] == 0:
            # print("конец")
            # print(f"всего {mm}, последний limit {limit} offset {offset}")
            break


        if dd["count"] >= limit:
            offset += limit
            # print("еще")
            await asyncio.sleep(0)

        else:

            # print(f"limit {limit}")
            # print(f"offset {offset}")

            limit_offset["limit"] = limit
            limit_offset["offset"] = offset
            await reupdata("limit_offset", limit_offset)

            # print("конец")
            # print(f"всего {mm}, последний limit {limit} offset {offset}")
            break

    if payload in list_pay:
        # print(True)
        data_pay["status_pay"] = "pay"
        await reupdata(payload, data_pay)

        dd = {
            "id_telega": data_pay["id_telega"],
            "amount": data_pay["amount"],
            "status": True,
            "mess": "оплатил - можно выдать"
        }
        # print(dd)
        return dd

    else:
        dd = {
            "status": False,
            "mess": "не нашли счет - не смогли проверить"
        }
        # print(dd)
        return dd



# ---------- УНИВЕРСАЛЬНЫЙ СБОР ДАННЫХ ИЗ REDIS ----------
async def fetch_all_2(pattern: str, batch_size: int = 100) -> List[Dict[str, Any]]:
    cursor = 0
    keys: List[str] = []
    while True:
        cursor, batch = await client_redis.scan(cursor=cursor, match=pattern, count=batch_size)
        for k in batch:
            keys.append(k.decode("utf-8", errors="ignore") if isinstance(k, (bytes, bytearray)) else k)
        if cursor == 0:
            break

    all_rows: List[Dict[str, Any]] = []
    for i in range(0, len(keys), batch_size):
        chunk = keys[i:i + batch_size]
        tasks = [redata(k) for k in chunk]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                # можно логировать r
                continue
            if isinstance(r, dict):
                all_rows.append(r)
    return all_rows




# запуск спина
async def test_post(id_telega, spin):
    user = await redata(f"user:{id_telega}")
    data_spin = generate_plinko_scenario(spin)
    win_spin = data_spin["result"]["win_amount"]
    user["stars"] -= spin
    user["stars"] += win_spin
    user["stavka"] = spin
    await reupdata(f"user:{id_telega}", user)

    return data_spin




async def start_data_0():
    dd = start_data()
    return dd



async def pool_spin():
    pass




async def my_prof(id_telegram):
    user = await redata(f"user:{id_telegram}")
    # print(user)

    await chek_new_param(id_telegram, user)

    dd = {
        "balans": user["stars"],
        "stavka": user["stavka"]
    }
    print(dd)
    return dd



async def plus_balans(id_telegram):
    user = await redata(f"user:{id_telegram}")

    dd = {
        "list_balans": [1, 50, 100, 500, 1000, 5000],
        "dubl_bonus": True,
        "mess_bonus": "Бонус на первый Депозит",
    }


    return dd



async def ttt():
    id_lera = 577753618
    id_nik = 563356818
    id_telegram = 310410518  # мой
    id_sasha = 980627987
    id_andr = 123857224
    my_seve = 8413154647  # Егорка Комар
    id_afon = 433688884
    sacha = 980627987

    id_evgeniyshow = 194092787
    # dd = await test_post(10)
    # print(dd)

    # pay_data {'id_pay_my': 'id_pay_my:310410518:1762961604NOQbR', 'id_telega': 310410518, 'typ': 'typ', 'invoice_link': 'https://t.me/$axlYEwLqqEgSEAAAo12rbstsM5c', 'amount': 1, 'status_pay': '', 'payload': 'id_pay_my:310410518:1762961604NOQbR', 'time': '2025-11-12 18:33'}
    # dd = generate_plinko_scenario(10)
    # print(dd)
    # print(user)

    # await get_pay(id_telegram, 1)

    # dd = await chek_pay('id_pay_my:310410518:1762961604NOQbR')
    # print(dd)
    # await rega_new_user(id_telegram)

    # await my_prof(id_telegram)

    pass



# asyncio.get_event_loop().run_until_complete(ttt())

