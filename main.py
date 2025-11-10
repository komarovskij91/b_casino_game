import logging
import json
import threading
import hashlib
import hmac
from urllib.parse import parse_qsl

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app, Info, Counter, Summary

import config
import models as model
from redis_aio import test_post, rega_new_user, test_while, chek_test, start_data_0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
APP_METRIC_INFO = Info('app_version', 'A version of the application')
APP_METRIC_INFO.info({'version': config.API_SERVICE_VERSION, 'buildhost': 'api'})
APP_METRIC_REQUEST_COUNT = Counter(
    'app_requests_total',
    'Info about requests',
    ['method', 'endpoint', 'status'],
)
APP_METRIC_REQUEST_LATENCY = Summary(
    'app_requests_latency',
    'Info about latency',
    ['method', 'endpoint', 'status'],
)

metrics_app = make_asgi_app()

app = FastAPI()

# CORS
origins = [
    "https://api.dev.vikbot.pro",
    "https://dev.vikbot.pro",
    "http://localhost:3000",
    "https://web.dev.vikbot.pro",
    "https://allows-shell-rd-stereo.trycloudflare.com",
    "https://catonback-production.up.railway.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /metrics для Prometheus
app.mount("/metrics", metrics_app)


def raise_response(req: dict, status_code: int = 200, message: str = "") -> dict:
    return {
        "statusCode": status_code,
        "body": {
            "message": message,
            "request": req,
        },
    }


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Проверка подписи Telegram WebApp initData.
    Возвращает dict без полей `hash` и `signature`,
    если подпись корректна, иначе кидает ValueError.
    """

    # Парсим query-string (значения уже декодированы из URL)
    data = dict(parse_qsl(init_data, keep_blank_values=True))

    if "hash" not in data:
        raise ValueError("hash is missing in initData")

    received_hash = data.pop("hash")
    # signature в подписи НЕ участвует
    data.pop("signature", None)

    # Формируем data_check_string
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items())
    )

    # Секретный ключ: HMAC_SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    # Хэш
    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError(
            f"Invalid hash: calculated={calculated_hash}, received={received_hash}"
        )

    return data


@app.get("/")
async def health_check():
    return "ok"


@app.get("/reward")
async def reward_handler(userid: str, request: Request):
    logger.info("Reward callback for user %s from %s", userid, request.client.host)
    # Тут твоя логика начисления реворда
    return {"status": "ok", "userid": userid}


@app.post("/v3")
async def api_v3(request: model.Request):
    logger.debug("Received request method: %s", request.method)

    # Методы, которые не требуют проверки подписи
    public_methods = {"start_data", "test_post"}

    parsed_data_for_response = None
    user_id = None

    # Проверяем подпись initData для непубличных методов
    if request.method not in public_methods:
        if not request.qhc or not request.qhc.strip():
            logger.error("qhc is empty")
            raise HTTPException(status_code=400, detail="qhc (initData) is required")

        logger.debug("Received qhc length: %s", len(request.qhc))
        logger.debug("qhc preview: %s...", request.qhc[:100])

        try:
            data = validate_telegram_init_data(request.qhc, config.TG_BOT_TOKEN)
        except ValueError as e:
            logger.error("Invalid signature: %s", e)
            raise HTTPException(status_code=401, detail="Invalid signature")

        # В initData поле user приходит как JSON-строка
        user_raw = data.get("user")
        try:
            user = json.loads(user_raw) if isinstance(user_raw, str) else user_raw
        except json.JSONDecodeError:
            logger.exception("Cannot decode user JSON from initData")
            raise HTTPException(status_code=400, detail="Invalid user field in initData")

        data["user"] = user
        parsed_data_for_response = data
        user_id = user.get("id")
        logger.debug("Signature check passed, user_id: %s", user_id)

    call_started = 1
    req = {
        "method": request.method,
        "call_started": call_started,
        "params": request.params,
        "qhc": request.qhc,
        "user": parsed_data_for_response.get("user") if parsed_data_for_response else None,
    }

    # ---------- Публичные методы ----------
    if request.method == "test_post":
        # пример: params = {"spin": ...}
        return await test_post(spin=req["params"]["spin"])

    if request.method == "start_data":
        return await start_data_0()

    # ---------- Служебный метод для отладки initData ----------
    if request.method == "test_qhc":
        logger.info("метод test_qhc")
        return {
            "ok": True,
            "req": req,
            "parsed_init_data": parsed_data_for_response,
        }

    # ---------- Пример метода регистрации через бота ----------
    if request.method == "telega_rega_bot":
        await rega_new_user(req["params"]["id_telega"], req["params"]["data"])
        return {"status": "ok"}

    # ---------- Фолбэк для неизвестных методов ----------
    return {"status": "ne ok", "req": req}


def run_uvicorn():
    uvicorn.run(app, host="0.0.0.0", port=8000)


def go_main():
    # Для Railway достаточно просто запустить uvicorn
    run_uvicorn()


if __name__ == "__main__":
    go_main()
