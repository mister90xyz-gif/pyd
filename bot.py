import os
import telebot
from telebot import types
from dotenv import load_dotenv
import yt_dlp

# .env ফাইল থেকে টোকেন লোড করা
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)

# ইউজার যখন /start দিবে
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "স্বাগতম! আমাকে কোনো ভিডিওর লিংক দিন, আমি ডাউনলোড করে দেব।")

# লিংক হ্যান্ডেল করার জন্য
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if "http" in url:
        # বাটন তৈরি করা (Audio / Video)
        markup = types.InlineKeyboardMarkup()
        btn_audio = types.InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"audio|{url}")
        btn_video = types.InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"video|{url}")
        markup.add(btn_audio, btn_video)
        
        bot.reply_to(message, "ফরম্যাট সিলেক্ট করুন:", reply_markup=markup)
    else:
        bot.reply_to(message, "দয়া করে একটি সঠিক লিংক দিন।")

# বাটন ক্লিক হ্যান্ডেল করা
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    action, url = call.data.split("|", 1)
    
    bot.answer_callback_query(call.id, "ডাউনলোড শুরু হচ্ছে... অপেক্ষা করুন।")
    bot.edit_message_text(f"ডাউনলোড হচ্ছে... ({action})", call.message.chat.id, call.message.message_id)

    try:
        file_path = download_media(url, action)
        
        # ফাইল আপলোড করা
        bot.edit_message_text("আপলোড হচ্ছে...", call.message.chat.id, call.message.message_id)
        
        with open(file_path, 'rb') as file:
            if action == "audio":
                bot.send_audio(call.message.chat.id, file)
            else:
                bot.send_video(call.message.chat.id, file)
        
        # কাজ শেষে ফাইল ডিলিট এবং মেসেজ আপডেট
        os.remove(file_path)
        bot.edit_message_text("ডাউনলোড সম্পন্ন! ✅", call.message.chat.id, call.message.message_id)

    except Exception as e:
        bot.send_message(call.message.chat.id, f"ত্রুটি হয়েছে: {str(e)}")
        # এরর হলে ফাইলটি ক্লিন করা (যদি থাকে)
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

# yt-dlp দিয়ে ডাউনলোড ফাংশন
def download_media(url, type):
    ydl_opts = {}
    
    if type == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
    else: # video
        ydl_opts = {
            'format': 'best[ext=mp4]', # MP4 ফরম্যাট এর জন্য
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        
        if type == "audio":
            # অডিও কনভার্ট হওয়ার পর এক্সটেনশন mp3 হয়ে যায়
            filename = os.path.splitext(filename)[0] + ".mp3"
            
        return filename

# বট চালু রাখা
print("Bot is running...")
bot.infinity_polling()
