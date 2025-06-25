import os
import asyncio
import requests
import json
from telegram import Update
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

load_dotenv()

PERSISTENCE_FILE = "last_reply.json"

BOT_TOKEN = os.getenv("BOT_TOKEN")
PERSONAL_TOKEN = os.getenv("PERSONAL_TOKEN")
BASE_ID = os.getenv("BASE_ID")
TABLE_ID = os.getenv("TABLE_ID")

BASE_URL = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'

headers = {
    'Authorization': f'Bearer {PERSONAL_TOKEN}',
    'Content-Type': 'application/json'
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.reply_to_message:
        reply_text = update.message.text
        chat_id = str(update.message.chat_id)  # Use string keys for JSON compatibility
        user = update.message.from_user.full_name
        replied_id = str(update.message.reply_to_message.message_id)

        data = {
            "fields": {
                "chat_id": chat_id,
                "user": user,
                "replied_id": replied_id,
                "chat_text": reply_text
            }
        }

        response = requests.post(BASE_URL, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200 or response.status_code == 201:
            print("Record saved successfully!") 
            print(response.json())
        else:
            print(f"Failed to save record: {response.status_code} - {response.text}")

async def start_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("Bot started. Listening for messages...")
    await asyncio.Event().wait()  # Keep running forever

if __name__ == "__main__":
    asyncio.run(start_bot())
