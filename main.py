import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatJoinRequestHandler,
    ChatMemberHandler,
    filters,
    ContextTypes,
)
from transformers import pipeline

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load a lightweight local text generation / Q&A model without any external API keys
# This downloads and runs inside your host container (Railway)
print("Loading open-source local model...")
qa_pipeline = pipeline("text-generation", model="distilbert/distilgpt2")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting when the user launches /start in private chat."""
    await update.message.reply_text(
        "Hello! I am your channel assistant. Ask me any question or join our channel!"
    )

async def welcome_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcomes users who join via invite links or direct additions."""
    result = update.chat_member
    if result.new_chat_member.status in ["member", "administrator"]:
        user_name = result.new_chat_member.user.first_name
        # Send welcome message to the user privately or in channel
        try:
            await context.bot.send_message(
                chat_id=result.new_chat_member.user.id,
                text=f"Welcome {user_name}! Thanks for joining our channel. Feel free to ask me any question here!"
            )
        except Exception:
            # If private chat isn't opened yet, post welcome in chat
            await context.bot.send_message(
                chat_id=result.chat.id,
                text=f"Welcome to the channel, {user_name}!"
            )

async def handle_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responds to user questions without needing external API keys."""
    user_query = update.message.text
    
    # Indicate typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Generate response using the local huggingface transformer pipeline
        generated = qa_pipeline(
            f"Question: {user_query}\nAnswer:",
            max_new_tokens=50,
            pad_token_id=50256
        )
        response_text = generated[0]["generated_text"].split("Answer:")[-1].strip()
        if not response_text:
            response_text = "I received your question! Let me know if you need specific details."
    except Exception as e:
        response_text = "I received your question! Feel free to ask more details."

    await update.message.reply_text(response_text)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is missing!")

    app = Application.builder().token(token).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatMemberHandler(welcome_chat_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_questions))

    print("Bot is up and running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
