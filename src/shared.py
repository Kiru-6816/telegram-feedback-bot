import mysql.connector
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from config import db_config

# Track user states
user_state = {}  # Format: {telegram_id: "reporting" | "suggesting" | None}
user_category_state = {}


async def show_categories(update: Update):
    """Show inline keyboard for category selection."""
    telegram_id = update.message.from_user.id
    if await is_user_banned(telegram_id):
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return
    keyboard = [
        [InlineKeyboardButton("🏫 School Facilities",
                              callback_data="facilities")],
        [InlineKeyboardButton("📚 Academics", callback_data="academics")],
        [InlineKeyboardButton("🎉 Events", callback_data="events")],
        [InlineKeyboardButton("🌱 Environment", callback_data="environment")],
        [InlineKeyboardButton("🌀 Others", callback_data="others")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "What type of suggestion do you have? Choose a category below:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def is_user_banned(telegram_id: int) -> bool:
    """Check if a user is banned."""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check blacklist table
        cursor.execute(
            "SELECT telegram_id FROM blacklist WHERE telegram_id = %s", (telegram_id,))
        is_banned = cursor.fetchone() is not None
        conn.close()

        return is_banned
    except mysql.connector.Error:
        return False  # Assume not banned if there's a database error
