# Telegram Feedback Bot

A Telegram bot for collecting feedback and error reports from users, with admin and super admin controls, MySQL database storage, and error notification/logging.

## Features

- Users can submit suggestions (up to 3 per day) in various categories.
- Users can report errors (up to 3 per day).
- Admins and super admins can export suggestions and reports, view stats, and manage bans.
- Attachments are blocked; only text is accepted.
- Banned users cannot interact with the bot.
- Errors are logged to a file and notified to a specified admin via Telegram.

## Setup

### 1. Clone the Repository

```sh
git clone https://github.com/Kiru-6816/telegram-feedback-bot.git
cd telegram-feedback-bot
```

### 2. Install Dependencies

```sh
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project directory with the following content:

```
TOKEN=your_telegram_bot_token
ADMINS=comma,separated,admin_ids
SUPER_ADMINS=comma,separated,super_admin_ids
ERROR_NOTIFY_USER_ID=your_telegram_user_id
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_DATABASE=your_db_name
```

- `ADMINS` and `SUPER_ADMINS` should be Telegram user IDs (numbers), comma-separated.
- `ERROR_NOTIFY_USER_ID` is the Telegram user ID to receive error notifications.

### 4. Set Up the Database

- Create a MySQL database.
- Run the SQL in `database_setup.sql` to create the required tables.

```sh
mysql -u your_db_user -p your_db_name < database_setup.sql
```

### 5. Run the Bot

```sh
python main.py
```

## File Structure

- `main.py` - Entry point, bot setup, and handler registration.
- `handlers.py` - Core message and command handlers.
- `commands.py` - Command implementations for users/admins.
- `shared.py` - Shared state and utility functions.
- `config.py` - Loads configuration from environment variables.
- `error_handlers.py` - Error logging and notification logic.
- `requirements.txt` - Python dependencies.
- `database_setup.sql` - SQL for required tables.
- `README.md` - This documentation.

## Customization

- To change categories, edit the `show_categories` function in `shared.py`.
- To change acknowledgment messages, edit the `acknowledgements` list in `config.py`.

## Notes

- Only text messages are accepted; attachments are blocked.
- All errors are logged to `bot_errors.log` and sent to the admin specified in `.env`.
- Make sure your bot token and database credentials are kept secure.

---

For any issues or contributions, please open an issue or pull request on the repository.
