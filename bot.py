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
    # ইউজার টেবিল
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, username TEXT, name TEXT, balance REAL, 
                       completed_tasks INTEGER, pending_tasks INTEGER, referrer_id INTEGER)''')
    # সেটিংস টেবিল
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
                      (key TEXT PRIMARY KEY, value TEXT)''')
    # টাস্ক হিস্ট্রি টেবিল
    cursor.execute('''CREATE TABLE IF NOT EXISTS task_history 
                      (user_id INTEGER, login_name TEXT PRIMARY KEY, status TEXT)''')
    # একটিভ সেশন টেবিল
    cursor.execute('''CREATE TABLE IF NOT EXISTS active_sessions
                      (user_id INTEGER PRIMARY KEY, start_time REAL, current_login TEXT)''')
    
    # ডিফল্ট অ্যাডমিন সেটিংস ভ্যালু (যদি আগে থেকে না থাকে)
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('task_name', '📱 Create Inst (2FA)')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('task_desc', 'In this task, you must create a new Inst acc using only a real mobile device.')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('task_password', 'EPAp1Wr7S0')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('task_reward', '0.0200')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_time', '1')")       # ডিফল্ট ১ মিনিট
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_percent', '100')")  # ডিফল্ট ১০০%
    conn.commit()
    conn.close()

init_db()

# ⚙️ ডাটাবেজ হেল্পার ফাংশন
def get_setting(key, default_value):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default_value

def set_setting(key, value):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def check_join(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return True

def join_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
    markup.add(types.InlineKeyboardButton("✅ Joined / Check", callback_data="check_subscription"))
    return markup

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("💰 Balance"), types.KeyboardButton("📋 Tasks"),
        types.KeyboardButton("📤 Withdraw"), types.KeyboardButton("👤 Profile"),
        types.KeyboardButton("🏆 Top"), types.KeyboardButton("👥 My Referrals")
    )
    return markup

# 🚀 /start
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    username = message.from_user.username or "নাই"
    name = message.from_user.first_name
    
    if not check_join(user_id):
        bot.send_message(user_id, "❌ বাটনগুলো ব্যবহার করতে প্রথমে আমাদের চ্যানেলে জয়েন করুন।", reply_markup=join_keyboard())
        return

    text_args = message.text.split()
    referrer = None
    if len(text_args) > 1 and text_args[1].isdigit():
        referrer = int(text_args[1])
        if referrer == user_id: referrer = None

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, 0.0010, 0, 0, ?)", (user_id, username, name, referrer))
        conn.commit()
        if referrer:
            cursor.execute("UPDATE users SET balance = balance + 0.0400 WHERE id=?", (referrer,))
            conn.commit()
            try: bot.send_message(referrer, "👥 আপনার লিংকে একজন নতুন ইউজার জয়েন করেছে! আপনি বোনাস পেয়েছেন।")
            except: pass
    conn.close()
    bot.send_message(user_id, "বটে আপনাকে স্বাগতম!", reply_markup=main_menu())

# 👑 এডমিন প্যানেল কন্ট্রোল
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != TASK_ADMIN: return
    
    t_name = get_setting('task_name', '📱 Create Inst (2FA)')
    t_reward = get_setting('task_reward', '0.0200')
    t_pass = get_setting('task_password', 'EPAp1Wr7S0')
    auto_t = get_setting('auto_time', '1')
    auto_p = get_setting('auto_percent', '100')
    
    admin_msg = (
        f"🛠️ **Dynamic Admin Control Panel** 🛠️\n\n"
        f"📝 **Task Name:** `{t_name}`\n"
        f"💰 **Reward:** `${t_reward}`\n"
        f"🔑 **Password:** `{t_pass}`\n"
        f"⏱️ **Auto-Approve Time:** `{auto_t} Minute(s)`\n"
        f"📊 **Auto-Approve Chance:** `{auto_p}%` (বাকি {100-int(auto_p)}% রিজেক্ট)\n\n"
        f"নিচের বাটনগুলো দিয়ে লাইভ কন্ট্রোল করুন:"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📝 Change Task Name", callback_data="adm_change_name"),
        types.InlineKeyboardButton("📄 Change Task Description", callback_data="adm_change_desc"),
        types.InlineKeyboardButton("🔑 Change Task Password", callback_data="adm_change_pass"),
        types.InlineKeyboardButton("💵 Change Task Reward", callback_data="adm_change_reward"),
        types.InlineKeyboardButton("⏱️ Change Auto-Approve Time (Minutes)", callback_data="adm_change_autotime"),
        types.InlineKeyboardButton("📊 Change Auto-Approve % (0-100)", callback_data="adm_change_autopercent")
    )
    bot.send_message(TASK_ADMIN, admin_msg, reply_markup=markup, parse_mode="Markdown")

# 📑 বাটন হ্যান্ডলার
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.chat.id
    text = message.text
    
    if not check_join(user_id):
        bot.send_message(user_id, "❌ চ্যানেলে জয়েন করুন!", reply_markup=join_keyboard())
        return

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance, completed_tasks, pending_tasks FROM users WHERE id=?", (user_id,))
    user_info = cursor.fetchone()
    
    if not user_info:
        conn.close()
        return
    balance, completed, pending = user_info

    if text == "💰 Balance":
        bot.send_message(user_id, f"💰 Your balance: ${balance:.4f}")
        
    elif text == "📋 Tasks":
        t_name = get_setting('task_name', '📱 Create Inst (2FA)')
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(t_name, callback_data="display_task_details"))
        bot.send_message(user_id, "👇 Please select a task:", reply_markup=markup)
        
    elif text == "📤 Withdraw":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("বিকাশ", callback_data="w_bkash"), types.InlineKeyboardButton("USDT", callback_data="w_usdt"))
        bot.send_message(user_id, "📤 Withdraw মাধ্যম সিলেক্ট করুন:", reply_markup=markup)
        
    elif text == "👤 Profile":
        profile_msg = f"👤 **YOUR PROFILE**\n\n💰 Balance: {balance:.4f} USDT\n✅ Completed: {completed}\n⏳ Pending: {pending}"
        bot.send_message(user_id, profile_msg, parse_mode="Markdown")
        
    elif text == "🏆 Top":
        cursor.execute("SELECT name, balance FROM users ORDER BY balance DESC LIMIT 10")
        top_users = cursor.fetchall()
        top_msg = "🏆 **Top Leaders:**\n\n"
        for i, u in enumerate(top_users, 1): top_msg += f"{i}. {u[0]} - ${u[1]:.4f}\n"
        bot.send_message(user_id, top_msg, parse_mode="Markdown")
        
    elif text == "👥 My Referrals":
        cursor.execute("SELECT COUNT(id) FROM users WHERE referrer_id=?", (user_id,))
        ref_count = cursor.fetchone()[0]
        ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        bot.send_message(user_id, f"👥 Refer Link: {ref_link}\nTotal Referrals: {ref_count}")
        
    conn.close()

# 🔴 ইনলাইন বাটন কন্ট্রোল
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    
    if call.data == "check_subscription":
        if check_join(user_id):
            bot.send_message(user_id, "✅ মেনু সচল হয়েছে।", reply_markup=main_menu())
            try: bot.delete_message(user_id, call.message.message_id)
            except: pass
        else:
            bot.answer_callback_query(call.id, "❌ জয়েন করা হয়নি!", show_alert=True)
        return

    # এডমিন চেঞ্জেস হ্যান্ডলিং
    if call.from_user.id == TASK_ADMIN:
        if call.data == "adm_change_name":
            msg = bot.send_message(TASK_ADMIN, "✍️ টাস্কের নতুন বাটন নাম দিন:")
            bot.register_next_step_handler(msg, lambda m: [set_setting('task_name', m.text), bot.send_message(TASK_ADMIN, "✅ বাটন নাম আপডেট হয়েছে।")])
            return
        elif call.data == "adm_change_desc":
            msg = bot.send_message(TASK_ADMIN, "✍️ টাস্কের নতুন বিস্তারিত ডেসক্রিপশন লিখুন:")
            bot.register_next_step_handler(msg, lambda m: [set_setting('task_desc', m.text), bot.send_message(TASK_ADMIN, "✅ ডেসক্রিপশন আপডেট হয়েছে।")])
            return
        elif call.data == "adm_change_pass":
            msg = bot.send_message(TASK_ADMIN, "✍️ নতুন পাসওয়ার্ড লিখুন:")
            bot.register_next_step_handler(msg, lambda m: [set_setting('task_password', m.text), bot.send_message(TASK_ADMIN, "✅ পাসওয়ার্ড আপডেট হয়েছে।")])
            return
        elif call.data == "adm_change_reward":
            msg = bot.send_message(TASK_ADMIN, "✍️ নতুন রিওয়ার্ড এমাউন্ট দিন (যেমন: 0.025):")
            bot.register_next_step_handler(msg, lambda m: [set_setting('task_reward', m.text), bot.send_message(TASK_ADMIN, "✅ রিওয়ার্ড আপডেট হয়েছে।")])
            return
        elif call.data == "adm_change_autotime":
            msg = bot.send_message(TASK_ADMIN, "✍️ কত মিনিট পর অটো-অ্যাপ্রুভ চালু হবে? শুধু সংখ্যা লিখুন (যেমন: ১ মিনিট চাইলে লিখবেন `1`, ৫ মিনিট চাইলে `5`):")
            bot.register_next_step_handler(msg, save_auto_time)
            return
        elif call.data == "adm_change_autopercent":
            msg = bot.send_message(TASK_ADMIN, "✍️ ১০০% এর মধ্যে কত পারসেন্ট অটো-অ্যাপ্রুভ করতে চান? শুধু সংখ্যা দিন (যেমন: ৬০% চাইলে `60`, ১০০% চাইলে `100`):")
            bot.register_next_step_handler(msg, save_auto_percent)
            return

    if call.data == "display_task_details":
        t_name = get_setting('task_name', '📱 Create Inst (2FA)')
        t_desc = get_setting('task_desc', '')
        task_txt = f"📋 **Task:** {t_name}\n\n📄 **Description:** {t_desc}\n\n❗ইউজার ইনফো না মিললে রিজেক্ট করা হবে।"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("▶️ Start", callback_data="task_start"), types.InlineKeyboardButton("❌ Cancel", callback_data="task_cancel"))
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=task_txt, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "task_cancel":
        bot.send_message(user_id, "👍 কাজটি বাতিল করা হয়েছে।")

    elif call.data == "task_start":
        admin_pass = get_setting('task_password', 'EPAp1Wr7S0')
        first_names = ["Palma", "Suraj", "John", "Monira", "Rony", "Tariq", "Siam", "Nadia"]
        last_names = ["Ahmed", "Priti", "Das", "Khan", "Hasan", "Zaman", "Chowdhury", "Akter"]
        r_f = random.choice(first_names)
        r_l = random.choice(last_names)
        
        full_name = f"{r_f} {r_l}"
        login_name = f"{r_f.lower()}{r_l.lower()}{random.randint(1000,9999)}"
        
        # সেশন টাইম এবং লগইন নেম ট্র্যাক করা হচ্ছে
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO active_sessions VALUES (?, ?, ?)", (user_id, time.time(), login_name))
        conn.commit()
        conn.close()
        
        task_info = (
            f"First name: `{full_name}`\n"
            f"Login: `{login_name}`\n"
            f"Password: `{admin_pass}`\n\n"
            f"💡 *লেখার ওপর ক্লিক করলেই কপি হয়ে যাবে!*\n"
            f"👉 সাবমিট করতে নিচের বাটনে চাপুন:"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📥 Get 2fa key", callback_data="process_get_2fa"))
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=task_info, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "process_get_2fa":
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT current_login FROM active_sessions WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            bot.answer_callback_query(call.id, "❌ সেশন পাওয়া যায়নি। টাস্কটি পুনরায় শুরু করুন।", show_alert=True)
            return
            
        login_name = row[0]

        # 🛑 ডাবল সাবমিশন প্রтеক্ট চেক
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM task_history WHERE login_name=?", (login_name,))
        already_exists = cursor.fetchone()
        conn.close()
        
        if already_exists:
            bot.answer_callback_query(call.id, "❌ এই টাস্কটি অলরেডি একবার সাবমিট করা হয়ে গেছে!", show_alert=True)
            return

        msg = bot.send_message(user_id, "পিলিজ আপনার 2fa key দেন:")
        bot.register_next_step_handler(msg, save_and_notify_admin, login_name)

    # ম্যানুয়াল এডমিন অ্যাপ্রুভ/রিজেক্ট
    elif call.data.startswith("adm_app_") and call.from_user.id == TASK_ADMIN:
        target_uid = int(call.data.split("_")[2])
        msg_text = call.message.text
        l_name = "unknown"
        for line in msg_text.split('\n'):
            if "Login:" in line: l_name = line.split("Login:")[1].strip().replace('`', '')
        approve_task(target_uid, l_name, call.message)
        
    elif call.data.startswith("adm_rej_") and call.from_user.id == TASK_ADMIN:
        target_uid = int(call.data.split("_")[2])
        msg_text = call.message.text
        l_name = "unknown"
        for line in msg_text.split('\n'):
            if "Login:" in line: l_name = line.split("Login:")[1].strip().replace('`', '')
        reject_task(target_uid, l_name, call.message)

    elif call.data == "w_bkash":
        msg = bot.send_message(user_id, "📱 আপনার বিকাশ নম্বরটি দিন:")
        bot.register_next_step_handler(msg, lambda m: bot.register_next_step_handler(bot.send_message(user_id, "পরিমাণ দিন:"), process_bkash_withdraw, m.text))
        
    elif call.data == "w_usdt":
        msg = bot.send_message(user_id, "📤 Enter your USDT (BEP-20) address:")
        bot.register_next_step_handler(msg, lambda m: bot.register_next_step_handler(bot.send_message(user_id, "Enter Amount:"), process_usdt_withdraw, m.text))

# 🛠️ এডমিন ডায়নামিক সেটিংস সেভ ফাংশনসমূহ
def save_auto_time(message):
    if message.chat.id != TASK_ADMIN: return
    try:
        minutes = int(message.text)
        set_setting('auto_time', minutes)
        bot.send_message(TASK_ADMIN, f"✅ সফলভাবে অটো-অ্যাপ্রুভ টাইম `{minutes}` মিনিট সেট করা হয়েছে।")
    except:
        bot.send_message(TASK_ADMIN, "❌ ভুল ইনপুট! শুধুমাত্র সংখ্যা লিখুন।")

def save_auto_percent(message):
    if message.chat.id != TASK_ADMIN: return
    try:
        percentage = int(message.text)
        if 0 <= percentage <= 100:
            set_setting('auto_percent', percentage)
            bot.send_message(TASK_ADMIN, f"✅ সফলভাবে অটো-অ্যাপ্রুভ হার `{percentage}%` সেট করা হয়েছে।")
        else:
            bot.send_message(TASK_ADMIN, "❌ ভুল ইনপুট! ০ থেকে ১০০ এর মধ্যে যেকোনো সংখ্যা দিন।")
    except:
        bot.send_message(TASK_ADMIN, "❌ ভুল ইনপুট! শুধুমাত্র সংখ্যা লিখুন।")

# 🛠️ টাস্ক সেভ ও ডায়নামিক অটো অ্যাপ্রুভ/রিজেক্ট প্রসেসিং লজিক
def save_and_notify_admin(message, login_name):
    user_id = message.chat.id
    user_2fa = message.text
    username = message.from_user.username or "নাই"
    admin_pass = get_setting('task_password', 'EPAp1Wr7S0')
    
    # টাস্ক ডাবল সাবমিশন ডাটাবেজ লক
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO task_history VALUES (?, ?, 'pending')", (user_id, login_name))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        bot.send_message(user_id, "❌ এই টাস্ক অ্যাকাউন্ট অলরেডি সিস্টেমে সাবমিট করা আছে।")
        return

    # টাইম ডিফারেন্স চেক
    cursor.execute("SELECT start_time FROM active_sessions WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    start_time = row[0] if row else time.time()
    conn.close()
    
    time_taken = time.time() - start_time
    
    # এডমিন প্যানেল থেকে সেট করা ডায়নামিক সেটিংস লোড করা হচ্ছে
    admin_set_minutes = int(get_setting('auto_time', '1'))
    admin_set_percent = int(get_setting('auto_percent', '100'))
    limit_seconds = admin_set_minutes * 60

    # ⏱️ ডায়নামিক লজিক: ইউজার যদি এডমিনের সেট করা সময়ের চেয়ে বেশি দেরি করে জমা দেয়
    if time_taken > limit_seconds:
        chance = random.randint(1, 100)
        if chance <= admin_set_percent:
            # ডায়নামিক পারসেন্টে অটো অ্যাপ্রুভ
            reward_amount = float(get_setting('task_reward', '0.0200'))
            conn = sqlite3.connect('bot_data.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET balance = balance + ?, completed_tasks = completed_tasks + 1 WHERE id=?", (reward_amount, user_id))
            cursor.execute("UPDATE task_history SET status='approved' WHERE login_name=?", (login_name,))
            conn.commit()
            conn.close()
            bot.send_message(user_id, f"✅ (Auto-Approved) নির্ধারিত সময়ের পর সাবমিট করায় সিস্টেম চেক করে আপনার কাজটি সফল করেছে! ব্যালেন্স +${reward_amount:.4f} যোগ করা হয়েছে।")
        else:
            # বাকি পারসেন্টে অটো রিজেক্ট
            conn = sqlite3.connect('bot_data.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE task_history SET status='rejected' WHERE login_name=?", (login_name,))
            conn.commit()
            conn.close()
            bot.send_message(user_id, "❌ (Auto-Rejected) নির্ধারিত সময়ের পর সাবমিট করায় সিস্টেম চেক করে আপনার কাজটি রিজেক্ট করেছে।")
        return

    # ⏳ নির্ধারিত সময়ের আগে সাবমিট করলে নরমাল অ্যাডমিন রিভিউতে যাবে
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET pending_tasks = pending_tasks + 1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    bot.send_message(user_id, "✅ Your report has been received! Please wait for Admin review.")
    
    admin_msg = (
        f"📥 **নতুন টাস্ক রিভিউ রিকোয়েস্ট**\n\n"
        f"👤 ইউজার: {message.from_user.first_name}\n"
        f"🆔 আইডি: `{user_id}`\n\n"
        f"🔐 Login: `{login_name}`\n"
        f"🔑 Password: `{admin_pass}`\n"
        f"🗝️ 2FA Key: `{user_2fa}`"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Approve ✅", callback_data=f"adm_app_{user_id}"),
        types.InlineKeyboardButton("Reject ❌", callback_data=f"adm_rej_{user_id}")
    )
    try: bot.send_message(TASK_ADMIN, admin_msg, reply_markup=markup, parse_mode="Markdown")
    except: pass

# ম্যানুয়াল অ্যাপ্রুভ ফাংশন (ডাবল ক্লিক প্রোটেক্টেড)
def approve_task(target_uid, l_name, message):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM task_history WHERE login_name=?", (l_name,))
    current_status = cursor.fetchone()
    
    if current_status and current_status[0] == 'approved':
        conn.close()
        bot.send_message(TASK_ADMIN, "⚠️ এই টাস্কটি অলরেডি একবার Approve করা হয়ে গেছে!")
        return

    reward_amount = float(get_setting('task_reward', '0.0200'))
    cursor.execute("UPDATE users SET balance = balance + ?, completed_tasks = completed_tasks + 1, pending_tasks = pending_tasks - 1 WHERE id=?", (reward_amount, target_uid))
    cursor.execute("UPDATE task_history SET status='approved' WHERE login_name=?", (l_name,))
    conn.commit()
    conn.close()
    
    bot.send_message(target_uid, f"✅ আপনার কাজটি সফল হয়েছে এবং ব্যালেন্স +${reward_amount:.4f} যোগ করা হয়েছে!")
    bot.edit_message_text(chat_id=TASK_ADMIN, message_id=message.message_id, text=f"{message.text}\n\n🟢 APPROVED BY ADMIN")

# ম্যানুয়াল রিজেক্ট ফাংশন
def reject_task(target_uid, l_name, message):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET pending_tasks = pending_tasks - 1 WHERE id=?", (target_uid,))
    cursor.execute("UPDATE task_history SET status='rejected' WHERE login_name=?", (l_name,))
    conn.commit()
    conn.close()
    
    bot.send_message(target_uid, "❌ আপনার কাজটি রিজেক্ট করা হয়েছে।")
    bot.edit_message_text(chat_id=TASK_ADMIN, message_id=message.message_id, text=f"{message.text}\n\n🔴 REJECTED BY ADMIN")

# উইথড্র প্রসেসিং
def process_bkash_withdraw(message, bkash_num):
    user_id = message.chat.id
    try: amount = float(message.text)
    except: return
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    balance = cursor.fetchone()[0]
    if amount < 0.20 or amount > balance:
        bot.send_message(user_id, "❌ পর্যাপ্ত ব্যালেন্স নাই বা ভুল এমাউন্ট।")
    else:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, user_id))
        conn.commit()
        bot.send_message(user_id, "⏳ উইথড্র রিকোয়েস্ট পেন্ডিং রয়েছে।")
        bot.send_message(WITHDRAW_ADMIN, f"💰 **বিকাশ উইথড্র!**\nID: `{user_id}`\nনম্বর: {bkash_num}\nপরিমাণ: ${amount}")
    conn.close()

def process_usdt_withdraw(message, address):
    user_id = message.chat.id
    try: amount = float(message.text)
    except: return
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    balance = cursor.fetchone()[0]
    if amount < 0.20 or amount > balance:
        bot.send_message(user_id, "❌ পর্যাপ্ত ব্যালেন্স নাই বা ভুল এমাউন্ট।")
    else:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, user_id))
        conn.commit()
        bot.send_message(user_id, "⏳ উইথড্র পেন্ডিং।")
        bot.send_message(WITHDRAW_ADMIN, f"💰 **USDT উইথড্র!**\nID: `{user_id}`\nАдрес: `{address}`\nপরিমাণ: ${amount}")
    conn.close()

bot.infinity_polling()
