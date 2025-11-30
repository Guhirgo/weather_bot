import logging
import asyncio
import requests
from telegram import Bot
from telegram.error import TelegramError

# --- КОНСТАНТИ (ОНОВЛЕНО) ---
TELEGRAM_BOT_TOKEN = "7669729694:AAGEqOJUevQW3ZfDZzCswsfO791bD0RHwHk"
OPENWEATHERMAP_API_KEY = "c44a8a089d4f828cd6c46ad0b8a1747f"
TARGET_CHAT_ID = "1060933896"
CITY = "Kyiv,UA"
# Інтервал для тестування: 30 секунд.
# Для постійної роботи не забудь змінити на 1800!
INTERVAL_SECONDS = 3

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- ФУНКЦІЇ ---

def get_weather_data(city: str) -> str:
    """Отримує дані про погоду з OpenWeatherMap і форматує їх."""
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHERMAP_API_KEY,
        "units": "metric",  # Температура у Цельсіях
        "lang": "ua"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Викликає HTTPError для поганих відповідей
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка при запиті до API погоди: {e}")
        return "Не вдалося отримати дані про погоду."

    # Обробка даних
    main = data.get('main', {})
    weather = data.get('weather', [{}])[0]
    wind = data.get('wind', {})

    # Конвертація
    temp = main.get('temp')
    feels_like = main.get('feels_like')
    description = weather.get('description', 'без опису').capitalize()
    wind_speed = wind.get('speed')
    humidity = main.get('humidity')

    # Форматування повідомлення
    message = (
        f"☀️ **Погода в Києві**\n"
        f"--- оновлення ---\n"
        f"🌡️ **Температура:** {temp:.1f}°C\n"
        f"🤔 **Відчувається як:** {feels_like:.1f}°C\n"
        f"☁️ **Умови:** {description}\n"
        f"💨 **Вітер:** {wind_speed:.1f} м/с\n"
        f"💧 **Вологість:** {humidity}%\n"
    )
    return message


async def send_weather_update(bot: Bot):
    """Отримує погоду та надсилає її у цільовий чат."""
    weather_message = get_weather_data(CITY)

    try:
        await bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=weather_message,
            parse_mode='Markdown'
        )
        logger.info(f"Надіслано оновлення погоди у чат {TARGET_CHAT_ID}")
    except TelegramError as e:
        logger.error(f"Помилка при надсиланні повідомлення в Telegram: {e}")


async def main():
    """Основна функція, яка запускає цикл оновлення."""
    # Примітка: Оскільки ти надав робочі ключі, перевірка заглушок видалена.

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    logger.info("Бот запущено. Початок циклу оновлення.")

    while True:
        # Чекаємо заданий інтервал
        await asyncio.sleep(INTERVAL_SECONDS)

        # Надсилаємо оновлення погоди
        await send_weather_update(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот зупинено вручну.")