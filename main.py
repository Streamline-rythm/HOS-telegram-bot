import os
import uvicorn
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from fastapi import FastAPI, HTTPException, Query
import asyncio
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

# Store the last reply in memory (for demo purposes)
last_reply = {}

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

@app.get("/get_replied_message")
async def get_replied_message(
    message_id: int = Query(..., description="The ID of the message")
):
    for i in range(120):
        reply = last_reply.get(message_id)
        if reply and "checking" in reply["text"].lower():
            # print(f"last_reply: {last_reply}")
            return reply
        await asyncio.sleep(1)  
        # Wait and retry
    return {
        "text": "not found"
    }

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
