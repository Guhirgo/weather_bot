
import logging
import requests
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- КОНСТАНТИ ---
# 1. Замініть на свій токен
TELEGRAM_BOT_TOKEN = "7669729694:AAGEqOJUevQW3ZfDZzCswsfO791bD0RHwHk"
# 2. Замініть на свій API-ключ OpenWeatherMap
OPENWEATHERMAP_API_KEY = "c44a8a089d4f828cd6c46ad0b8a1747f"
# Місто для запиту
CITY = "Kyiv,UA"
# Шлях до файлу, де зберігаються ID чатів
CHATS_FILE = "chats.txt"
# Інтервал у секундах (30 хвилин = 1800 секунд)
INTERVAL_SECONDS = 3

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- ДОПОМІЖНІ ФУНКЦІЇ ---

def get_chat_ids():
    """Читає всі збережені Chat ID з файлу."""
    try:
        with open(CHATS_FILE, 'r') as f:
            # Повертає список унікальних ID
            return list(set(f.read().splitlines()))
    except FileNotFoundError:
        return []


def save_chat_id(chat_id: str):
    """Зберігає Chat ID у файл, якщо його там ще немає."""
    chat_ids = get_chat_ids()
    if chat_id not in chat_ids:
        with open(CHATS_FILE, 'a') as f:
            f.write(chat_id + '\n')
        logger.info(f"Збережено новий Chat ID: {chat_id}")


def get_weather_data() -> str:
    """Отримує дані про погоду з OpenWeatherMap і форматує їх."""
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": CITY,
        "appid": OPENWEATHERMAP_API_KEY,
        "units": "metric",
        "lang": "ua"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка при запиті до API погоди: {e}")
        return "Не вдалося отримати дані про погоду."

    # Обробка даних
    main = data.get('main', {})
    weather = data.get('weather', [{}])[0]
    wind = data.get('wind', {})

    temp = main.get('temp')
    feels_like = main.get('feels_like')
    description = weather.get('description', 'без опису').capitalize()
    wind_speed = wind.get('speed')
    humidity = main.get('humidity')

    # Форматування повідомлення
    message = (
        f"☀️ **Погода в Києві**\n"
        f"--- оновлення {time.strftime('%H:%M')} ---\n"
        f"🌡️ **Температура:** {temp:.1f}°C\n"
        f"🤔 **Відчувається як:** {feels_like:.1f}°C\n"
        f"☁️ **Умови:** {description}\n"
        f"💨 **Вітер:** {wind_speed:.1f} м/с\n"
        f"💧 **Вологість:** {humidity}%\n"
        f"\nЩоб відписатися, скористайтеся /stop."
    )
    return message


# --- ОБРОБНИКИ КОМАНД ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє команду /start. Зберігає Chat ID та надсилає вітальне повідомлення."""
    chat_id = str(update.effective_chat.id)
    save_chat_id(chat_id)  # Зберігаємо ID нового користувача

    # Надсилаємо перше повідомлення про погоду одразу
    weather_message = get_weather_data()

    await update.message.reply_text(
        f"Вітаю! Я буду надсилати вам оновлення погоди в Києві кожні 30 хвилин. \n\n{weather_message}",
        parse_mode='Markdown'
    )
    logger.info(f"Користувач {chat_id} почав користуватися ботом.")


# --- ФУНКЦІЯ ПЛАНУВАННЯ ---

async def send_weather_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Робота, яка виконується за розкладом: отримує погоду та надсилає її всім чатам."""
    logger.info("Початок циклу надсилання погоди всім користувачам.")

    chat_ids = get_chat_ids()
    if not chat_ids:
        logger.warning("Немає збережених Chat ID для надсилання повідомлення.")
        return

    weather_message = get_weather_data()

    for chat_id in chat_ids:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=weather_message,
                parse_mode='Markdown'
            )
            logger.info(f"Надіслано погоду в чат {chat_id}")
        except Exception as e:
            # Це може статися, якщо користувач заблокував бота
            logger.error(f"Не вдалося надіслати повідомлення в чат {chat_id}: {e}")


# --- ЗАПУСК БОТА ---

def main() -> None:
    """Запускає бота."""
    if TELEGRAM_BOT_TOKEN == "ВСТАВТЕ_ВАШ_ТОКЕН_БОТА_ТЕЛЕГРАМ" or \
            OPENWEATHERMAP_API_KEY == "ВСТАВТЕ_ВАШ_API_КЛЮЧ_ПОГОДИ":
        logger.error("Будь ласка, замініть усі заглушки (токен, ключ API) у коді.")
        return

    # 1. Створення Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 2. Додавання обробника команди /start
    application.add_handler(CommandHandler("start", start_command))

    # 3. Налаштування планувальника (Jobs)
    job_queue = application.job_queue
    # job_queue.run_repeating(функція, інтервал, перше_виконання)
    job_queue.run_repeating(
        send_weather_job,
        interval=INTERVAL_SECONDS,  # Кожні 30 хвилин
        first=5  # Перше виконання через 5 секунд після запуску бота
    )

    # 4. Запуск бота
    logger.info("Бот запущено. Початок опитування Telegram...")
    application.run_polling(poll_interval=1)


if __name__ == '__main__':
    main()