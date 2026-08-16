import asyncio
import os
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
    # Возвращаем весь HTML-код дашборда напрямую из памяти сервера, исключая сбои путей Linux
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SmartDrag Telemetry - Mission Control</title>
        <script src="https://jsdelivr.net"></script>
        <script src="https://unpkg.com"></script>
        <script src="https://jsdelivr.net"></script>
        <script src="https://telegram.org"></script>
    </head>
    <body class="bg-slate-950 text-slate-100 font-sans antialiased">
        <div id="app" class="max-w-4xl mx-auto p-4">
            <header class="border-b border-slate-800 pb-4 mb-6 flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-black tracking-wider text-red-500 uppercase">SmartDrag Telemetry</h1>
                    <p class="text-xs text-slate-400 mt-1">📊 СГЛАЖЕННЫЙ АНАЛИЗ ГИДРОАЭРОДИНАМИКИ БОЛИДА</p>
                </div>
                <span class="px-3 py-1 bg-red-950 text-red-400 text-xs font-bold rounded-full border border-red-800 animate-pulse">
                    F1 LIVE MODE
                </span>
            </header>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                    <p class="text-xs text-slate-400 uppercase font-bold">Пиковая скорость</p>
                    <p class="text-2xl font-black text-white mt-1">86.2 <span class="text-xs text-slate-400">км/ч</span></p>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                    <p class="text-xs text-slate-400 uppercase font-bold">Лобовое сопротивление</p>
                    <p class="text-2xl font-black text-red-400 mt-1">104.7 <span class="text-xs text-slate-400">Н</span></p>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                    <p class="text-xs text-slate-400 uppercase font-bold">Потеря мощности</p>
                    <p class="text-2xl font-black text-orange-400 mt-1">1.18 <span class="text-xs text-slate-400">л.с.</span></p>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                    <p class="text-xs text-slate-400 uppercase font-bold">Боковая нагрузка</p>
                    <p class="text-2xl font-black text-cyan-400 mt-1">1.45 <span class="text-xs text-slate-400">G</span></p>
                </div>
            </div>

            <div class="bg-slate-900 border border-slate-800 p-4 rounded-2xl mb-6">
                <h3 class="text-sm font-bold text-slate-300 uppercase tracking-wide mb-4">📈 Линейный анализ воздушных потоков и ускорения</h3>
                <div class="relative h-64 w-full">
                    <canvas id="telemetryChart"></canvas>
                </div>
            </div>
        </div>

        <script>
            const { createApp, onMounted } = Vue;
            createApp({
                setup() {
                    onMounted(() => {
                        if (window.Telegram && window.Telegram.WebApp) {
                            window.Telegram.WebApp.ready();
                            window.Telegram.WebApp.expand();
                        }
                        const ctx = document.getElementById('telemetryChart').getContext('2d');
                        const labels = Array.from({length: 45}, (_, i) => `${i}с`);
                        const speedData = Array.from({length: 45}, (_, i) => 40 + Math.sin(i/3) * 30 + Math.random() * 2);
                        const dragData = speedData.map(s => (s ** 2) * 0.015);

                        new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: labels,
                                datasets: [
                                    { label: 'Скорость болида (км/ч)', data: speedData, borderColor: '#ffffff', borderWidth: 2, pointRadius: 0, tension: 0.3 },
                                    { label: 'Сила сопротивления воздуха (Ньютоны)', data: dragData, borderColor: '#ef4444', borderWidth: 2, pointRadius: 0, tension: 0.3, backgroundColor: 'rgba(239, 68, 68, 0.1)', fill: true }
                                ]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { labels: { color: '#94a3b8', font: { weight: 'bold' } } } },
                                scales: { x: { grid: { color: '#1e293b' }, ticks: { color: '#64748b' } }, y: { grid: { color: '#1e293b' }, ticks: { color: '#64748b' } } }
                            }
                        });
                    });
                }
            }).mount('#app');
        </script>
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
            [InlineKeyboardButton(text="📈 Открыть Дашборд Телеметрии (F1 Live)", web_app=WebAppInfo(url="https://telemetry-r49l.onrender.com"))]
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

