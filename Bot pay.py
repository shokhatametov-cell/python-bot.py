import telebot
from telebot import types
import sqlite3

# ===== CONFIG =====
TOKEN = "SENING_BOT_TOKENING"  # <-- bot tokeningiz
ADMIN = 1896321851  # <-- admin ID
CHANNELS = ["@shokh_vss", "@shokh_news"]  # <-- majburi obuna kanallari
GROUPS = ["@shokh_group", "@shokh_chat"]  # <-- majburi obuna guruhlari

# ===== DATABASE =====
conn = sqlite3.connect("startup.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    invited_by INTEGER,
    premium INTEGER DEFAULT 0,
    invited_count INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS invites(
    invited_user INTEGER UNIQUE,
    inviter INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT
)
""")
conn.commit()

# ===== HELPERS =====
def log(uid, action):
    cursor.execute("INSERT INTO logs(user_id, action) VALUES(?,?)",(uid,action))
    conn.commit()

def get_user(uid):
    cursor.execute("SELECT * FROM users WHERE user_id=?",(uid,))
    return cursor.fetchone()

def add_user(uid, ref=None):
    if not get_user(uid):
        cursor.execute("INSERT INTO users(user_id, invited_by) VALUES(?,?)",(uid,ref))
        conn.commit()
        if ref and ref != uid:
            cursor.execute("SELECT * FROM invites WHERE invited_user=?", (uid,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO invites VALUES(?,?)",(uid,ref))
                cursor.execute("UPDATE users SET points=points+1, coins=coins+1, referrals=referrals+1 WHERE user_id=?",(ref,))
                conn.commit()
                log(ref, f"+1 referral from {uid}")

def add_points(uid, points):
    cursor.execute("UPDATE users SET points=points+?, coins=coins+? WHERE user_id=?",(points, points, uid))
    conn.commit()

def check_sub(uid):
    for ch in CHANNELS + GROUPS:
        try:
            m = bot.get_chat_member(ch, uid)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"❌ Subscription error: {e}")
            return False
    return True

# ===== MENU =====
def join_menu(uid):
    kb = types.InlineKeyboardMarkup()
    for ch in CHANNELS + GROUPS:
        kb.add(types.InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch.replace('@','')}"))
    kb.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check"))
    bot.send_message(uid, "❌ Iltimos, majburiy obunaga a'zo bo‘ling:", reply_markup=kb)

def menu(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👤 Profil", callback_data="profile"),
        types.InlineKeyboardButton("👥 Taklif", callback_data="ref"),
    )
    if uid == ADMIN:
        kb.add(types.InlineKeyboardButton("⚙ Admin Panel", callback_data="admin"))
    bot.send_message(uid, "📋 Asosiy menyu:", reply_markup=kb)

# ===== START COMMAND =====
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.chat.id
    args = msg.text.split()
    ref = None
    if len(args) > 1:
        try:
            ref = int(args[1])
        except:
            ref = None
    add_user(uid, ref)

    if not check_sub(uid):
        join_menu(uid)
        return

    bot.send_message(uid, "🚀 Xush kelibsiz!")
    menu(uid)

# ===== CALLBACK HANDLER =====
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid = c.message.chat.id
    user = get_user(uid)
    if not user:
        add_user(uid)
        user = get_user(uid)

    if c.data == "check":
        if check_sub(uid):
            bot.send_message(uid, "✅ Obuna tekshiruvi muvaffaqiyatli!")
        else:
            bot.send_message(uid, "❌ Siz hali barcha maj