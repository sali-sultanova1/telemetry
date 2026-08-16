import asyncio
import os
import io
import math
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from fastapi import FastAPI, UploadFile, File
import uvicorn
from fastapi.responses import HTMLResponse
import pandas as pd

# Подключаем наше математическое ядро из соседнего файла (Соблюдаем SOLID)
from engine import TelemetryEngine

BOT_TOKEN = os.getenv("BOT_TOKEN")
STORAGE_DIR = "./storage/telemetry"
os.makedirs(STORAGE_DIR, exist_ok=True)

app = FastAPI()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
engine = TelemetryEngine() # Инициализируем наше гоночное ядро

@app.get("/dash", response_class=HTMLResponse)
async def get_dashboard():
    # Профессиональный расчет путей: находим точную корневую папку нашего проекта в облаке
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "templates", "index.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🏁 **MISSION CONTROL СИСТЕМЫ СТАНДАРТА FORMULA-1 ТЕЛЕМЕТРИИ** 🏁\n\n"
        "Инженерный бэкенд запущен. Алгоритмы фильтрации шумов датчиков активны.\n\n"
        "📥 Отправьте файл логов (`track.csv` или `mock_track.csv`) для проведения "
        "глубокого аэродинамического и динамического анализа сессии."
    )

@dp.message(lambda message: message.document and message.document.file_name.endswith(".csv"))
async def handle_telemetry_file(message: types.Message):
    await message.answer("🔄 **Файл получен.** Запускаю облачную фильтрацию шумов датчиков...")

    try:
        # 1. Скачиваем файл напрямую в оперативную память сервера (Защита диска Render)
        file_id = message.document.file_id
        file_info = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        
        # 2. Читаем таблицу напрямую из байтов памяти
        df = pd.read_csv(io.BytesIO(file_bytes.read()))
        
        # 3. КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Передаем таблицу в наше импортированное ядро engine!
        # Мы используем метод analyze или аналогичный главный метод вашего TelemetryEngine
        metrics = engine.analyze(df) 
        
        # Профессиональный спортивный отчет
        report = (
            f"📋 **ТЕЛЕМЕТРИЧЕСКИЙ ОТЧЕТ ПО РЕЗУЛЬТАТАМ ФИЛЬТРАЦИИ:**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏎 **Пиковая скорость болида:** `{metrics['max_speed']} км/ч`\n"
            f"🌪 **Сглаженное лобовое сопротивление:** `{metrics['max_drag']} Н`\n"
            f"📉 **Потеря чистой мощности на аэродинамику:** `{metrics['avg_power_loss']} л.с.`\n"
            f"⚡️ **Очищенная макс. боковая перегрузка:** `{metrics['max_lateral_g']} G`\n"
            f"🛑 **Макс. замедление при торможении:** `{metrics['max_braking_g']} G`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🧮 Успешно обработано телеметрических точек: `{metrics['total_points_analyzed']}`\n\n"
            f"🤖 Цифровой двойник заезда построен. Дашборд готов к рендерингу графиков."
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📈 Открыть Дашборд Телеметрии (F1 Live)", web_app=WebAppInfo(url="https://telemetry-r49l.onrender.com/dash"))]
        ])

        await message.answer(report, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка математического анализа лога: {str(e)}")

async def main():
    asyncio.create_task(dp.start_polling(bot))
    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ДЛЯ RENDER: Слушаем глобальный хост 0.0.0.0 и порт из среды облака
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())


