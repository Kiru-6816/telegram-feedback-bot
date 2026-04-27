import mysql.connector
import datetime
import random
from telegram import Update
from telegram.ext import ContextTypes
from shared import user_category_state, user_state, show_categories, is_user_banned
from config import acknowledgements, admins, db_config


# Handle user messages and enforce restrictions for banned users
async def user_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id

    if await is_user_banned(telegram_id):
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return

    await suggestion_and_report_handler(update, context)


# Handle category button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = query.from_user.id
    category = query.data
    user_category_state[telegram_id] = category
    user_state[telegram_id] = "suggesting"

    await query.answer()
    await query.edit_message_text(
        text=f"📋 *Category Selected:* {category.capitalize()}\n\n✏️ Please send your suggestion below.",
        parse_mode="Markdown"
    )


# Handle suggestions and reports
async def suggestion_and_report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id

    if await is_user_banned(telegram_id):
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return

    state = user_state.get(telegram_id, None)

    # Handle reporting state
    if state == "reporting":
        message_text = update.message.text.strip()
        if len(message_text) < 5:
            await update.message.reply_text("⚠️ Your report is too short. Please provide more details.")
            return

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO error_reports (telegram_id, message, date)
                VALUES (%s, %s, NOW())
            """, (telegram_id, message_text))
            conn.commit()
            conn.close()

            await update.message.reply_text("✅ Thank you for reporting the issue. We'll look into it.")
            if telegram_id not in admins:
                user_state[telegram_id] = "choosing_category"
            if telegram_id in admins:
                user_state[telegram_id] = "none"
        except mysql.connector.Error as err:
            await update.message.reply_text(f"❌ Could not save your report due to a database error: {str(err)}")
        return

    if state == "choosing_category":
        await update.message.reply_text("⚠️ Please select a category first!")
        await show_categories(update)
        return

    if telegram_id in admins:
        await update.message.reply_text("⚠️ Your input was not recognized. Please use the available admin commands or type /help for assistance.")
        return

    category = user_category_state.get(telegram_id)
    if not category:
        await update.message.reply_text("⚠️ Please select a category first!")
        await show_categories(update)
        return

    message_text = update.message.text.strip()
    if len(message_text) < 3:
        await update.message.reply_text("⚠️ Your suggestion is too short. Please provide more details!")
        return

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        current_date = datetime.datetime.now().date()
        cursor.execute("""
            SELECT COUNT(*) FROM suggestions
            WHERE telegram_id = %s AND date = %s
        """, (telegram_id, current_date))
        count = cursor.fetchone()[0]

        if count >= 3:
            await update.message.reply_text("⚠️ You have already sent 3 suggestions today. Try again tomorrow!")
        else:
            cursor.execute("""
                INSERT INTO suggestions (telegram_id, message, date, category)
                VALUES (%s, %s, %s, %s)
            """, (telegram_id, message_text, current_date, category))
            conn.commit()

            response = random.choice(acknowledgements)
            await update.message.reply_text(response)

        conn.close()
    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ A database error occurred: {str(err)}")


# Block attachments and notify the user
async def block_attachments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id

    if await is_user_banned(telegram_id):
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return

    await update.message.reply_text(
        "⚠️ Attachments are not allowed. Please send text messages only."
    )


# Handle unknown commands
async def unknowncommand_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ Oops! I didn’t understand that command. Type /help to see what I can do."
    )
