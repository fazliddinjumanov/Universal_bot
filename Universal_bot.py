import os
import logging
import sys
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# --- SOZLAMALAR (RENDERDAN OLADI) ---
# Tokenlarni kodga yozmaymiz, Renderning "Environment" bo'limiga yozamiz
API_TOKEN = os.getenv("8436252310:AAH5fVrD5FLMBqodFbxP27q-9cUEjV6jZ6g")
GOOGLE_API_KEY = os.getenv("AIzaSyCZeQ87rINQqYmaFq_i9BzNNigOdkNVQao")
# Render beradigan sayt manzili (https://sizning-app.onrender.com)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"



# Gemini sozlash
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Loglar
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# --- MENYU ---
def asosiy_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🤖 Gemini AI Chat")
    builder.button(text="🌐 Tarjima")
    # Qolgan tugmalar hozircha vizual
    builder.button(text="📄 PDF ➡️ Word")
    builder.button(text="📝 Word ➡️ PDF")
    builder.button(text="📊 Slayd ➡️ Word")
    builder.button(text="📷 Rasm ➡️ PDF")
    builder.button(text="📝 Rasmdan Matn (OCR)")
    builder.button(text="🗣️ Matn ➡️ Ovoz")
    builder.button(text="🎙️ Ovoz ➡️ Matn")
    builder.adjust(2, 2, 2, 3)
    return builder.as_markup(resize_keyboard=True)


USER_STATE = {}


# --- HANDLERLAR ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Salom! Universal bepul botga xush kelibsiz (Render 24/7) 👇",
        reply_markup=asosiy_menu()
    )


@dp.message(F.text == "🤖 Gemini AI Chat")
async def gemini_chat_btn(message: types.Message):
    USER_STATE[message.from_user.id] = "chat"
    await message.answer("✅ Chat rejimi! Savolingizni yozing:")


@dp.message(F.text == "🌐 Tarjima")
async def tarjima_btn(message: types.Message):
    USER_STATE[message.from_user.id] = "tarjima"
    await message.answer("✅ Tarjima rejimi! Matn yuboring:")


@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    if not text: return

    # Menyudagi so'zlarni bot javob deb o'ylamasligi uchun
    tugmalar = ["🤖 Gemini AI Chat", "🌐 Tarjima", "📄 PDF ➡️ Word", "📝 Word ➡️ PDF",
                "📊 Slayd ➡️ Word", "📷 Rasm ➡️ PDF", "📝 Rasmdan Matn (OCR)",
                "🗣️ Matn ➡️ Ovoz", "🎙️ Ovoz ➡️ Matn"]
    if text in tugmalar: return

    state = USER_STATE.get(user_id)

    if state == "chat":
        wait_msg = await message.answer("✍️...")
        try:
            response = model.generate_content(text)
            await wait_msg.delete()
            await message.answer(response.text, parse_mode="Markdown")
        except Exception as e:
            await wait_msg.edit_text(f"Xatolik: {e}")

    elif state == "tarjima":
        wait_msg = await message.answer("🔄 Tarjima...")
        try:
            response = model.generate_content(f"Tarjima qil (ingliz yoki o'zbek tiliga): {text}")
            await wait_msg.delete()
            await message.answer(response.text)
        except Exception as e:
            await wait_msg.edit_text(f"Xatolik: {e}")
    else:
        await message.answer("Iltimos, menyudan tugma tanlang 👆")


# --- RENDER UCHUN PING ROUTE ---
# Bu juda muhim! Render bot ishlab turganini tekshirish uchun shu joyga kirib ko'radi.
async def health_check(request):
    return web.Response(text="Bot ishlab turibdi! 🚀")


# --- ISHGA TUSHIRISH ---
async def on_startup(bot: Bot):
    # Webhookni ulaymiz
    if WEBHOOK_URL:
        full_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
        logging.info(f"Webhook o'rnatilmoqda: {full_url}")
        await bot.set_webhook(full_url)


def main():
    app = web.Application()

    # 1. Asosiy handlerlar
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # 2. Setup application
    setup_application(app, dp, bot=bot)

    # 3. Startup event (webhookni set qilish)
    app.on_startup.append(on_startup)

    # 4. Health check (UptimeRobot uchun)
    app.router.add_get('/', health_check)

    # 5. Portni Renderdan olish
    port = int(os.environ.get("PORT", 8080))

    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":

    main()

