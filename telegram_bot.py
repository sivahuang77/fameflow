import logging
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Import the core logic module
import core_logic

# --- Constants ---
TELEGRAM_TOKEN = "8208040651:AAG9a5tZKNO5dgsTDPjMJXrWlnPOLpgNPSo"
DB_PATH = 'influencers.db'

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Telegram-Specific Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "您好！我是您的 AI 經紀人助理。\n"
        "[注意] 目前 AI 大腦處於離線模式，僅供測試。\n"
        "如果您是初次使用，請使用 `/register [您的名字]` 來綁定身份。"
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    try:
        name = ' '.join(context.args)
        if not name:
            await update.message.reply_text("請在指令後方加上您的名字，例如: `/register 小花 (Flora)`")
            return

        conn = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM influencers WHERE name = ?", (name,))
        if not cursor.fetchone():
            await update.message.reply_text(f"在資料庫中找不到名為 '{name}' 的資料。")
            conn.close()
            return

        cursor.execute("UPDATE influencers SET telegram_id = ? WHERE name = ?", (user_id, name))
        conn.commit()
        if cursor.rowcount > 0:
            await update.message.reply_text(f"歡迎您，{name}！您的身份已成功綁定。")
        else:
            await update.message.reply_text(f"看起來您已經綁定為 {name} 了。")
        conn.close()
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        await update.message.reply_text(f"註冊過程中發生錯誤: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    response_text = core_logic.process_message(
        user_identifier=user_id, message_text=user_message, platform='telegram'
    )
    if response_text:
        await update.message.reply_text(response_text)

# --- Main Application Setup ---
def main() -> None:
    """Starts the Telegram bot connector with the standard application builder."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Telegram Connector is running... Press Ctrl-C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()