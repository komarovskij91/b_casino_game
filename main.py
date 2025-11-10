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
from redis_aio import test_post, rega_new_user, test_while, chek_test, start_data_0

# -----------------------------
# Логирование
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# Prometheus metrics
# -----------------------------
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


# -----------------------------
# Утилита для метрик
# -----------------------------
def observe_request_metrics(method: str, endpoint: str, status_code: int, started_at: float) -> None:
    status_str = str(status_code)
    APP_METRIC_REQUEST_COUNT.labels(method, endpoint, status_str).inc()
    APP_METRIC_REQUEST_LATENCY.labels(method, endpoint, status_str).observe(time.time() - started_at)


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


# -----------------------------
# Фоновый таск при старте (chek_test)
# -----------------------------
@app.on_event("startup")
async def startup_event():
    # если chek_test – бесконечный цикл, пускай отдельно живёт
    asyncio.create_task(chek_test())
    logger.info("Background task chek_test started")


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
    print("Получен запрос:", request.model_dump())
    print("request.qhc", request.qhc)
    """
    Универсальный эндпоинт под TMA:
    - request.method  — имя метода (start_data, test_qhc, myprof, ...)
    - request.params  — параметры
    - request.qhc     — Telegram WebApp initData (initData string)
    """
    started_at = time.time()
    endpoint = "/v3"
    method_name: str = getattr(request, "method", None)

    logger.debug("Received /v3 method: %s", method_name)

    # Методы, которые НЕ требуют qhc/initData и проверки подписи
    public_methods = {
        "start_data",
        "test_post"
        "telega_rega_bot",  # этот часто вызывается не из миниаппа, оставим публичным
    }

    parsed_init_data: Optional[dict] = None
    user_id: Optional[int] = None

    # -------------------------
    # Проверка подписи initData
    # -------------------------
    if method_name not in public_methods:
        if not request.qhc or not request.qhc.strip():
            logger.error("qhc is empty for method %s", method_name)
            observe_request_metrics(method_name or "unknown", endpoint, 400, started_at)
            raise HTTPException(status_code=400, detail="qhc (initData) is required")

        logger.debug("Received qhc length: %s", len(request.qhc))
        logger.debug("qhc preview: %s...", request.qhc[:120])

        try:
            data = validate_telegram_init_data(request.qhc, config.TG_BOT_TOKEN)
        except ValueError as e:
            logger.error("Invalid signature for method %s: %s", method_name, e)
            observe_request_metrics(method_name or "unknown", endpoint, 401, started_at)
            raise HTTPException(status_code=401, detail="Invalid signature")

        # user в initData — JSON-строка
        user_raw = data.get("user")
        try:
            user = json.loads(user_raw) if isinstance(user_raw, str) else user_raw
        except json.JSONDecodeError:
            logger.exception("Cannot decode user JSON from initData")
            observe_request_metrics(method_name or "unknown", endpoint, 400, started_at)
            raise HTTPException(status_code=400, detail="Invalid user field in initData")

        data["user"] = user
        parsed_init_data = data
        user_id = user.get("id")
        logger.debug("Signature check passed, user_id: %s", user_id)
    else:
        logger.debug("Public method %s, skip initData auth", method_name)

    # Объект, который можно возвращать в отладочных методах

    req_obj = {
        "method": method_name,
        "params": request.params,
        "qhc": request.qhc,
        "init_data": parsed_init_data,
        "user_id": user_id,
    }

    # -------------------------
    # Роутинг по методам
    # -------------------------
    try:
        # Публичные методы
        if method_name == "start_data":
            response = await start_data_0()
            observe_request_metrics(method_name, endpoint, 200, started_at)
            return response

        if method_name == "test_post":
            response = await test_post(spin=request.params.get("spin"))
            observe_request_metrics(method_name, endpoint, 200, started_at)
            return response

        if method_name == "test_qhc":
            # просто возвращаем то, что пришло/распарсили
            observe_request_metrics(method_name, endpoint, 200, started_at)
            return {"ok": True, "req": req_obj}


        # TODO: сюда же добавишь остальные методы игры:
        # if method_name == "myprof":
        #     ...

        # Если метод неизвестен
        logger.warning("Unknown method in /v3: %s", method_name)
        observe_request_metrics(method_name or "unknown", endpoint, 400, started_at)
        raise HTTPException(status_code=400, detail={"message": "unknown method", "req": req_obj})

    except HTTPException:
        # уже всё залогировано и прометей обновлён выше
        raise
    except Exception as e:
        logger.exception("Error while handling method %s: %s", method_name, e)
        observe_request_metrics(method_name or "unknown", endpoint, 500, started_at)
        raise HTTPException(status_code=500, detail="internal server error")


# -----------------------------
# Точка входа
# -----------------------------
if __name__ == "__main__":
    # Railway обычно запускает `python main.py`, этого достаточно
    uvicorn.run(app, host="0.0.0.0", port=8000)
