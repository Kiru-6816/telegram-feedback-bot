import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TOKEN')

admins = [int(x) for x in os.getenv('ADMINS', '').split(',') if x]
super_admins = [int(x) for x in os.getenv('SUPER_ADMINS', '').split(',') if x]
error_notify_user_id = int(os.getenv('ERROR_NOTIFY_USER_ID', 0))

db_config = {
    "host": os.getenv('DB_HOST'),
    "user": os.getenv('DB_USER'),
    "password": os.getenv('DB_PASSWORD'),
    "database": os.getenv('DB_DATABASE')
}

# Randomized acknowledgment messages
acknowledgements = [
    "✅ Thank you for your feedback! We'll review it soon. 💡",
    "🌟 Your idea has been recorded. Thank you for contributing!",
    "👍 Got it! Thanks for helping improve our service!",
    "📬 Your feedback is now in the system. Thanks!",
    "🙌 Thanks for your input! Together, we can make a difference."
]
