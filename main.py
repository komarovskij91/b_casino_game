import asyncio
import hashlib
import hmac
import json
import logging
import time
from typing import Optional
from urllib.parse import parse_qsl

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Info, Counter, Summary, make_asgi_app

import config
import models as model
from redis_aio import test_post, rega_new_user, test_while, chek_test, start_data_0, get_pay, chek_pay, \
user_data_chek, user_data_rega, my_prof


metrics_app = make_asgi_app()

# -----------------------------
# FastAPI app + CORS
# -----------------------------
app = FastAPI()

# пока максимально расслабленный CORS, можно потом сузить
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /metrics для Prometheus
app.mount("/metrics", metrics_app)


APP_METRIC_REQUEST_COUNT = Counter('app_requests_total', 'Info about requests', ['method', 'endpoint', 'status'])
APP_METRIC_REQUEST_LATENCY = Summary('app_requests_latency', 'Info about latency', ['method', 'endpoint', 'status'])

# -----------------------------
# Проверка подписи Telegram WebApp initData
# -----------------------------
def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Проверка подписи Telegram WebApp initData.
    Возвращает dict (без hash/signature), либо кидает ValueError.
    """
    # 1. Парсим query-string в dict (значения уже декодированы из URL)
    data = dict(parse_qsl(init_data, keep_blank_values=True))

    if "hash" not in data:
        raise ValueError("hash is missing in initData")

    received_hash = data.pop("hash")
    # signature в подписи НЕ участвует
    data.pop("signature", None)

    # 2. data_check_string: key=value\n, отсортировано по key
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items())
    )

    # 3. secret_key = HMAC_SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    # 4. calculated_hash = HMAC_SHA256(secret_key, data_check_string)
    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError(
            f"Invalid hash: calculated={calculated_hash}, received={received_hash}"
        )

    return data


def raise_response(req: dict, status_code=200, message=""):

    # if status_code in [400, 405]:
    #     logging.error(f"'status_code': {status_code}, 'message': {message}")
    # else:
    #     logging.info(f"'status_code': {status_code}, 'message': {message}")

    # post metrics for non-standard responses:
    APP_METRIC_REQUEST_COUNT.labels(req["method"], 'v1', status_code).inc()
    APP_METRIC_REQUEST_LATENCY.labels(req["method"], 'v1', status_code).observe(time.time()-req["call_started"])

    raise HTTPException(status_code=status_code, detail={"message": message})


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



# -----------------------------
# Фоновый таск при старте (chek_test)
# -----------------------------
@app.on_event("startup")
async def startup_event():
    return {"status": True, "mess": "startup on_event"}


# -----------------------------
# Простые эндпоинты
# -----------------------------
@app.get("/")
async def health_check():
    return "ok"


# чтобы не видеть 405 на GET /v3
@app.get("/v3")
async def v3_get():
    return {"status": "ok", "message": "use POST for API methods"}

# -----------------------------
# Основной эндпоинт для TMA
# -----------------------------
@app.post("/v3")
async def api_v3(request: model.Request):
    # print("Получен запрос:", request.model_dump())
    # print("request.qhc", request.qhc)

    call_started = 1

    req = {
        "method": request.method,  # типо пример myprof
        "call_started": call_started,
        "params": request.params,
        "qhc": request.qhc
    }

    # if req["qhc"] == "":
    #     print("postman")

    try:
        qq = parse_user_query(request.qhc, req)
        # print("дата от телеги")
        # print(qq)

        id_telega = qq["user"]["id"]
        language_code = qq["user"]["language_code"]

        # print(id_telega, request.method)
        # print(f"ответ распарсить")

    except Exception as ex:
        id_telega = 310410518
        print("ошибка1 qq = parse_user_query(request.qhc, req)")

    if request.method == "track_referral":

        print("Зашли через ссылку на игру!")
        referral_code = req["params"]["referral_code"]
        print(f"🎯 РЕФЕРАЛЬНЫЙ КОД ПОЛУЧЕН: {referral_code}")

        # Получаем ID пользователя из qhc
        parsed_data = parse_user_query(request.qhc, req)
        user_id = parsed_data["user"]["id"]

        print(f"👤 Пользователь ID: {user_id}")
        print(f"🔗 Реферальный код: {referral_code}")

        # Здесь можно сохранить в базу данных

        dd = user_data_chek(qq)
        dd_rega = user_data_rega(dd)

        data_reg = await rega_new_user(user_id, dd_rega)
        return data_reg



    # Стартовые параметры
    if request.method == "start_data":
        return await start_data_0()


    # запуск спина
    if request.method == "test_post":
        return await test_post(id_telega, req["params"]["spin"])



    # Платежи
    if request.method == "my_prof":
        return await my_prof(id_telega)

    if request.method == "chek_pay":
        return await chek_pay(req["params"]["payload"])



    return {"status": False, "mess": "err"}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
