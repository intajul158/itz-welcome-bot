import json
import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.getenv("8644485641:AAFJdbNKciBE3PWHIjGBplmBM1sVzeCTQg4")

DEVELOPER_USERNAME = "@iTZ_ADMINS"

INTERVAL = 120  # 2 minutes
DATA_FILE = "bot_data.json"

PORT = int(os.getenv("PORT", "10000"))


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# =========================
# RENDER HEALTH SERVER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        return


def start_health_server():
    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    logging.info(
        f"Health server running on port {PORT}"
    )

    server.serve_forever()


# =========================
# DATA
# =========================

def load_data():

    if not os.path.exists(DATA_FILE):
        return {
            "users": {},
            "groups": {}
        }

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return {
            "users": {},
            "groups": {}
        }


def save_data():

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


data = load_data()


# =========================
# GROUP ADMIN CHECK
# =========================

async def is_group_admin(update: Update):

    if update.effective_chat.type not in [
        "group",
        "supergroup"
    ]:
        return False

    member = await update.effective_chat.get_member(
        update.effective_user.id
    )

    return member.status in [
        "administrator",
        "creator"
    ]


# =========================
# ADMIN ONLY MESSAGE
# =========================

async def admin_only(update: Update):

    await update.message.reply_text(
        "⚠️ This command is only for admins."
    )


# =========================
# /LT
# START SCHEDULER
# =========================

async def lt_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat

    # /lt শুধু group-এ
    if chat.type not in [
        "group",
        "supergroup"
    ]:

        await update.message.reply_text(
            "⚠️ Use /lt inside your group."
        )

        return

    # শুধু admin
    if not await is_group_admin(update):

        await admin_only(update)

        return

    user_id = str(
        update.effective_user.id
    )

    # Admin-এর saved message আছে কিনা
    user = data["users"].get(user_id)

    message = None

    if user:
        message = user.get("message")

    if not message:

        await update.message.reply_text(
            "⚠️ First set your message in private chat "
            "using /setmessage."
        )

        return

    group_id = str(chat.id)

    # Group ON
    data["groups"][group_id] = {
        "user_id": user_id,
        "enabled": True
    }

    save_data()

    await update.message.reply_text(
        "🟢 Scheduler ON\n\n"
        "Your saved message will be sent "
        "every 2 minutes."
    )


# =========================
# /DL
# STOP SCHEDULER
# =========================

async def dl_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat

    if chat.type not in [
        "group",
        "supergroup"
    ]:

        await update.message.reply_text(
            "⚠️ Use /dl inside your group."
        )

        return

    # শুধু admin
    if not await is_group_admin(update):

        await admin_only(update)

        return

    group_id = str(chat.id)

    group = data["groups"].get(group_id)

    if group and group.get("enabled"):

        group["enabled"] = False

        save_data()

        await update.message.reply_text(
            "🔴 Scheduler OFF."
        )

    else:

        await update.message.reply_text(
            "ℹ️ Scheduler is already OFF."
        )


# =========================
# /STATUS
# =========================

async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat

    # GROUP STATUS
    if chat.type in [
        "group",
        "supergroup"
    ]:

        if not await is_group_admin(update):

            await admin_only(update)

            return

        group_id = str(chat.id)

        group = data["groups"].get(group_id)

        if group and group.get("enabled"):

            state = "🟢 ON"

        else:

            state = "🔴 OFF"

        await update.message.reply_text(
            "📊 Group Status\n\n"
            f"Scheduler: {state}\n"
            "Interval: 2 minutes"
        )

        return

    # PRIVATE STATUS

    user_id = str(
        update.effective_user.id
    )

    user = data["users"].get(
        user_id,
        {}
    )

    message = user.get("message")

    await update.message.reply_text(
        "📊 Your Status\n\n"
        f"Message: "
        f"{'✅ Set' if message else '❌ Not set'}"
    )


# =========================
# /SETMESSAGE
# =========================

async def setmessage_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat

    # Group-এ দিলে
    if chat.type in [
        "group",
        "supergroup"
    ]:

        if not await is_group_admin(update):

            await admin_only(update)

            return

        await update.message.reply_text(
            "📩 Please use /setmessage "
            "in the bot's private chat."
        )

        return

    # Private chat
    if chat.type == "private":

        user_id = str(
            update.effective_user.id
        )

        data["users"].setdefault(
            user_id,
            {
                "message": None
            }
        )

        context.user_data[
            "waiting_message"
        ] = True

        await update.message.reply_text(
            "📩 Send your announcement "
            "message now."
        )


# =========================
# RECEIVE MESSAGE
# =========================

async def receive_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_chat.type != "private":
        return

    if not context.user_data.get(
        "waiting_message"
    ):
        return

    if not update.message.text:

        await update.message.reply_text(
            "⚠️ Please send a text message."
        )

        return

    user_id = str(
        update.effective_user.id
    )

    data["users"].setdefault(
        user_id,
        {
            "message": None
        }
    )

    data["users"][user_id][
        "message"
    ] = update.message.text

    context.user_data[
        "waiting_message"
    ] = False

    save_data()

    await update.message.reply_text(
        "✅ Message saved successfully!\n\n"
        "Now add me to your group and use "
        "/lt as a group admin."
    )


# =========================
# /CMD
# COMMAND LIST
# =========================

async def cmd_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat

    if chat.type in [
        "group",
        "supergroup"
    ]:

        await update.message.reply_text(
            "📚 COMMAND LIST\n\n"
            "/lt - Start scheduler "
            "(Admin only)\n"
            "/dl - Stop scheduler "
            "(Admin only)\n"
            "/status - Check status "
            "(Admin only)\n"
            "/setmessage - Set message "
            "(Use in private chat)\n"
            "/cmd - Show command list\n\n"
            "⏱ Interval: 2 minutes\n"
            "🔐 Group management is admin only."
        )

        return

    await update.message.reply_text(
        f"🤖 Scheduled Announcement Bot\n\n"
        f"👨‍💻 Developer: "
        f"{DEVELOPER_USERNAME}\n\n"
        "📚 COMMAND LIST\n\n"
        "/setmessage - Set your message\n"
        "/status - Check your message status\n"
        "/cmd - Show command list\n\n"
        "👥 After setting your message, "
        "add the bot to your group.\n\n"
        "🔐 Group scheduler is controlled "
        "by group admins.\n\n"
        "⚡ Group commands:\n"
        "/lt - ON\n"
        "/dl - OFF\n"
        "/status - Status"
    )


# =========================
# SCHEDULER
# =========================

async def send_scheduled_message(
    context: ContextTypes.DEFAULT_TYPE
):

    for group_id, group in list(
        data["groups"].items()
    ):

        if not group.get("enabled"):
            continue

        user_id = str(
            group.get("user_id")
        )

        user = data["users"].get(
            user_id
        )

        if not user:
            continue

        message = user.get("message")

        if not message:
            continue

        try:

            await context.bot.send_message(
                chat_id=int(group_id),
                text=message
            )

        except Exception as error:

            logging.error(
                f"Could not send to "
                f"{group_id}: {error}"
            )


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    # Render health server
    health_thread = threading.Thread(
        target=start_health_server,
        daemon=True
    )

    health_thread.start()

    # Telegram application
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler(
            "lt",
            lt_command
        )
    )

    app.add_handler(
        CommandHandler(
            "dl",
            dl_command
        )
    )

    app.add_handler(
        CommandHandler(
            "status",
            status_command
        )
    )

    app.add_handler(
        CommandHandler(
            "setmessage",
            setmessage_command
        )
    )

    app.add_handler(
        CommandHandler(
            "cmd",
            cmd_command
        )
    )

    # Private message receiver
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_message
        )
    )

    # Every 2 minutes
    app.job_queue.run_repeating(
        send_scheduled_message,
        interval=INTERVAL,
        first=INTERVAL
    )

    logging.info(
        "Bot is running..."
    )

    app.run_polling()


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()
