import hmac, hashlib, os, json, asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# ========= ENV
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "8080"))

# ========= FastAPI app
app = FastAPI(title="MiniApp Backend")

# ========= Bot (polling cho nhanh)
application = Application.builder().token(BOT_TOKEN).build()

async def on_message(update: Update, context):
    msg = update.effective_message
    if msg and msg.web_app_data:
        data_str = msg.web_app_data.data
        try:
            data = json.loads(data_str)
        except Exception:
            data = {"raw": data_str}
        await msg.reply_text(f"Đã nhận từ Mini App: {data}")

application.add_handler(MessageHandler(filters.ALL, on_message))

# Khởi động polling trong background khi FastAPI start
@app.on_event("startup")
async def on_startup():
    asyncio.create_task(application.initialize())
    asyncio.create_task(application.start())
    # application.run_polling() là blocking; ta dùng initialize/start để chạy nền

@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()

# ========= Verify initData (chuẩn Telegram)
def validate_init_data(init_data: str) -> bool:
    from urllib.parse import parse_qsl
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    hash_recv = parsed.pop("hash", None)

    # 1) data_check_string = "{key}={value}\n..." theo thứ tự key a→z
    data_check_string = "\n".join(f"{k}={parsed[k]}" for k in sorted(parsed.keys()))

    # 2) secret = HMAC_SHA256(BOT_TOKEN, key="WebAppData")
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()

    # 3) calc_hash = HMAC_SHA256(data_check_string, key=secret) (hex)
    calc_hash = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()

    # 4) So sánh an toàn
    return hmac.compare_digest(calc_hash, hash_recv or "")

@app.post("/verify-init")
async def verify_init(req: Request):
    body = await req.json()
    init_data = body.get("initData")
    if not init_data:
        return JSONResponse({"ok": False, "error": "Missing initData"}, status_code=400)
    ok = validate_init_data(init_data)
    return JSONResponse({"ok": ok})

@app.get("/")
async def root():
    return PlainTextResponse("Backend OK")
