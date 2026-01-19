import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import whisper
import tempfile

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загружаем модель Whisper (будет загружена при первом запуске)
# Используем модель 'base' - хороший баланс между скоростью и качеством
print("Загрузка модели Whisper...")
model = whisper.load_model("base")
print("Модель Whisper загружена!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я бот для преобразования голосовых сообщений в текст.\n\n"
        "📱 Просто отправь мне голосовое сообщение, и я переведу его в текст!\n\n"
        "Я использую технологию Whisper от OpenAI и автоматически расставляю знаки препинания."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "ℹ️ Как использовать:\n\n"
        "1. Отправь мне голосовое сообщение\n"
        "2. Подожди несколько секунд\n"
        "3. Получи текст с правильными знаками препинания!\n\n"
        "Команды:\n"
        "/start - Начать работу\n"
        "/help - Показать эту справку"
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик голосовых сообщений"""
    try:
        # Отправляем сообщение о начале обработки
        status_message = await update.message.reply_text("🎙 Обрабатываю голосовое сообщение...")

        # Получаем файл голосового сообщения
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)

        # Создаем временный файл для сохранения аудио
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_audio:
            temp_path = temp_audio.name
            await file.download_to_drive(temp_path)

        logger.info(f"Голосовое сообщение сохранено: {temp_path}")

        # Обновляем статус
        await status_message.edit_text("🔄 Распознаю речь...")

        # Распознаем речь с помощью Whisper
        result = model.transcribe(temp_path, language='ru', fp16=False)
        text = result["text"].strip()

        # Удаляем временный файл
        os.unlink(temp_path)

        # Проверяем, что текст не пустой
        if not text:
            await status_message.edit_text("❌ Не удалось распознать речь. Попробуйте еще раз.")
            return

        # Отправляем распознанный текст
        await status_message.edit_text(f"✅ Распознанный текст:\n\n{text}")

        logger.info(f"Успешно обработано сообщение: {text[:50]}...")

    except Exception as e:
        logger.error(f"Ошибка при обработке голосового сообщения: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке голосового сообщения. "
            "Пожалуйста, попробуйте еще раз."
        )

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик аудиофайлов"""
    await update.message.reply_text(
        "ℹ️ Я работаю только с голосовыми сообщениями из Telegram.\n"
        "Пожалуйста, отправьте голосовое сообщение (кнопка микрофона в чате)."
    )

def main():
    """Главная функция запуска бота"""
    # Получаем токен из переменной окружения
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    if not TOKEN:
        raise ValueError(
            "Не найден токен бота! Установите переменную окружения TELEGRAM_BOT_TOKEN"
        )

    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Добавляем обработчик голосовых сообщений
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Добавляем обработчик аудиофайлов (чтобы объяснить пользователю)
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))

    # Запускаем бота
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
