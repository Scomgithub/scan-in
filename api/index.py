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
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is missing")
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
        
        # Open image with PIL, explicitly setting format to avoid imghdr
        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Convert to RGB if needed (some barcode formats require it)
            if image.mode != "RGB":
                image = image.convert("RGB")
        except Exception as e:
            logger.error(f"Error opening image: {e}")
            update.message.reply_text("Failed to process the image. Please ensure it's a valid image file.")
            return

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
        update = Update.de_json(await request.json(), bot)
        if update is None:
            logger.error("Invalid update received")
            return {"message": "invalid update"}, 400
        await dispatcher.process_update(update)
        return {"message": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"message": str