import os
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from io import BytesIO
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import httpx

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("No TELEGRAM_BOT_TOKEN environment variable found. Bot cannot start.")
    
HEALTH_CHECK_PORT = int(os.environ.get("PORT", 8080))  # Default to 8080 if not specified

# Welcome message with emojis
WELCOME_MESSAGE = """
🎵 *Welcome to Music Downloader Bot!* 🎵

I can help you download your favorite music from YouTube. 
Just follow these simple steps:

1️⃣ Send me the name of the song or artist you're looking for
2️⃣ I'll show you matching results
3️⃣ Select the song you want to download
4️⃣ Wait a moment while I prepare your music file
5️⃣ Enjoy your music! 🎧

*Commands:*
/start - Show this welcome message
/help - Get help with using the bot

Created with ❤️ by @zerocreations
"""

# Health check server class
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        # Suppress log messages from health check requests
        return

# Start health check server in a separate thread
def start_health_server():
    server = HTTPServer(('0.0.0.0', HEALTH_CHECK_PORT), HealthCheckHandler)
    logger.info(f"Starting health check server on port {HEALTH_CHECK_PORT}")
    server.serve_forever()

# Function to search YouTube for music
async def search_youtube(query, max_results=5):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'default_search': 'ytsearch',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'socket_timeout': 15,  # Add timeout
        }
        
        search_query = f"ytsearch{max_results}:{query}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            results = []
            if 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        results.append({
                            'title': entry.get('title', 'Unknown'),
                            'duration': entry.get('duration', 0),
                            'url': entry.get('webpage_url', ''),
                            'id': entry.get('id', '')
                        })
            return results
    except Exception as e:
        logger.error(f"Error in search_youtube: {e}")
        return []

# Function to download a YouTube video as MP3
async def download_youtube_audio(url):
    loop = asyncio.get_event_loop()
    buffer = BytesIO()
    
    def download_to_buffer():
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '-',
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'socket_timeout': 30,  # Add timeout
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'music')
                ydl.download([url])
                return title, buffer.getvalue()
        except Exception as e:
            logger.error(f"Error in download_to_buffer: {e}")
            return None, None
    
    try:
        title, audio_data = await loop.run_in_executor(None, download_to_buffer)
        return title, audio_data
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        return None, None

# Start command handler
async def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message and image when the command /start is issued."""
    user = update.effective_user
    
    try:
        # Send welcome image
        try:
            with open('welcome.jpg', 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"👋 Hello {user.first_name}!"
                )
        except FileNotFoundError:
            logger.error("welcome.jpg not found")
            await update.message.reply_text(f"👋 Hello {user.first_name}!")
        
        # Send welcome message
        await update.message.reply_text(
            WELCOME_MESSAGE,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        try:
            await update.message.reply_text(
                "👋 Welcome to Music Downloader Bot! Send me a song name to download music."
            )
        except Exception as inner_e:
            logger.error(f"Failed to send fallback message: {inner_e}")

# Help command handler
async def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "To download music, simply send me the name of the song or artist.\n"
        "I'll search YouTube and show you the results. Then select the song you want to download."
    )

# Handle regular messages (search queries)
async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle the user message."""
    query = update.message.text
    await update.message.reply_text(f"🔍 Searching for: '{query}'...")
    
    results = await search_youtube(query)
    
    if not results:
        await update.message.reply_text("❌ No results found. Please try a different search.")
        return
    
    # Create inline keyboard with search results
    keyboard = []
    for i, result in enumerate(results):
        duration_mins = result['duration'] // 60
        duration_secs = result['duration'] % 60
        button_text = f"{i+1}. {result['title']} ({duration_mins}:{duration_secs:02d})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"download_{result['url']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a song to download:", reply_markup=reply_markup)

# Handle button callbacks
async def button_callback(update: Update, context: CallbackContext) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("download_"):
        url = query.data.replace("download_", "")
        await query.edit_message_text(text=f"⏳ Downloading your music... Please wait.")
        
        # Download the audio
        title, audio_data = await download_youtube_audio(url)
        
        if audio_data:
            # Send the audio file
            audio_file = BytesIO(audio_data)
            audio_file.name = f"{title}.mp3"
            
            await query.message.reply_audio(
                audio=audio_file,
                title=title,
                caption=f"🎵 {title} 🎵\n\nEnjoy your music! 🎧"
            )
            await query.edit_message_text(text=f"✅ Download complete: {title}")
        else:
            await query.edit_message_text(text="❌ Sorry, there was an error downloading this song. Please try another one.")

def main() -> None:
    """Start the bot."""
    try:
        # Create the Application with increased connection pool and timeouts
        application = Application.builder().token(TOKEN).http_version("1.1").get_updates_connection_pool_size(8).connection_pool_size(16).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_callback))

        # Start health check server in a separate thread
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        logger.info(f"Health check server running on port {HEALTH_CHECK_PORT}")

        # Run the bot with proper error handling
        logger.info("Starting the bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES, timeout=60, read_timeout=60, write_timeout=60, connect_timeout=60, pool_timeout=60)
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        # Wait a bit before restarting to avoid rapid restarts
        time.sleep(10)
        # Try again - Koyeb will restart the container if it keeps failing
        main()

if __name__ == "__main__":
    main()
