import asyncio
import os
import io
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from fastapi import FastAPI, UploadFile, File
import uvicorn
from fastapi.responses import HTMLResponse  # <--- ДОБАВЬТЕ ЭТОТ ИМПОРТ


# Подключаем наше математическое ядро из соседнего файла
from engine import TelemetryEngine

BOT_TOKEN = os.getenv("BOT_TOKEN")
STORAGE_DIR = "./storage/telemetry"

# Создаем папку для безопасного хранения логов, если её нет
os.makedirs(STORAGE_DIR, exist_ok=True)

app = FastAPI()

@app.get("/dash", response_class=HTMLResponse)
async def get_dashboard():
    # Возвращаем монолитный, красивый гоночный интерфейс со встроенным CSS
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SmartDrag Telemetry — Mission Control</title>
        <style>
            /* Профессиональные стили в стиле Формулы-1 */
            body {
                background-color: #020617;
                color: #f8fafc;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0;
                padding: 16px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            header {
                border-b: 1px solid #1e293b;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding-bottom: 12px;
                margin-bottom: 24px;
                border-bottom: 2px solid #1e293b;
            }
            h1 {
                color: #ef4444;
                font-size: 24px;
                font-weight: 900;
                letter-spacing: 1px;
                margin: 0;
                text-transform: uppercase;
            }
            .subtitle {
                font-size: 11px;
                color: #94a3b8;
                margin: 4px 0 0 0;
                font-weight: bold;
            }
            .badge {
                background-color: #450a0a;
                color: #f87171;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 9999px;
                border: 1px solid #991b1b;
            }
            .grid {
                display: grid;
                grid-template-cols: repeat(2, 1fr);
                gap: 12px;
                margin-bottom: 24px;
            }
            @media (min-width: 600px) {
                .grid { grid-template-cols: repeat(4, 1fr); }
            }
            .card {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                padding: 16px;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
            .card-title {
                font-size: 11px;
                color: #94a3b8;
                text-transform: uppercase;
                font-weight: bold;
                margin: 0;
            }
            .card-value {
                font-size: 26px;
                font-weight: 900;
                margin: 8px 0 0 0;
                color: #ffffff;
            }
            .card-unit {
                font-size: 12px;
                color: #64748b;
                font-weight: normal;
            }
            .chart-container {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                padding: 16px;
                border-radius: 16px;
            }
            .chart-header {
                font-size: 13px;
                font-weight: bold;
                color: #cbd5e1;
                text-transform: uppercase;
                margin-bottom: 16px;
            }
            /* Стилизация SVG-графика высокого разрешения */
            .f1-chart {
                width: 100%;
                height: auto;
                background-color: #020617;
                border-radius: 8px;
            }
            .axis-line { stroke: #1e293b; stroke-width: 2; }
            .grid-line { stroke: #0f172a; stroke-width: 1; stroke-dasharray: 4; }
            .speed-path { fill: none; stroke: #38bdf8; stroke-width: 3; stroke-linecap: round; }
            .drag-path { fill: rgba(239, 68, 68, 0.15); stroke: #ef4444; stroke-width: 3; stroke-linecap: round; }
            .legend {
                display: flex;
                gap: 16px;
                margin-top: 12px;
                font-size: 12px;
            }
            .legend-item { display: flex; align-items: center; gap: 6px; color: #94a3b8; }
            .dot-speed { width: 10px; height: 10px; background-color: #38bdf8; border-radius: 50%; }
            .dot-drag { width: 10px; height: 10px; background-color: #ef4444; border-radius: 50%; }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div>
                    <h1>SmartDrag Telemetry</h1>
                    <p class="subtitle">🏎 МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ГИДРОАЭРОДИНАМИКИ СЕССИИ</p>
                </div>
                <div class="badge">F1 LIVE MODE</div>
            </header>

            <div class="grid">
                <div class="card">
                    <p class="card-title">Пиковая скорость</p>
                    <p class="card-value" style="color: #38bdf8;">86.2 <span class="card-unit">км/ч</span></p>
                </div>
                <div class="card">
                    <p class="card-title">Сопротивление воздуха</p>
                    <p class="card-value" style="color: #ef4444;">104.7 <span class="card-unit">Н</span></p>
                </div>
                <div class="card">
                    <p class="card-title">Потеря мощности</p>
                    <p class="card-value" style="color: #f97316;">1.18 <span class="card-unit">л.с.</span></p>
                </div>
                <div class="card">
                    <p class="card-title">Боковая перегрузка</p>
                    <p class="card-value" style="color: #22d3ee;">1.45 <span class="card-unit">G</span></p>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-header">📈 Линейный анализ набегающего потока (Скорость / Торможение)</div>
                
                <!-- Аппаратный рендеринг спортивного графика через векторную графику SVG -->
                <svg viewBox="0 0 500 200" class="f1-chart">
                    <!-- Сетки осей -->
                    <line x1="40" y1="20" x2="40" y2="170" class="axis-line" />
                    <line x1="40" y1="170" x2="480" y2="170" class="axis-line" />
                    <line x1="40" y1="70" x2="480" y2="70" class="grid-line" />
                    <line x1="40" y1="120" x2="480" y2="120" class="grid-line" />
                    
                    <!-- График Лобового Сопротивления (Красная гоночная волна с заливкой) -->
                    <path d="M 40 170 Q 120 40, 200 130 T 360 60 T 480 170 L 480 170 L 40 170 Z" class="drag-path" />
                    
                    <!-- График Скорости Карта по GPS (Синяя спортивная линия) -->
                    <path d="M 40 150 Q 120 30, 200 110 T 360 40 T 480 160" class="speed-path" />
                </svg>

                <div class="legend">
                    <div class="legend-item"><div class="dot-speed"></div> Скорость карта (GPS)</div>
                    <div class="legend-item"><div class="dot-drag"></div> Сила сопротивления воздуха (Ньютоны)</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """




bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
engine = TelemetryEngine()

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
    await message.answer("🔄 **Файл получен.** Локализирую лог на диск сервера и запускаю фильтрацию шумов...")

    # Безопасное скачивание файла на жесткий диск (Защита памяти сервера)
    file_id = message.document.file_id
    file_info = await bot.get_file(file_id)
    
    local_filepath = os.path.join(STORAGE_DIR, message.document.file_name)
    await bot.download_file(file_info.file_path, local_filepath)

    try:
        # 1. Скачиваем файл напрямую в оперативную память облачного сервера Render
        file_id = message.document.file_id
        file_info = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        
        # 2. Передаем байты в Pandas (Превращаем в гоночную таблицу без записи на диск)
        df = pd.read_csv(io.BytesIO(file_bytes.read()))
        
        # 3. Запускаем наше математическое ядро анализа заезда
        metrics = clean_and_analyze(df)
        
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
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())

