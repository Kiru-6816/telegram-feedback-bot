from telegram import Bot, Update
from telegram.ext import ContextTypes
from config import token, error_notify_user_id
import logging

# Logger setup
logging.basicConfig(
    filename='bot_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def log_error(error_text: str):
    """Log error messages to a file."""
    logging.error(error_text)


async def notify_admin_of_error(error_text: str):
    """Send an error notification to the specified admin via Telegram."""
    bot = Bot(token=token)
    try:
        await bot.send_message(
            chat_id=error_notify_user_id,
            text=f"🚨 Bot Error Notification:\n\n{error_text}"
        )
    except Exception as e:
        print(f"Failed to notify admin: {e}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors, notify the user, and inform the admin."""
    if update is not None and update.message:
        error_message = (
            "❌ An unexpected error occurred. Please try again later.\n"
            "If the problem persists, contact the admin."
        )
        await update.message.reply_text(error_message)
    else:
        print("Update is None or does not contain a message.")

    # Log error to file
    log_error(str(context.error))
    print(f"Error: {context.error}")

    # Notify admin via Telegram
    await notify_admin_of_error(str(context.error))

    # Notify user if possible
    if update is not None and getattr(update, "message", None):
        await update.message.reply_text(error_message)
    elif getattr(update, "callback_query", None):
        await update.callback_query.answer(error_message, show_alert=True)
    else:
        print("Unhandled update type in error handler.")
