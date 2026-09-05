import os
import json
import logging
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)

# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "8370179229:AAEiEo7z1uSiWIjorSZfly8vUzi4qF04Kgk")

DEVELOPER = "iTZ iNTAJUL"
VERSION = "1.0"

DATA_FILE = Path("bot_data.json")


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# DATABASE
# ============================================================

def load_data():
    if not DATA_FILE.exists():
        return {
            "groups": {},
            "users": []
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception:
        logger.exception("Failed to load bot_data.json")

        return {
            "groups": {},
            "users": []
        }


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(
                bot_data,
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception:
        logger.exception("Failed to save bot_data.json")


bot_data = load_data()


# ============================================================
# 4 WELCOME CARDS
# ============================================================

WELCOME_CARDS = [

    # --------------------------------------------------------
    # CARD 1
    # --------------------------------------------------------

    """
╭━━━━━━━━━━━━━━━━━━━━╮
       👋 WELCOME
╰━━━━━━━━━━━━━━━━━━━━╯

Hello, {NAME}! 🎉

Welcome to {GROUP_NAME} ❤️

We're happy to have you here!

📌 Please follow the group rules
💬 Feel free to join the conversation

━━━━━━━━━━━━━━━━━━━━
       ✨ Enjoy your stay!
━━━━━━━━━━━━━━━━━━━━

👨‍💻 Developer
      iTZ iNTAJUL
""",

    # --------------------------------------------------------
    # CARD 2
    # --------------------------------------------------------

    """
┌─────────────────────┐
│   ✨ NEW MEMBER ✨   │
└─────────────────────┘

       👤 {NAME}

🎊 Welcome to the family!

You've officially joined
{GROUP_NAME} 🚀

🤝 Meet New People
💬 Join the Conversation
🌟 Enjoy the Community

──────────────────────
       ❤️ Have fun!
──────────────────────

👨‍💻 Developer
      iTZ iNTAJUL
""",

    # --------------------------------------------------------
    # CARD 3
    # --------------------------------------------------------

    """
╔══════════════════════╗
║    🎊 HELLO THERE!   ║
╚══════════════════════╝

Hey {NAME}! 👋

We're excited to have
you with us! 🥳

🌱 Make new friends
💬 Start a conversation
🤝 Respect everyone

       🎉 WELCOME 🎉

Enjoy your time here! 💙

━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 Developer
      iTZ iNTAJUL
━━━━━━━━━━━━━━━━━━━━━━
""",

    # --------------------------------------------------------
    # CARD 4
    # --------------------------------------------------------

    """
━━━━━━━━━━━━━━━━━━━━━━
        👑 WELCOME
━━━━━━━━━━━━━━━━━━━━━━

        {NAME} ✨

You are now a part of
our amazing community.

💎 {GROUP_NAME}

━━━━━━━━━━━━━━━━━━━━━━
  🤝 Connect
  💬 Communicate
  🌟 Enjoy
━━━━━━━━━━━━━━━━━━━━━━

       ❤️ Welcome!

👨‍💻 Developer
      iTZ iNTAJUL
━━━━━━━━━━━━━━━━━━━━━━
"""
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_group(chat):
    return chat and chat.type in ("group", "supergroup")


def get_group_settings(chat_id):

    chat_id = str(chat_id)

    if chat_id not in bot_data["groups"]:

        bot_data["groups"][chat_id] = {
            "allowed": False,
            "counter": 0
        }

        save_data()

    return bot_data["groups"][chat_id]


def escape_html(text):

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def get_user_name(user):

    if user.full_name:
        return user.full_name

    if user.username:
        return f"@{user.username}"

    return "New Member"


def create_mention(user):

    name = escape_html(get_user_name(user))

    return (
        f'<a href="tg://user?id={user.id}">'
        f'{name}'
        f'</a>'
    )


async def check_admin(update, context):

    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user:
        return False

    try:

        member = await context.bot.get_chat_member(
            chat.id,
            user.id
        )

        return member.status in (
            "administrator",
            "creator"
        )

    except Exception:

        logger.exception("Admin check failed")

        return False


# ============================================================
# /START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not user:
        return

    # Save user
    user_id = str(user.id)

    if user_id not in bot_data["users"]:

        bot_data["users"].append(user_id)

        save_data()

    name = create_mention(user)

    bot_username = context.bot.username or "your_bot"

    text = f"""
╭━━━━━━━━━━━━━━━━━━━━━━━━━━╮
        🤖  WELCOME
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯

👋 Hello, {name}!

Welcome to our official bot. ❤️

✨ What I can do:

• 🎉 Welcome new group members
• 🔄 4 different welcome cards
• ⚙️ Easy group control
• 🛡️ Admin-only settings

━━━━━━━━━━━━━━━━━━━━━━━━━━

👨‍💻 Developer
      <b>{DEVELOPER}</b>

🚀 Version {VERSION}

━━━━━━━━━━━━━━━━━━━━━━━━━━
     💙 Thanks for using me!
━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ Add Me To Group",
                    url=f"https://t.me/{bot_username}?startgroup=true"
                )
            ],
            [
                InlineKeyboardButton(
                    "📖 Help",
                    callback_data="help"
                ),
                InlineKeyboardButton(
                    "👨‍💻 Developer",
                    callback_data="developer"
                )
            ]
        ]
    )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )


# ============================================================
# /ALLOW
# ============================================================

async def allow(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if not is_group(chat):

        await update.message.reply_text(
            "❌ এই command শুধুমাত্র Telegram group-এ ব্যবহার করা যাবে।"
        )

        return

    if not await check_admin(update, context):

        await update.message.reply_text(
            "❌ শুধুমাত্র Group Admin এই command ব্যবহার করতে পারবেন।"
        )

        return

    group = get_group_settings(chat.id)

    group["allowed"] = True

    save_data()

    await update.message.reply_text(
        """
╭━━━━━━━━━━━━━━━━━━━━╮
     ✅ WELCOME ON
╰━━━━━━━━━━━━━━━━━━━━╯

🎉 Welcome system successfully enabled!

এখন থেকে নতুন member join করলে
automatic welcome message আসবে।

🔄 ৪টি Welcome Card
ঘুরে ঘুরে ব্যবহার হবে।

👨‍💻 Developer
      iTZ iNTAJUL

🛑 বন্ধ করতে /stop ব্যবহার করুন।
"""
    )


# ============================================================
# /STOP
# ============================================================

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if not is_group(chat):

        await update.message.reply_text(
            "❌ এই command শুধুমাত্র Telegram group-এ ব্যবহার করা যাবে।"
        )

        return

    if not await check_admin(update, context):

        await update.message.reply_text(
            "❌ শুধুমাত্র Group Admin এই command ব্যবহার করতে পারবেন।"
        )

        return

    group = get_group_settings(chat.id)

    group["allowed"] = False

    save_data()

    await update.message.reply_text(
        """
╭━━━━━━━━━━━━━━━━━━━━╮
     🛑 WELCOME OFF
╰━━━━━━━━━━━━━━━━━━━━╯

Welcome system disabled.

আবার চালু করতে:

/allow

👨‍💻 Developer
      iTZ iNTAJUL
"""
    )


# ============================================================
# /STATUS
# ============================================================

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if not is_group(chat):

        await update.message.reply_text(
            "❌ এই command group-এ ব্যবহার করুন।"
        )

        return

    group = get_group_settings(chat.id)

    if group["allowed"]:
        status_text = "🟢 ENABLED"
    else:
        status_text = "🔴 DISABLED"

    next_card = (group["counter"] % 4) + 1

    await update.message.reply_text(
        f"""
╭━━━━━━━━━━━━━━━━━━━━╮
       📊 BOT STATUS
╰━━━━━━━━━━━━━━━━━━━━╯

Welcome System: {status_text}

🔄 Next Welcome Card: #{next_card}

👨‍💻 Developer
      {DEVELOPER}

🚀 Version: {VERSION}
"""
    )


# ============================================================
# /HELP
# ============================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        f"""
╭━━━━━━━━━━━━━━━━━━━━╮
        📖 HELP
╰━━━━━━━━━━━━━━━━━━━━╯

🤖 Welcome Bot Commands

/start
Start the bot

/allow
Enable welcome system

/stop
Disable welcome system

/status
Check bot status

/help
Show help menu

━━━━━━━━━━━━━━━━━━━━

🔐 /allow এবং /stop
শুধুমাত্র Group Admin
ব্যবহার করতে পারবেন।

👨‍💻 Developer
      {DEVELOPER}

🚀 Version {VERSION}
"""
    )


# ============================================================
# BUTTON CALLBACK
# ============================================================

async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.data == "help":

        await query.message.reply_text(
            f"""
📖 <b>HELP</b>

/start - Start bot
/allow - Enable welcome
/stop - Disable welcome
/status - Check status
/help - Help menu

👨‍💻 Developer: <b>{DEVELOPER}</b>
""",
            parse_mode=ParseMode.HTML
        )

    elif query.data == "developer":

        await query.message.reply_text(
            f"""
╭━━━━━━━━━━━━━━━━━━━━╮
     👨‍💻 DEVELOPER
╰━━━━━━━━━━━━━━━━━━━━╯

<b>{DEVELOPER}</b>

🚀 Welcome Bot
⚙️ Group Welcome System

Version: {VERSION}
""",
            parse_mode=ParseMode.HTML
        )


# ============================================================
# NEW MEMBER HANDLER
# ============================================================

async def welcome_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message
    chat = update.effective_chat

    if not message or not chat:
        return

    if not message.new_chat_members:
        return

    group = get_group_settings(chat.id)

    # /allow না দেওয়া থাকলে welcome পাঠাবে না
    if not group["allowed"]:
        return

    group_name = escape_html(
        chat.title or "Our Group"
    )

    for new_member in message.new_chat_members:

        # Bot join করলে welcome message পাঠাবে না
        if new_member.is_bot:
            continue

        # Current card
        card_index = (
            group["counter"]
            % len(WELCOME_CARDS)
        )

        member_name = create_mention(
            new_member
        )

        welcome_text = WELCOME_CARDS[
            card_index
        ].format(
            NAME=member_name,
            GROUP_NAME=group_name
        )

        try:

            await message.reply_text(
                welcome_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

        except Exception:

            logger.exception(
                "Failed to send welcome message."
            )

        # Next card
        group["counter"] += 1

    save_data()


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Exception while handling update:",
        exc_info=context.error
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if (
        not BOT_TOKEN
        or BOT_TOKEN == "YOUR_BOT_TOKEN"
    ):

        raise RuntimeError(
            "BOT_TOKEN সেট করা হয়নি।"
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # --------------------------------------------------------
    # COMMANDS
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("allow", allow)
    )

    application.add_handler(
        CommandHandler("stop", stop)
    )

    application.add_handler(
        CommandHandler("status", status)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    # --------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            button_callback
        )
    )

    # --------------------------------------------------------
    # NEW MEMBER
    # --------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member
        )
    )

    # --------------------------------------------------------
    # ERROR
    # --------------------------------------------------------

    application.add_error_handler(
        error_handler
    )

    print("=" * 50)
    print("🤖 Welcome Bot is running...")
    print(f"👨‍💻 Developer: {DEVELOPER}")
    print(f"🚀 Version: {VERSION}")
    print("=" * 50)

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# ============================================================
# START BOT
# ============================================================

if __name__ == "__main__":
    main()
