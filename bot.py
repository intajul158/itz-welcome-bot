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

BOT_TOKEN = os.getenv("BOT_TOKEN", "8644485641:AAFJdbNKciBE3PWHIjGBplmBM1sVzeCTQg4")
DEVELOPER_USERNAME = "@iTZ_ADMINS"

INTERVAL = 120
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
# HEALTH SERVER
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
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    logging.info(f"Health server running on port {PORT}")
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
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {
            "users": {},
            "groups": {}
        }


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


data = load_data()


# =========================
# ADMIN CHECK
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
# ADMIN-ONLY MESSAGE
# =========================

async def admin_only(update: Update):

    await update.message.reply_text(
        "⚠️ This command is only for admins."
    )


# =========================
# /START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat
    user_id = str(update.effective_user.id)

    # GROUP
    if chat.type in ["group", "supergroup"]:

        if not await is_group_admin(update):
            await admin_only(update)
            return

        if user_id not in data["users"]:
            await update.message.reply_text(
                "⚠️ First set your message in private chat "
                "using /setmessage."
            )
            return

        message = data["users"][user_id].get("message")

        if not message:
            await update.message.reply_text(
                "⚠️ First set your message in private chat "
                "using /setmessage."
            )
            return

        group_id = str(chat.id)

        data["groups"][group_id] = {
            "user_id": user_id,
            "enabled": True
        }

        save_data()

        await update.message.reply_text(
            "🟢 Scheduler Started!\n\n"
            "Your saved message will be sent every 2 minutes."
        )
        return

    # PRIVATE
    if chat.type == "private":

        if user_id not in data["users"]:
            data["users"][user_id] = {
                "message": None
            }
            save_data()

        await update.message.reply_text(
            f"👋 Welcome!\n\n"
            f"🤖 Scheduled Announcement Bot\n"
            f"👨‍💻 Developer: {DEVELOPER_USERNAME}\n\n"
            f"📩 Use /setmessage to save your message.\n\n"
            f"📚 Commands:\n"
            f"/start - Start\n"
            f"/setmessage - Set your message\n"
            f"/status - Check status\n"
            f"/disable - Stop scheduler\n"
            f"/help - Help\n"
            f"/ls - Command list\n"
            f"/lt - Admin command information"
        )


# =========================
# /SETMESSAGE
# =========================

async def setmessage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat
    user_id = str(update.effective_user.id)

    # GROUP
    if chat.type in ["group", "supergroup"]:

        if not await is_group_admin(update):
            await admin_only(update)
            return

        await update.message.reply_text(
            "📩 Please use /setmessage in the bot's "
            "private chat."
        )
        return

    # PRIVATE
    if chat.type == "private":

        data["users"].setdefault(
            user_id,
            {"message": None}
        )

        context.user_data["waiting_message"] = True

        await update.message.reply_text(
            "📩 Send me your announcement message now."
        )


# =========================
# RECEIVE PRIVATE MESSAGE
# =========================

async def receive_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_chat.type != "private":
        return

    if not context.user_data.get("waiting_message"):
        return

    user_id = str(update.effective_user.id)

    if not update.message.text:
        await update.message.reply_text(
            "⚠️ Please send a text message."
        )
        return

    data["users"].setdefault(
        user_id,
        {"message": None}
    )

    data["users"][user_id]["message"] = update.message.text

    context.user_data["waiting_message"] = False

    save_data()

    await update.message.reply_text(
        "✅ Message saved successfully!\n\n"
        "Now add the bot to your group and use "
        "/start there as a group admin."
    )


# =========================
# /DISABLE
# =========================

async def disable(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat

    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text(
            "⚠️ Use /disable inside your group."
        )
        return

    if not await is_group_admin(update):
        await admin_only(update)
        return

    group_id = str(chat.id)

    if group_id in data["groups"]:
        data["groups"][group_id]["enabled"] = False
        save_data()

        await update.message.reply_text(
            "🔴 Scheduler Disabled."
        )
    else:
        await update.message.reply_text(
            "ℹ️ Scheduler is already disabled."
        )


# =========================
# /STATUS
# =========================

async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat

    if chat.type in ["group", "supergroup"]:

        if not await is_group_admin(update):
            await admin_only(update)
            return

        group_id = str(chat.id)

        group = data["groups"].get(group_id)

        if group and group.get("enabled"):
            scheduler = "🟢 ON"
        else:
            scheduler = "🔴 OFF"

        await update.message.reply_text(
            f"📊 Group Status\n\n"
            f"Scheduler: {scheduler}\n"
            f"Interval: 2 minutes"
        )
        return

    # PRIVATE
    user_id = str(update.effective_user.id)

    user = data["users"].get(user_id, {})
    message = user.get("message")

    await update.message.reply_text(
        f"📊 Your Status\n\n"
        f"Message: "
        f"{'✅ Set' if message else '❌ Not set'}"
    )


# =========================
# /HELP
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat

    if chat.type in ["group", "supergroup"]:

        if not await is_group_admin(update):
            await admin_only(update)
            return

        await update.message.reply_text(
            "📚 GROUP ADMIN COMMANDS\n\n"
            "/start - Start scheduler\n"
            "/disable - Stop scheduler\n"
            "/status - Check status\n"
            "/setmessage - Set message in private chat\n"
            "/lt - Admin command information\n\n"
            "⏱ Interval: 2 minutes\n"
            "🔐 Only group admins can control the scheduler."
        )
        return

    await update.message.reply_text(
        "📚 PRIVATE COMMANDS\n\n"
        "/start - Start\n"
        "/setmessage - Set your message\n"
        "/status - Check your status\n"
        "/help - Help\n"
        "/ls - Command list\n"
        "/lt - Admin command information"
    )


# =========================
# /LS
# =========================

async def ls_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await help_command(update, context)


# =========================
# /LT
# =========================

async def lt_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat

    if chat.type in ["group", "supergroup"]:

        if not await is_group_admin(update):
            await update.message.reply_text(
                "⚠️ This command is only for admins."
            )
            return

        await update.message.reply_text(
            "🔐 Admin Command\n\n"
            "Only group administrators can manage "
            "the scheduler.\n\n"
            "/start - Start scheduler\n"
            "/disable - Stop scheduler\n"
            "/status - Check status\n"
            "/setmessage - Set message privately"
        )
        return

    await update.message.reply_text(
        "🔐 /lt\n\n"
        "Group management commands are available "
        "only to group administrators."
    )


# =========================
# SCHEDULER
# =========================

async def send_scheduled_message(
    context: ContextTypes.DEFAULT_TYPE
):

    for group_id, group in list(data["groups"].items()):

        if not group.get("enabled"):
            continue

        user_id = str(group.get("user_id"))

        user = data["users"].get(user_id)

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
                f"Could not send to {group_id}: {error}"
            )


# =========================
# MAIN
# =========================

def main():

    # Render health server
    health_thread = threading.Thread(
        target=start_health_server,
        daemon=True
    )
    health_thread.start()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("setmessage", setmessage)
    )

    app.add_handler(
        CommandHandler("disable", disable)
    )

    app.add_handler(
        CommandHandler("status", status)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CommandHandler("ls", ls_command)
    )

    app.add_handler(
        CommandHandler("lt", lt_command)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_message
        )
    )

    # প্রতি ২ মিনিটে
    app.job_queue.run_repeating(
        send_scheduled_message,
        interval=INTERVAL,
        first=INTERVAL
    )

    logging.info("Bot is running...")

    app.run_polling()


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()
