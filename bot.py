import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Target channel username (must include @ and bot MUST be an admin in this channel)
CHANNEL_USERNAME = "@financemasters1"
CHANNEL_URL = "https://t.me/financemasters1"


async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if the user is currently subscribed to the channel."""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        # Returns True if user is creator, administrator, or regular member
        return member.status in ["creator", "administrator", "member"]
    except TelegramError as e:
        logger.error(f"Error checking chat member status: {e}")
        # If check fails (e.g. bot is not admin in channel), allow access to avoid locking everyone out
        return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responds when the user types /start."""
    user = update.effective_user
    if not update.message:
        return

    # Check channel membership
    subscribed = await is_user_member(user.id, context)

    if subscribed:
        # Access Granted: Welcome message
        welcome_text = (
            f"Hello {user.first_name}! 👋\n\n"
            "📈 **FinanceGrowthBot** helps you learn personal finance, "
            "improve money habits, and grow long-term wealth with simple, practical tips."
        )
        await update.message.reply_text(text=welcome_text, parse_mode="Markdown")
    else:
        # Access Denied: Force join prompt
        force_join_text = (
            f"⚠️ **Access Denied!**\n\n"
            f"Hello {user.first_name}, you must join our official channel to use this bot.\n\n"
            f"Click the button below to join, then click **Verify** to start using the bot."
        )
        keyboard = [
            [InlineKeyboardButton("📢 Join Finance Masters Channel", url=CHANNEL_URL)],
            [InlineKeyboardButton("🔄 Verify Membership", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text=force_join_text, reply_markup=reply_markup, parse_mode="Markdown")


async def check_subscription_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the 'Verify Membership' button click."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    subscribed = await is_user_member(user.id, context)

    if subscribed:
        # Edit the prompt into the welcome message once verified
        welcome_text = (
            f"✅ **Verification Successful!**\n\n"
            f"Welcome {user.first_name}!\n\n"
            "📈 **FinanceGrowthBot** helps you learn personal finance, "
            "improve money habits, and grow long-term wealth with simple, practical tips."
        )
        await query.edit_message_text(text=welcome_text, parse_mode="Markdown")
    else:
        # Show alert if they still haven't joined
        await query.answer("❌ You still haven't joined the channel! Please join first.", show_alert=True)


def main() -> None:
    if not TOKEN:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
        return

    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_subscription_button, pattern="^check_subscription$"))

    logger.info("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
