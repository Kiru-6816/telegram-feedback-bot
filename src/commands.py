import mysql.connector
import datetime
import csv
import os
from telegram import Update, ForceReply
from telegram.ext import (ContextTypes)
from shared import user_category_state, user_state, show_categories
from config import admins, super_admins, db_config

# Common Commands


async def category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow users to manually change their category."""
    telegram_id = update.message.from_user.id
    # Clear the previously selected category
    user_category_state.pop(telegram_id, None)

    # Check if user is an admin
    if telegram_id in admins:
        await update.message.reply_text("⚠️ The /category command is intended for regular users, not admins.")
        return

    await update.message.reply_text(
        "📋 You have reset your category. Please choose a new category for your next suggestion."
    )
    await show_categories(update)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a dynamic help message based on user role."""
    telegram_id = update.message.from_user.id
    if telegram_id in super_admins:
        help_message = (
            "🔧 *Super Admin Commands:*\n\n"
            "  - /start: Initialize the bot.\n"
            "  - /help: Display this help message.\n"
            "  - /check <days>: Export suggestions from the last <days> days.\n"
            "  - /stats: View a summary of all suggestions.\n"
            "  - /report: Submit an error or issue for review.\n"
            "  - /export\\_reports: Export error reports to a CSV file.\n"
            "  - /ban <user id> <reason>: Ban a user with a specific reason.\n"
            "  - /unban <user id>: Unban a previously banned user.\n"
            "  - /list\\_banned\\_users: View a list of all banned users.\n\n"
            "Examples:\n"
            "`/check 7` - Export suggestions submitted in the last 7 days.\n"
            "`/ban 12345678 Use of inappropriate language` - Ban the user with ID `1245678` for using of inappropriate language.\n"
            "`/unban 12345678` - Unban the user with ID `12345678`"
        )
    elif telegram_id in admins:
        help_message = (
            "🔧 *Admin Commands:*\n\n"
            "  - /start: Initialize the bot.\n"
            "  - /help: Display this help message.\n"
            "  - /check <days>: Export suggestions from the last <days> days.\n"
            "  - /stats: View a summary of all suggestions.\n"
            "  - /report: Submit an error or issue for review.\n"
            "  - /export\\_reports: Export error reports to a CSV file.\n\n"
            "Example:\n"
            "`/check 7` - Export the last 7 days of suggestions.\n"
        )
    else:
        help_message = (
            "🤖 *How to Use the Suggestion Box Bot*\n\n"
            "🛠️ *Commands:*\n"
            "  - /start: Start the bot and begin submitting suggestions.\n"
            "  - /category: Change your category for suggestions.\n"
            "  - /help: Display this help message.\n"
            "  - /my\\_suggestions: View your recent suggestions.\n"
            "  - /report: Submit an error or issue for review.\n\n"
            "💡 *How It Works:*\n"
            "  - Choose a category to organize your suggestion.\n"
            "  - Submit your suggestions after selecting a category.\n"
            "  - You can send up to 3 suggestions per day.\n"
            "  - To report an error or issue, use `/report`. You can submit one report after clicking the command. If you need to submit another report, type `/report` again.\n\n"
            "Thank you for making our school a better place! 🎉"
        )
    await update.message.reply_text(help_message, parse_mode="Markdown")

# User Commands


async def mysuggestions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show a user's recent suggestions."""
    telegram_id = update.message.from_user.id

    # Check if user is an admin
    if telegram_id in admins:
        await update.message.reply_text("⚠️ The /my_suggestions command is intended for regular users, not admins.")
        return
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, message, date FROM suggestions
            WHERE telegram_id = %s
            ORDER BY date DESC
            LIMIT 5
        """, (telegram_id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await update.message.reply_text("📭 You have not submitted any suggestions yet.")
        else:
            response = "📋 *Your Recent Suggestions:*\n\n"
            for row in rows:
                response += f"- ID: {row[0]}, Date: {row[2]}\n  `{row[1]}`\n\n"
            await update.message.reply_text(response, parse_mode="Markdown")
    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ A database error occurred: {str(err)}")


async def report_error_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt the user to report an error with force_reply."""
    telegram_id = update.message.from_user.id

    # Check daily limit for reports
    current_date = datetime.datetime.now().date()
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check if the user has reached the daily limit
        cursor.execute("""
            SELECT COUNT(*) FROM error_reports WHERE telegram_id = %s AND DATE(date) = %s
        """, (telegram_id, current_date))
        report_count = cursor.fetchone()[0]
        conn.close()

        if report_count >= 3:
            await update.message.reply_text("⚠️ You have reached the daily limit of 3 reports. Try again tomorrow.")
            return
    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ A database error occurred: {str(err)}")
        return

    # Set the user state to "reporting"
    user_state[telegram_id] = "reporting"

    # Send the report prompt and track the message ID
    await update.message.reply_text(
        "🛠️ Please describe the issue you encountered:",
        reply_markup=ForceReply(selective=True)
    )

# Admin Commands


async def export_suggestions_to_csv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export the database to CSV and send it to the admin."""
    telegram_id = update.message.from_user.id

    # Check if user is an admin
    if telegram_id not in admins:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        # Get number of days from command
        if len(context.args) != 1 or not context.args[0].isdigit():
            await update.message.reply_text("⚠️ Usage: /check <number_of_days>")
            return

        days = int(context.args[0])
        end_date = datetime.datetime.now().date()
        start_date = end_date - datetime.timedelta(days=days)

        # Query database for relevant records
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, telegram_id, category, message, date FROM suggestions
            WHERE date BETWEEN %s AND %s
            ORDER BY date DESC
        """, (start_date, end_date))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await update.message.reply_text("📭 No suggestions found for the specified period.")
            return

        # Write to CSV file
        file_path = f"suggestions_{days}_days.csv"
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                ["ID", "Telegram ID", "Category", "Message", "Date"])
            writer.writerows(rows)

        # Send the file
        await update.message.reply_document(document=open(file_path, "rb"))

        # Clean up the file
        os.remove(file_path)

    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ A database error occurred: {str(err)}")
    except Exception as e:
        await update.message.reply_text(f"❌ An error occurred: {str(e)}")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show stats for admins."""
    telegram_id = update.message.from_user.id
    if telegram_id not in admins:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM suggestions")
        total = cursor.fetchone()[0]

        cursor.execute(
            "SELECT category, COUNT(*) FROM suggestions GROUP BY category")
        categories = cursor.fetchall()

        conn.close()

        response = f"📊 *Suggestions Stats:*\n\nTotal Suggestions: {total}\n\nBy Category:\n"
        for category, count in categories:
            response += f"  - {category}: {count}\n"
        await update.message.reply_text(response, parse_mode="Markdown")
    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ A database error occurred: {str(err)}")


async def export_reports_to_csv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export error reports to a CSV file for admins."""
    telegram_id = update.message.from_user.id
    if telegram_id not in admins:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, telegram_id, message, date
            FROM error_reports
            ORDER BY id ASC
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await update.message.reply_text("📭 No error reports found.")
            return

        # Write reports to a CSV file
        file_path = "error_reports.csv"
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Report ID", "Telegram ID",
                            "Message", "Date"])  # CSV header
            writer.writerows(rows)

        # Send the CSV file to the admin
        await update.message.reply_document(document=open(file_path, "rb"))
        os.remove(file_path)  # Clean up the file after sending
    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ Could not export reports due to a database error: {str(err)}")

# Super admin commands


async def ban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user by their Telegram ID."""
    admin_id = update.message.from_user.id

    if admin_id not in super_admins:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    # Check for arguments
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: /ban <telegram_id> <reason>")
        return

    try:
        telegram_id = int(context.args[0])
        reason = " ".join(context.args[1:])

        # Validate the Telegram ID
        if telegram_id <= 0:
            await update.message.reply_text("⚠️ Invalid Telegram ID. Please provide a valid number.")
            return

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check if user is already banned
        cursor.execute(
            "SELECT telegram_id FROM blacklist WHERE telegram_id = %s", (telegram_id,))
        if cursor.fetchone():
            await update.message.reply_text(f"⚠️ User {telegram_id} is already banned.")
            return

        # Insert into blacklist
        cursor.execute("""
            INSERT INTO blacklist (telegram_id, reason, banned_at, admin_id)
            VALUES (%s, %s, NOW(), %s)
        """, (telegram_id, reason, admin_id))
        conn.commit()

        # Log the ban action in an admin actions log
        cursor.execute("""
            INSERT INTO admin_actions (action, telegram_id, admin_id, action_time)
            VALUES (%s, %s, %s, NOW())
        """, ("ban", telegram_id, admin_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ User {telegram_id} has been banned for: {reason}")
    except ValueError:
        await update.message.reply_text("⚠️ Invalid Telegram ID. Please provide a valid number.")
    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ A database error occurred: {str(err)}")


async def unban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user by their Telegram ID."""
    admin_id = update.message.from_user.id

    if admin_id not in super_admins:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    # Check for arguments
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Usage: /unban <telegram_id>")
        return

    try:
        telegram_id = int(context.args[0])

    # Validate the Telegram ID
        if telegram_id <= 0:
            await update.message.reply_text("⚠️ Invalid Telegram ID. Please provide a valid positive number.")
            return

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check if user is banned
        cursor.execute(
            "SELECT telegram_id FROM blacklist WHERE telegram_id = %s", (telegram_id,))
        if not cursor.fetchone():
            await update.message.reply_text(f"⚠️ User {telegram_id} is not banned.")
            return

        # Remove from blacklist
        cursor.execute(
            "DELETE FROM blacklist WHERE telegram_id = %s", (telegram_id,))
        conn.commit()

        # Log the unban action in an admin actions log
        cursor.execute("""
            INSERT INTO admin_actions (action, telegram_id, admin_id, action_time)
            VALUES (%s, %s, %s, NOW())
        """, ("unban", telegram_id, admin_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ User {telegram_id} has been unbanned.")
    except ValueError:
        await update.message.reply_text("⚠️ Invalid Telegram ID. Please provide a valid number.")
    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ A database error occurred: {str(err)}")


async def list_banned_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all banned users."""
    admin_id = update.message.from_user.id

    if admin_id not in super_admins:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Retrieve all banned users
        cursor.execute("SELECT telegram_id, reason, banned_at FROM blacklist")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await update.message.reply_text("📋 No banned users.")
            return

        # Format the list
        banned_list = "\n".join(
            [f"👤 {row[0]} | Reason: {row[1]} | Date: {row[2].strftime('%Y-%m-%d %H:%M:%S')}" for row in rows]
        )
        await update.message.reply_text(f"📋 *Banned Users:*\n\n{banned_list}", parse_mode="Markdown")
    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ A database error occurred: {str(err)}")
