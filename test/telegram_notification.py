import os

import telebot

TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

bot = telebot.TeleBot(TOKEN)


if __name__ == "__main__":
    if TOKEN and CHAT_ID:
        bot.send_document(CHAT_ID, open(os.path.join(BASE_DIR, "report.html"), "rb"))
