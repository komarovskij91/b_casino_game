import logging
import json
# import motor.motor_asyncio
import uvicorn
from typing import Union

import threading
import hashlib
import hmac
from operator import itemgetter
from urllib.parse import parse_qsl



import config
import models as model

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware


from aiogram import Bot
bot = Bot(config.TG_BOT_TOKEN, parse_mode='html')



from prometheus_client import make_asgi_app, Info, Counter, Summary
import time


# то что я добавил
import json
import pymongo
import asyncio

# import motor.motor_asyncio
import motor.motor_asyncio

import time
import random
import inspect

# from test_f import my_profile

# сделдать ручную добычу каждый час или каждые 15 минут

from redis_aio import test_post, rega_new_user, test_while, chek_test, start_data_0

print("ok Start")


# Prometheus metrics:
APP_METRIC_INFO = Info('app_version', 'A version of the application')
APP_METRIC_INFO.info({'version': config.API_SERVICE_VERSION, 'buildhost': 'foo@bar'})

APP_METRIC_REQUEST_COUNT = Counter('app_requests_total', 'Info about requests', ['method', 'endpoint', 'status'])
APP_METRIC_REQUEST_LATENCY = Summary('app_requests_latency', 'Info about latency', ['method', 'endpoint', 'status'])

metrics_app = make_asgi_app()

####################################

# logging.basicConfig(format="{ 'time': '%(asctime)s', 'app': 'api_service', 'user': '%(name)s', 'log_level': '%(levelname)s', 'message': %(message)s }", level=logging.DEBUG)


# client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_URI)
# db = client.get_database(config.MONGO_DB)
# wallet_collection = db.get_collection("wallet")
#############################


app = FastAPI()

### Set ORIGIN CORS
origins = [
    "https://api.dev.vikbot.pro",
    "https://dev.vikbot.pro",
    "http://localhost:3000",
    "https://web.dev.vikbot.pro",
    "https://allows-shell-rd-stereo.trycloudflare.com",
    "https://catonback-production.up.railway.app"
]

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    # allow_methods=["*"],
    allow_headers=["*"],
)


#####################

# endpoint for prometheus metrics
app.mount("/metrics", metrics_app)

# logging.info(f"api_service version: {config.API_SERVICE_VERSION}")


# что-то для проверки ошибок
def raise_response(req: dict, status_code=200, message=""):

    # if status_code in [400, 405]:
    #     logging.error(f"'status_code': {status_code}, 'message': {message}")
    # else:
    #     logging.info(f"'status_code': {status_code}, 'message': {message}")

    # post metrics for non-standard responses:
    APP_METRIC_REQUEST_COUNT.labels(req["method"], 'v1', status_code).inc()
    APP_METRIC_REQUEST_LATENCY.labels(req["method"], 'v1', status_code).observe(time.time()-req["call_started"])

    raise HTTPException(status_code=status_code, detail={"message": message})


############################################################################################ мое



######################################
########### V1 #######################
# Only telegram autenticated request #
def parse_user_query(init_data: str, req):
    try:
        parsed_data = dict(parse_qsl(init_data))
        parsed_data['user'] = json.loads(parsed_data['user'])
        # мое

        #?
        # logged_ = parsed_data['auth_date']
        # if int(time.time()) - int(logged_) > int(config.AUTH_SESSION_ALIVE):
        #     # Request is expired. Need to relogin to webapp
        #     output = json.dumps({
        #         "message": "Your session has expired"
        #     })
        #     raise_response(req, 401, output)


    except ValueError:
        # Init data is not a valid query string
        output = json.dumps({
            "message": "Init data is not a valid query string"
        })
        raise_response(req, 400, output)

    if "hash" not in parsed_data:
        # Hash is not present in init data
        output = json.dumps({
            "message": "Hash is not present in init data"
        })
        raise_response(req, 401, output)

    return parsed_data

def check_webapp_signature(parsed_data: dict, token=config.TG_BOT_TOKEN) -> bool:
    """
    Check incoming WebApp init data signature

    Source: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app

    :param token:
    :param init_data:
    :return:
    """
    # try:
    #     parsed_data = dict(parse_qsl(init_data))
    # except ValueError:
    #     # Init data is not a valid query string
    #     return False
    # if "hash" not in parsed_data:
    #     # Hash is not present in init data
    #     return False

    hash_ = parsed_data.pop('hash')
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0))
    )
    secret_key = hmac.new(
        key=b"WebAppData", msg=token.encode(), digestmod=hashlib.sha256
    )
    calculated_hash = hmac.new(
        key=secret_key.digest(), msg=data_check_string.encode(), digestmod=hashlib.sha256
    ).hexdigest()


    return calculated_hash == hash_


# Часть которая слушает. Она нужна одна и все

@app.get("/")
async def health_check():
    return "ok"



@app.get("/reward")
async def reward_handler(userid: str, request: Request):
    """
    Эндпоинт, который вызывается Adsgram при событии реворда.
    Пример запроса: https://test.adsgram.ai/reward?userid=310410518
    """
    # Логируем для наглядности
    print(f"Получен запрос на реворд от пользователя {userid}")
    print(f"IP отправителя: {request.client.host}")

    # Тут можно добавить свою бизнес-логику:
    # например, начисление награды пользователю
    # await add_reward_to_user(userid)


    return {"status": "ok", "userid": userid}



@app.post("/v3")
async def api_v2(request: model.Request):
    # print("Получен запрос:", request.model_dump())
    # print("request.qhc", request.qhc)


    call_started = 1

    req = {
        "method": request.method,  # типо пример myprof
        "call_started": call_started,
        "params": request.params,
        "qhc": request.qhc
    }

    if request.method == "test1":

        return {
            "status": "success",
            "method": request.method,
            "params": request.params,
            "qhc": request.qhc
        }

    if request.method == "test_post":
        return await test_post(spin=req["params"]["spin"])

    if request.method == "start_data":
        return start_data_0()



    return {"status": f"ne ok {req}"}



@app.post("/v2")
async def api_v2(request: model.Request):
    # print("Получен запрос:", request.model_dump())
    # print("request.qhc", request.qhc)


    call_started = 1

    req = {
        "method": request.method,  # типо пример myprof
        "call_started": call_started,
        "params": request.params,
        "qhc": request.qhc
    }


    if req["qhc"] == "":
        print("postman")

    try:
        qq = parse_user_query(request.qhc, req)
        # print("дата от телеги\n")
        # print(qq)

        id_telega = qq["user"]["id"]
        language_code = qq["user"]["language_code"]

        # print(id_telega, request.method)
        print(f"ответ распарсить")

    except Exception as ex:
        id_telega = 310410518
        print("ошибка1")



    # Рега через бота
    if request.method == "telega_rega_bot":
        print("рега через бота")
        await rega_new_user(req["params"]["id_telega"], req["params"]["data"])
        return "ok"


    # все норм
    if req["qhc"] != "":
        qq = parse_user_query(request.qhc, req)
        id_telega = qq["user"]["id"]


    if req["qhc"] == "":
        print("Пустой QHC")
        id_telega = 310410518

    # if req["qhc"] == "":
    #     print("test id_telega = ")
    #     id_telega = 310410518
    #
    #     return {
    #         "status": "success",
    #         "message": "test id_telega = "
    #     }

    if request.method == "test1":

        return {
            "status": "success",
            "method": request.method,
            "params": request.params,
            "qhc": request.qhc
        }

    if request.method == "telega_rega":
        inf_ = {
              'user': {
                'id': 310410518,
                'first_name': 'Егор',
                'last_name': 'Комаровский',
                'username': 'komarovskij91',
                'language_code': 'ru',
                'is_premium': True,
                'allows_write_to_pm': True,
                'photo_url': 'https://t.me/i/userpic/320/xzTDFMn9vsJoCFHvD2mxR1C1T_9dvx0nidKrjo0lqFQ.svg'
              },
              'chat_instance': '-5254413471388297401',
              'chat_type': 'supergroup',
              'auth_date': '1752155419',
              'signature': '7o-Hxcex55KA445MIVgHbmcuxfwDvsNNeuDf4UhY2KzDeDl6Bel-n1-nl4PrG2yE4bI-UWRgwPTyYG-mbI6kCw',
              'hash': 'c7ed572808d1f2aa15ee7e26587bf9f7f960392a6d18f95823def59bcc2271cf'
            }

        inf_0 = {
              'query_id': 'AAHr_d9IAAAAAOv930ivD80T',
              'user': {
                'id': 1222639083,
                'first_name': '?',
                'last_name': '',
                'language_code': 'ru',
                'is_premium': True,
                'allows_write_to_pm': True,
                'photo_url': 'https://t.me/i/userpic/320/klc4NzIcsQlx10TkV0IduBKdmBr-K6LmS6-xBax0scw.svg'
              },
              'auth_date': '1753025980',
              'signature': 'q7QTRzZwYA3HHlUL5hqShA127Y-rgsBopA4t9eooc2TiYx69XkSKKNCCKLLbH21w8L1VgQeVP7yghv6kgzD0Ag',
              'hash': 'c1bd6e8f75af30b104f94aa98ac5d15afe0173d62381a6d24f03c7954c0ca6c2'
            }

        print("telega_rega")
        await rega_new_user(req["params"]["id_telega"], req["params"]["data"])
        return "ok"

    if request.method == "my_prof":

        # print("my_prof", id_telega)
        if req["qhc"] != "":
            data = {
                "username": None,
                "first_name": qq["user"]["first_name"],
                'last_name': qq["user"]["last_name"],
                'language_code': qq["user"]["language_code"],
                "ref": ""
            }

            if "username" in qq["user"]:
                data["username"] = qq["user"]["username"]
            else:
                data["username"] == ""

            if "is_premium" in qq["user"]:
                data["prem"] = qq["user"]["is_premium"]
            else:
                data["prem"] = None

        # return await my_prof(id_telega, data)




    return {"status": "ne ok"}


# Функция для запуска Uvicorn
def run_uvicorn():
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Функция для запуска асинхронной функции в отдельном потоке
def run_async_function():
    # Запуск
    asyncio.run(chek_test())


# Основная функция
def go_main():
    # Запускаем сервер Uvicorn в отдельном потоке
    uvicorn_thread = threading.Thread(target=run_uvicorn, daemon=True)
    uvicorn_thread.start()

    # Запускаем асинхронную функцию в основном потоке
    run_async_function()


######################################

if __name__ == "__main__":

    # uvicorn.run(app, host="0.0.0.0", port=8000)
    go_main()