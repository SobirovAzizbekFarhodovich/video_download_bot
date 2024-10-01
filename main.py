import os
import re
import yt_dlp
import instaloader
import time
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

DOWNLOAD_FOLDER = 'downloads'

# Papkani yaratish va ichidagi fayllarni o'chirish
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
else:
    # Papka ichidagi barcha fayllarni o'chirish
    for filename in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"O'chirildi: {file_path}")
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
                print(f"O'chirildi: {file_path}")
        except Exception as e:
            print(f"O'chirishda xato: {e}")

def clear_downloads_folder():
    while True:
        time.sleep(300)  # 5 daqiqa kutish
        if os.path.exists(DOWNLOAD_FOLDER):
            for filename in os.listdir(DOWNLOAD_FOLDER):
                file_path = os.path.join(DOWNLOAD_FOLDER, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"O'chirildi: {file_path}")
                    elif os.path.isdir(file_path):
                        os.rmdir(file_path)
                        print(f"O'chirildi: {file_path}")
                except Exception as e:
                    print(f"O'chirishda xato: {e}")

def download_youtube(link):
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            print(f"Yuklangan video fayl: {filename}")
            return filename
    except Exception as e:
        print(f"Xato: {e}")
        return None

def download_youtube_audio(link):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': '/usr/bin/ffmpeg',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3')
            print(f"Yuklangan audio fayl: {filename}")
            return filename
    except Exception as e:
        print(f"Audio yuklashda xato: {e}")
        return None

def clean_youtube_url(url):
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    match = re.match(youtube_regex, url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(6)}"
    return None

def download_instagram(link, query):
    try:
        loader = instaloader.Instaloader(download_videos=True, download_pictures=False, download_comments=False)

        USERNAME = '__sab1rov_'
        PASSWORD = 'sab1rov'

        loader.login(USERNAME, PASSWORD)

        post_shortcode = link.split("/")[-2]
        post = instaloader.Post.from_shortcode(loader.context, post_shortcode)

        if post.owner_profile.is_private:
            print("Post private, uni yuklash mumkin emas.")
            return None

        loader.download_post(post, target=DOWNLOAD_FOLDER)
        video_file = None

        for file in os.listdir(DOWNLOAD_FOLDER):
            if file.endswith('.mp4'):
                video_file = os.path.join(DOWNLOAD_FOLDER, file)
                break

        if video_file:
            print(f"Instagram video fayli yuklandi: {video_file}")
            return video_file
        else:
            print("Video topilmadi, ehtimol postda faqat rasm bor.")
            return None

    except instaloader.exceptions.ConnectionException as e:
        print(f"Instagram yuklashda xato: {e}")
        return None
    except Exception as e:
        print(f"Instagram yuklashda xato: {e}")
        return None

def show_buttons(update, context, cleaned_url):
    keyboard = [
        [InlineKeyboardButton("Audio", callback_data=f"audio|{cleaned_url}")],
        [InlineKeyboardButton("Video", callback_data=f"video|{cleaned_url}")],
        [InlineKeyboardButton("Video va Audio", callback_data=f"both|{cleaned_url}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Tanlang:', reply_markup=reply_markup)

def button_handler(update, context):
    query = update.callback_query
    query.answer()

    option, url = query.data.split("|")
    query.edit_message_text(text="Yuklanmoqda...")

    if option == "audio":
        audio_filename = download_youtube_audio(url)
        if audio_filename and os.path.exists(audio_filename):
            query.message.reply_audio(open(audio_filename, 'rb'))
        else:
            query.message.reply_text("YouTube audioni yuklab bo'lmadi.")
    
    elif option == "video":
        video_filename = download_youtube(url)
        if video_filename and os.path.exists(video_filename):
            query.message.reply_video(open(video_filename, 'rb'))
        else:
            query.message.reply_text("YouTube videoni yuklab bo'lmadi.")
    
    elif option == "both":
        video_filename = download_youtube(url)
        audio_filename = download_youtube_audio(url)
        
        if video_filename and os.path.exists(video_filename):
            query.message.reply_video(open(video_filename, 'rb'))
        else:
            query.message.reply_text("YouTube videoni yuklab bo'lmadi.")
        
        if audio_filename and os.path.exists(audio_filename):
            query.message.reply_audio(open(audio_filename, 'rb'))
        else:
            query.message.reply_text("YouTube audioni yuklab bo'lmadi.")

def handle_message(update, context):
    text = update.message.text
    cleaned_url = clean_youtube_url(text)
    
    if cleaned_url:
        print(f"To'g'ri YouTube URL: {cleaned_url}")
        show_buttons(update, context, cleaned_url)
    elif "instagram.com" in text:
        update.message.reply_text("Yuklanmoqda...")
        filename = download_instagram(text, update.message)
        if filename and os.path.exists(filename):
            update.message.reply_video(open(filename, 'rb'))
        else:
            update.message.reply_text("Instagram postini yuklab bo'lmadi.")
    else:
        update.message.reply_text("Yaroqli link kiriting.")

def main():
    threading.Thread(target=clear_downloads_folder, daemon=True).start()

    updater = Updater('7609118292:AAFzNe3eECU9fUm7Z2SIAU2tjcsoGGhn3Ug', use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
