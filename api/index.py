import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from PIL import Image
import io
from pyzbar.pyzbar import decode

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize Telegram Bot
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Command handler for /start
def start(update, context):
    update.message.reply_text(
        "Hi! I'm a barcode scanner bot. Send me an image containing a barcode "
        "(e.g., Code 128, Code 39, or EAN-13/UPC-12 made with Libre Barcode font), "
        "and I'll decode it for you."
    )

# Handler for processing images
def handle_image(update, context):
    try:
        # Get the photo from the message
        photo = update.message.photo[-1]  # Get the highest resolution photo
        file = photo.get_file()
        file_bytes = file.download_as_bytearray()

        # Open image with PIL
        image = Image.open(io.BytesIO(file_bytes))

        # Decode barcode
        barcodes = decode(image)
        if barcodes:
            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")
                barcode_type = barcode.type
                update.message.reply_text(
                    f"Barcode detected!\nType: {barcode_type}\nData: {barcode_data}"
                )
        else:
            update.message.reply_text("No barcode found in the image.")
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        update.message.reply_text("Sorry, I couldn't process the image. Please try again.")

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.PHOTO, handle_image))

@app.post("/webhook")
async def webhook(request: Request):
    try:
        # Get the JSON payload from Telegram
        update = Update.de_json(await request.json(), bot)
        await dispatcher.process_update(update)
        return {"message": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"message": "error"}, 500

@app.get("/")
async def index():
    return {"message": "Hello World"}