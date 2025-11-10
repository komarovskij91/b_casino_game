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

def check_webapp_signature_from_init_data(init_data: str, token=None) -> bool:
    """
    Проверяет подпись напрямую по оригинальной строке init_data.
    Реализация согласно старому рабочему варианту:
    Использует parse_qsl для декодирования значений, затем формирует data_check_string
    из декодированных значений (как в старом рабочем коде).
    
    Алгоритм (как в старом варианте):
    1. Парсим init_data через parse_qsl (декодирует URL-encoded значения)
    2. Извлекаем hash
    3. Формируем data_check_string из всех полей кроме hash, отсортированных по ключу
    4. Вычисляем secret_key = HMAC-SHA256("WebAppData", bot_token)
    5. Вычисляем calculated_hash = HMAC-SHA256(secret_key, data_check_string)
    6. Сравниваем calculated_hash с полученным hash
    """
    try:
        # Используем токен напрямую из кода для тестирования
        # Сначала пробуем переданный токен, потом хардкодный (который указал пользователь)
        if token is not None:
            bot_token = token.strip()
        else:
            # Используем хардкодный токен, который указал пользователь
            # Это токен бота, для которого создано мини-приложение
            bot_token = "8036216160:AAHwGBXCA-SWBGP6GqC8dd4uJX1q-RnR0NE"
            print(f"DEBUG: Using hardcoded token (length: {len(bot_token)}, preview: {bot_token[:15]}...)")
        
        if bot_token.startswith("Bot "):
            bot_token = bot_token[4:]
        if bot_token.startswith("bot "):
            bot_token = bot_token[4:]
        
        print(f"DEBUG: Final bot_token (length: {len(bot_token)}, preview: {bot_token[:15]}...)")
        
        # Парсим init_data используя parse_qsl - это декодирует URL-encoded значения
        # Это ключевое отличие от предыдущего подхода!
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
        
        if "hash" not in parsed_data:
            print("ERROR: Hash is not present in init_data")
            return False
        
        # Извлекаем hash (как в старом варианте)
        hash_value = parsed_data.pop('hash')
        
        # Удаляем signature, если есть (он не участвует в проверке)
        parsed_data.pop('signature', None)
        
        # ВАЖНО: В старом коде user остается как строка (не распарсена)
        # parse_qsl уже декодировал URL-encoding, но user - это JSON строка
        # Используем ее как есть для проверки подписи
        
        # Формируем строку для проверки подписи из ДЕКОДИРОВАННЫХ значений
        # Это ключевое отличие - используем декодированные значения из parse_qsl!
        # user остается как JSON строка (не объект)
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0))
        )
        
        print(f"DEBUG: data_check_string length: {len(data_check_string)}")
        print(f"DEBUG: data_check_string:\n{data_check_string}")
        print(f"DEBUG: hash from init_data: {hash_value}")
        print(f"DEBUG: keys in data_check_string: {sorted(parsed_data.keys())}")
        
        # Вычисляем секретный ключ: HMAC-SHA256("WebAppData", bot_token)
        # Как в старом варианте
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode('utf-8'),
            digestmod=hashlib.sha256
        )
        
        # Вычисляем hash: HMAC-SHA256(secret_key, data_check_string)
        # Как в старом варианте
        calculated_hash = hmac.new(
            key=secret_key.digest(),
            msg=data_check_string.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        is_valid = calculated_hash == hash_value
        
        print(f"DEBUG: calculated_hash: {calculated_hash}")
        print(f"DEBUG: received_hash: {hash_value}")
        print(f"DEBUG: valid: {is_valid}")
        
        if not is_valid:
            print(f"DEBUG: Token used: {bot_token[:25]}... (full length: {len(bot_token)})")
            print(f"DEBUG: Secret key (first 16 bytes hex): {secret_key.digest()[:16].hex()}")
            print(f"DEBUG: WARNING: Signature validation failed!")
            print(f"DEBUG: This might indicate:")
            print(f"DEBUG:   1. Wrong bot token")
            print(f"DEBUG:   2. Data was modified")
            print(f"DEBUG:   3. Time expired (auth_date too old)")
        else:
            print("DEBUG: SUCCESS! Signature validation passed!")
        
        return is_valid
    except Exception as e:
        print(f"ERROR: Exception in check_webapp_signature_from_init_data: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_webapp_signature(parsed_data: dict, token=config.TG_BOT_TOKEN) -> bool:
    """
    Check incoming WebApp init data signature
    Source: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    :param parsed_data: Словарь с распарсенными данными (будет изменен - hash будет удален)
    :param token: Токен бота
    :return: True если подпись валидна, False иначе
    """
    try:
        # Создаем копию, чтобы не изменять оригинальный словарь
        data_copy = parsed_data.copy()
        
        if "hash" not in data_copy:
            print("ERROR: Hash is not present in parsed_data")
            return False
        
        hash_ = data_copy.pop('hash')
        
        # ВАЖНО: signature не должен участвовать в проверке подписи!
        # Удаляем signature, если он есть
        if 'signature' in data_copy:
            data_copy.pop('signature')
            print("DEBUG: Removed 'signature' field from data_check_string (not used in signature verification)")
        
        # ВАЖНО: user должен быть декодированной JSON строкой (не объектом и не URL-encoded)!
        # parse_qsl уже декодирует URL-encoding, поэтому используем сохраненную JSON строку
        if '_user_json' in data_copy:
            data_copy['user'] = data_copy.pop('_user_json')
            print(f"DEBUG: Using saved user JSON string for signature check (length: {len(data_copy['user'])})")
            print(f"DEBUG: User JSON string preview: {data_copy['user'][:100]}...")
        elif 'user' in data_copy and isinstance(data_copy['user'], dict):
            # Fallback: если сохраненной строки нет, преобразуем обратно в JSON
            data_copy['user'] = json.dumps(data_copy['user'], separators=(',', ':'))
            print("DEBUG: Converted user dict back to JSON string for signature check (fallback)")
        
        # Формируем строку для проверки подписи (только поля без hash и signature)
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(data_copy.items(), key=itemgetter(0))
        )
        
        print(f"DEBUG: data_check_string length: {len(data_check_string)}")
        print(f"DEBUG: data_check_string preview: {data_check_string[:200]}...")
        print(f"DEBUG: Token length: {len(token)}")
        print(f"DEBUG: Token preview: {token[:10]}...")
        
        secret_key = hmac.new(
            key=b"WebAppData", msg=token.encode(), digestmod=hashlib.sha256
        )
        calculated_hash = hmac.new(
            key=secret_key.digest(), msg=data_check_string.encode(), digestmod=hashlib.sha256
        ).hexdigest()
        
        is_valid = calculated_hash == hash_
        print(f"DEBUG: Signature check - calculated: {calculated_hash}, received: {hash_}, valid: {is_valid}")
        
        if not is_valid:
            print(f"DEBUG: Keys in data_copy: {list(data_copy.keys())}")
            print(f"DEBUG: Full data_check_string:\n{data_check_string}")
        
        return is_valid
    except Exception as e:
        print(f"ERROR: Exception in check_webapp_signature: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def parse_user_query(init_data: str, req):
    """
    Парсит init_data и возвращает распарсенные данные.
    Выбрасывает HTTPException при ошибке вместо использования raise_response.
    Сохраняет оригинальную строку user для проверки подписи.
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
        # Сохраняем декодированную JSON строку user ДО преобразования в объект
        # parse_qsl уже декодирует URL-encoding, но user остается как JSON строка
        user_json_string = parsed_data.get('user', '')
        parsed_data['user'] = json.loads(user_json_string)
        
        # Сохраняем декодированную JSON строку для проверки подписи
        parsed_data['_user_json'] = user_json_string
        print(f"DEBUG: Saved user JSON string for signature check (length: {len(user_json_string)})")
        print(f"DEBUG: parse_user_query succeeded, user_id: {parsed_data.get('user', {}).get('id', 'unknown')}")
    except ValueError as e:
        print(f"ERROR: ValueError in parse_user_query: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Init data is not a valid query string"
        )
    except json.JSONDecodeError as e:
        print(f"ERROR: JSONDecodeError in parse_user_query: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="User data is not valid JSON"
        )
    except KeyError as e:
        print(f"ERROR: KeyError in parse_user_query: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Missing required field: {str(e)}"
        )
    
    if "hash" not in parsed_data:
        print("ERROR: Hash is not present in init data")
        raise HTTPException(
            status_code=401,
            detail="Hash is not present in init data"
        )
    
    return parsed_data

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
    print(f"DEBUG: Received request method: {request.method}")
    
    # Методы, которые могут работать без аутентификации
    public_methods = ["start_data", "test_post"]
    
    # Проверяем qhc перед обработкой запроса (кроме публичных методов)
    if request.method not in public_methods:
        if not request.qhc or len(request.qhc.strip()) == 0:
            print("ERROR: qhc is empty")
            raise HTTPException(status_code=400, detail="qhc (initData) is required")
        
        print(f"DEBUG: Received qhc length: {len(request.qhc)}")
        print(f"DEBUG: qhc preview: {request.qhc[:100]}...")
        
        # Парсим qhc (теперь parse_user_query выбрасывает HTTPException)
        try:
            parsed_data = parse_user_query(request.qhc, request)
        except HTTPException:
            raise  # Пробрасываем HTTPException дальше
        except Exception as e:
            print(f"ERROR: Unexpected error in parse_user_query: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=f"Error parsing qhc: {str(e)}")
        
        # Проверяем подпись напрямую по оригинальной строке init_data
        print("DEBUG: Checking signature...")
        try:
            # Используем прямую проверку по оригинальной строке - это более надежно
            # Передаем None, чтобы использовался хардкодный токен из функции
            signature_valid = check_webapp_signature_from_init_data(request.qhc, None)
            
            if not signature_valid:
                print("ERROR: Invalid signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
            
            print("DEBUG: Signature check passed")
        except HTTPException:
            raise
        except Exception as e:
            print(f"ERROR: Error checking signature: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=401, detail=f"Signature verification error: {str(e)}")
        
        print("DEBUG: All checks passed, processing method...")
        parsed_data_for_response = parsed_data
    else:
        # Для публичных методов не требуется аутентификация
        print(f"DEBUG: Public method {request.method}, skipping authentication")
        parsed_data_for_response = None
    
    # Если проверка прошла успешно (или метод публичный), продолжаем обработку
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
            "qhc": request.qhc,
            "user": parsed_data_for_response.get("user") if parsed_data_for_response else None
        }
    
    if request.method == "test_post":
        # test_post - публичный метод, не требует аутентификации
        return await test_post(spin=req["params"]["spin"])
    
    if request.method == "start_data":
        return await start_data_0()
    
    if request.method == "test_qhc":
        print("метод test_qhc")
        print("req")
        print(req)
        print("parsed_data (user info):")
        print(parsed_data_for_response.get("user") if parsed_data_for_response else None)
        print(request)
        return {
            "status": "success",
            "message": "oke",
            "user": parsed_data_for_response.get("user") if parsed_data_for_response else None
        }
    
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

