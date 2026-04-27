import mysql.connector
import time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
)
from config import token, admins, db_config
from commands import report_error_command, help_command, category_command, mysuggestions_command, export_reports_to_csv_command, export_suggestions_to_csv_command, stats_command, ban_user_command, unban_user_command, list_banned_users_command
from handlers import suggestion_and_report_handler, button_handler, block_attachments, unknowncommand_handler
from error_handlers import error_handler
from shared import user_state, show_categories, is_user_banned

# MySQL Database Setup


def init_db():
    """Initialize the MySQL database and create tables for suggestions and error reports."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Suggestions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            category VARCHAR(255) DEFAULT 'General',
            message TEXT NOT NULL,
            date DATE NOT NULL
        )
    """)

    # Error reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            message TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Blacklist table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            telegram_id BIGINT PRIMARY KEY,
            admin_id BIGINT,
            reason TEXT,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Logging table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_actions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            action ENUM('ban', 'unban'),
            telegram_id BIGINT NOT NULL,
            admin_id BIGINT NOT NULL,
            action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message and show categories."""
    telegram_id = update.message.from_user.id
    user_state.pop(telegram_id, None)

    if telegram_id in admins:
        welcome_message = (
            "👋 Welcome to the School Suggestion Box Bot! 🎉\n\n"
            "🛠 You have admin access. Use /help to view admin commands."
        )
    elif await is_user_banned(telegram_id):
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return
    else:
        welcome_message = (
            "🎉 Welcome to the School Suggestion Box! 🎉\n\n"
            "📢 *Your ideas matter!* Use this platform to share your thoughts on how we can make our school better.\n\n"
            "ℹ️ *Need help?* type /help for guidance on how to use this bot!\n\n"
            "💡 Ready to make a difference!!"
        )
        user_state[telegram_id] = "choosing_category"
    # Clear any previous user state
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

    if telegram_id not in admins:
        await show_categories(update)


def main():
    """Run the bot."""
    TOKEN = token

    # Initialize database
    init_db()

    # Build the application
    application = ApplicationBuilder().token(TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("report", report_error_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("category", category_command))
    application.add_handler(CommandHandler(
        "my_suggestions", mysuggestions_command))
    application.add_handler(CommandHandler(
        "check", export_suggestions_to_csv_command))
    application.add_handler(CommandHandler(
        "export_reports", export_reports_to_csv_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("ban", ban_user_command))
    application.add_handler(CommandHandler("unban", unban_user_command))
    application.add_handler(CommandHandler(
        "list_banned_users", list_banned_users_command))
    application.add_handler(MessageHandler(
        filters.COMMAND, unknowncommand_handler))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, suggestion_and_report_handler))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.Document.ALL |
                            filters.Sticker.ALL | filters.VOICE | filters.VIDEO_NOTE | filters.ANIMATION, block_attachments))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(error_handler)

    # Run the bot
    print("Bot is running...")
    application.run_polling()


while True:
    try:
        main()  # Start the bot
    except Exception as e:
        print(f"Bot crashed with error: {e}. Restarting in 5 seconds...")
        time.sleep(5)  # Wait before restarting
