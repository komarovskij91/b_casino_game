import logging
import json
import hashlib
import hmac
from urllib.parse import parse_qsl

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app, Info, Counter, Summary

import config
import models as model
from redis_aio import test_post, rega_new_user, chek_test, start_data_0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# Prometheus metrics
# =========================
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

# =========================
# FastAPI app
# =========================
app = FastAPI()

# CORS — делаем максимально дружелюбно, чтобы не было 400 на OPTIONS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # если хочешь — можешь потом сузить до своих доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /metrics для Prometheus
app.mount("/metrics", metrics_app)


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Проверка подписи Telegram WebApp initData.
    Возвращает dict (без hash/signature), либо кидает ValueError.
    """
    # Парсим query-string в dict
    data = dict(parse_qsl(init_data, keep_blank_values=True))

    if "hash" not in data:
        raise ValueError("hash is missing in initData")

    received_hash = data.pop("hash")
    # signature в подписи НЕ участвует
    data.pop("signature", None)

    # data_check_string: key=value\n, отсортировано по key
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items())
    )

    # secret_key = HMAC_SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    # calculated_hash = HMAC_SHA256(secret_key, data_check_string)
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


@app.get("/")
async def health_check():
    return "ok"


@app.post("/v3")
async def api_v3(request: model.Request):
    """
    Универсальный эндпоинт под TMA:
    - request.method  — имя метода (start_data, test_qhc, ...)
    - request.params  — параметры
    - request.qhc     — Telegram WebApp initData
    """
    logger.debug("Received request method: %s", request.method)

    public_methods = {"start_data", "test_post"}  # без подписи

    parsed_init_data = None
    user_id = None

    # =========================
    # Проверка подписи initData
    # =========================
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

        # user в initData — JSON-строка
        user_raw = data.get("user")
        try:
            user = json.loads(user_raw) if isinstance(user_raw, str) else user_raw
        except json.JSONDecodeError:
            logger.exception("Cannot decode user JSON from initData")
            raise HTTPException(status_code=400, detail="Invalid user field in initData")

        data["user"] = user
        parsed_init_data = data
        user_id = user.get("id")
        logger.debug("Signature check passed, user_id: %s", user_id)
    else:
        logger.debug("Public method %s, skipping auth", request.method)

    # Базовый объект запроса, который можно возвращать в отладочных методах
    req = {
        "method": request.method,
        "params": request.params,
        "qhc": request.qhc,
        "init_data": parsed_init_data,
        "user_id": user_id,
    }

    # =========================
    # Публичные методы
    # =========================

    if request.method == "start_data":
        # стартовые данные для миниаппа
        return await start_data_0()

    if request.method == "test_post":
        # Пример тестового метода с параметром spin
        return await test_post(spin=request.params.get("spin"))

    # =========================
    # Служебный метод для проверки initData
    # =========================
    if request.method == "test_qhc":
        # Просто выдаём то, что распарсили
        return {
            "ok": True,
            "req": req,
        }

    # =========================
    # Боевая логика
    # =========================
    if request.method == "telega_rega_bot":
        # регистрация через бота
        await rega_new_user(request.params["id_telega"], request.params["data"])
        return {"status": "ok"}

    # сюда потом добавишь свои остальные методы:
    # if request.method == "some_method":
    #     ...

    # Если метода нет — вернём заглушку
    return {
        "status": "ne ok",
        "error": "unknown method",
        "req": req,
    }


if __name__ == "__main__":
    # Railway обычно сам запускает uvicorn, но если у тебя entrypoint = "python main.py",
    # то так ок:
    uvicorn.run(app, host="0.0.0.0", port=8000)
