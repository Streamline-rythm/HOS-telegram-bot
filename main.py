import os
import uvicorn
import asyncio
import requests
from fastapi import FastAPI
from telegram import Update
from dotenv import load_dotenv
from pydantic import BaseModel
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

# Store the last reply in memory (for demo purposes)
last_reply = {}

class FirstDataFromScenario(BaseModel):
    "message_id": str,
    "name": str,
    "phone_number": str,
    "thread_id": str,
    "airtable_record_id": str

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.reply_to_message:
        replied_id = update.message.reply_to_message.message_id
        user = update.message.from_user.full_name
        reply_text = update.message.text
        last_reply[replied_id] = {"user": user, "text": reply_text}

# Start the bot in the background
async def start_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await asyncio.Event().wait()

# Define lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(start_bot())  # Start the bot
    yield  # Wait here while the app runs
    # Optionally: add any shutdown logic here

# Create FastAPI app with lifespan
app = FastAPI(
    title="Telegram Message Retriever",
    description="API to retrieve replied messages from Telegram",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/get_replied_message")
async def get_replied_message(first_data_from_scenario: FirstDataFromScenario):
    message_id = first_data_from_scenario["message_id"]
    name = first_data_from_scenario["name"]
    phone_number = first_data_from_scenario["phone_number"]
    thread_id = first_data_from_scenario["thread_id"]
    airtable_record_id = first_data_from_scenario["airtable_record_id"]

    while(True):
        reply = last_reply.get(message_id)
        if reply and "checking" in reply["text"].lower():
            # print(f"last_reply: {last_reply}")
            telegram_content = reply["text"]
            body = {
                "message_id": message_id,
                "telegram_content": telegram_content,
                "name": name,
                "phone_number": phone_number,
                "thread_id": thread_id,
                "airtable_record_id": airtable_record_id
            }

            requests.post(url='https://hook.us2.make.com/vqinhxh6v9m8cf7yuhdeqrdxotvl3k7f', json=body)
            
        await asyncio.sleep(3)  
        # Wait and retry

@app.get("/get_replied_message_again")
async def get_replied_message_again(
    message_id: int = Query(..., description="The ID of the message"),
):
    for i in range(10):
        reply = last_reply.get(message_id)
        if reply and "checking" not in reply["text"].lower():
            return reply
        await asyncio.sleep(2)  
        # Wait and retry
    return {
        "text": "not found"
    }

@app.get("/test")
async def test():
    return {"result": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, proxy_headers=True,)
