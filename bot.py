import json
import os
import logging

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

BOT_TOKEN = "8644485641:AAFJdbNKciBE3PWHIjGBplmBM1sVzeCTQg4"

# তোমার Telegram numeric User ID
ADMIN_ID = 7590910189

# Developer username
DEVELOPER_USERNAME = "@iTZ_ADMINS"

# প্রতি ২ মিনিট
INTERVAL = 120

DATA_FILE = "bot_data.json"


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# =========================
# DATA
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "message": None,
            "groups": []
        }

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


data = load_data()


# =========================
# ADMIN CHECK
# =========================

def is_admin(update: Update):
    return (
        update.effective_user
        and update.effective_user.id == ADMIN_ID
    )


# =========================
# /START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text(
            "❌ You are not authorized."
        )
        return

    if update.effective_chat.type in ["group", "supergroup"]:

        if not data["message"]:
            await update.message.reply_text(
                "⚠️ First set a message using /setmessage."
            )
            return

        chat_id = update.effective_chat.id

        if chat_id not in data["groups"]:
            data["groups"].append(chat_id)
            save_data(data)

        await update.message.reply_text(
            "🟢 Scheduler Started!\n\n"
            "Message will be sent every 2 minutes."
        )

    else:

        await update.message.reply_text(
            f"👋 Welcome!\n\n"
            f"🤖 Scheduled Announcement Bot\n"
            f"👨‍💻 Developer: {DEVELOPER_USERNAME}\n\n"
            f"📩 Use /setmessage to set your message.\n\n"
            f"📚 Commands:\n"
            f"/start - Start bot / scheduler\n"
            f"/help - Show help\n"
            f"/ls - Command list\n"
            f"/setmessage - Set message\n"
            f"/status - Check status\n"
            f"/disable - Stop scheduler"
        )


# =========================
# /HELP
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        await update.message.reply_text(
            "❌ You are not authorized."
        )
        return

    await update.message.reply_text(
        "📚 COMMAND LIST\n\n"
        "/start - Start bot or scheduler\n"
        "/help - Show this help\n"
        "/ls - Show command list\n"
        "/setmessage - Set announcement\n"
        "/status - Check status\n"
        "/disable - Stop scheduler\n\n"
        "⏱ Interval: 2 minutes\n"
        "🔐 Admin only control"
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
# /SETMESSAGE
# =========================

async def setmessage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        await update.message.reply_text(
            "❌ You are not authorized."
        )
        return

    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "⚠️ Use /setmessage in private chat."
        )
        return

    context.user_data["waiting_message"] = True

    await update.message.reply_text(
        "📩 Send me your announcement message now."
    )


# =========================
# RECEIVE MESSAGE
# =========================

async def receive_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        return

    if update.effective_chat.type != "private":
        return

    if not context.user_data.get("waiting_message"):
        return

    data["message"] = update.message.text

    context.user_data["waiting_message"] = False

    save_data(data)

    await update.message.reply_text(
        "✅ Message saved successfully!\n\n"
        "Now add the bot to your authorized group "
        "and use /start there."
    )


# =========================
# /DISABLE
# =========================

async def disable(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update):
        await update.message.reply_text(
            "❌ You are not authorized."
        )
        return

    if update.effective_chat.type not in [
        "group",
        "supergroup"
    ]:
        await update.message.reply_text(
            "⚠️ Use /disable inside the group."
        )
        return

    chat_id = update.effective_chat.id

    if chat_id in data["groups"]:

        data["groups"].remove(chat_id)
        save_data(data)

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

    if not is_admin(update):
        await update.message.reply_text(
            "❌ You are not authorized."
        )
        return

    chat_id = update.effective_chat.id

    if update.effective_chat.type in [
        "group",
        "supergroup"
    ]:

        running = chat_id in data["groups"]

        await update.message.reply_text(
            f"📊 Status\n\n"
            f"Scheduler: "
            f"{'🟢 ON' if running else '🔴 OFF'}\n"
            f"Message: "
            f"{'✅ Set' if data['message'] else '❌ Not set'}\n"
            f"Interval: 2 minutes"
        )

    else:

        await update.message.reply_text(
            f"📊 Bot Status\n\n"
            f"Message: "
            f"{'✅ Set' if data['message'] else '❌ Not set'}\n"
            f"Active groups: {len(data['groups'])}"
        )


# =========================
# SCHEDULER
# =========================

async def send_scheduled_message(
    context: ContextTypes.DEFAULT_TYPE
):

    if not data["message"]:
        return

    for chat_id in data["groups"].copy():

        try:

            await context.bot.send_message(
                chat_id=chat_id,
                text=data["message"]
            )

        except Exception as error:

            logging.error(
                f"Could not send to {chat_id}: {error}"
            )


# =========================
# MAIN
# =========================

def main():

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CommandHandler("ls", ls_command)
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

    print("Bot is running...")

    app.run_polling()


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()