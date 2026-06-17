import telebot
from telebot import types
import sqlite3
import random
import time

# 🔑 বট টোকেন
TOKEN = '8985929984:AAF23m2CD0DEYWsQfXD-0yMABQxMAFZu-Lc'
bot = telebot.TeleBot(TOKEN)

# 📢 টেলিগ্রাম চ্যানেল তথ্য
CHANNEL_USERNAME = '@tasbot100'
CHANNEL_LINK = 'https://t.me/tasbot100'

# 👑 অ্যাডমিন আইডি সেটিংস
WITHDRAW_ADMIN = 7916255597
TASK_ADMIN = 7953282546

# 🗄️ ডাটাবেজ সেটআপ
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY, username TEXT, name TEXT, balance REAL,
                       completed_tasks INTEGER, pending_tasks INTEGER, referrer_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings
                      (key TEXT PRIMARY KEY, value TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS task_history
                      (user_id INTEGER, login_name TEXT PRIMARY KEY, status TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS active_sessions
                      (user_id INTEGER PRIMARY KEY, start_time REAL, current_login TEXT)''')

    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('task_name', '📱 Create Inst (2FA)')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('task_desc', 'In this task, you must create a new Inst acc using only a real mobile device.')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('task_password', 'EPAp1Wr7S0')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('task_reward', '0.0200')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_time', '1')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_percent', '100')")
    conn.commit()
    conn.close()

init_db()

def check_join(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return True

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    if not check_join(user_id):
        bot.send_message(user_id, "❌ চ্যানেলে জয়েন করুন!")
        return
    bot.send_message(user_id, "বট এখন অনলাইন!")

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    bot.send_message(message.chat.id, "বট কাজ করছে!")

bot.infinity_polling()