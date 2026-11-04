import logging
import random
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

import config
import database as db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== وضعیت‌ها ==================
(
    WAIT_JOIN, WAIT_NAME, WAIT_BET,
    WAIT_RPS, WAIT_TAS, WAIT_GUESS, WAIT_GOL,
    WAIT_ADMIN_PASS, WAIT_ADMIN_CODE, WAIT_ADMIN_ACTION
) = range(10)

# ================== چک عضویت ==================
async def check_membership(context, user_id):
    try:
        member = await context.bot.get_chat_member(config.CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

# ================== /start ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if db.is_joined(user_id):
        return await main_menu(update, context)

    keyboard = [
        [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{config.CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")]
    ]
    await update.message.reply_text(
        f"👋 خوش آمدید!\n\n"
        f"⚠️ برای استفاده از این ربات باید وارد و عضو کانال زیر شوید:\n"
        f"{config.CHANNEL_USERNAME}\n\n"
        f"بعد از عضویت روی دکمه «✅ عضو شدم» بزنید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await check_membership(context, user_id):
        keyboard = [[InlineKeyboardButton("🆕 ساخت حساب کاربری", callback_data="create_account")]]
        await query.edit_message_text(
            "✅ عضویت شما تایید شد!\n\nبرای ادامه روی دکمه زیر بزنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.answer("❌ شما عضو نشدید! دوباره تلاش کنید.", show_alert=True)

# ================== ساخت حساب ==================
async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✍️ لطفاً اسم خاص خود را بنویسید:\n"
        "• فقط حروف انگلیسی\n"
        "• بین ۳ تا ۱۶ حرف\n"
        "• بدون عدد و فاصله\n\n"
        "مثال: `Tamsoom`",
        parse_mode="Markdown"
    )

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    user_id = update.effective_user.id

    if not re.fullmatch(r"[A-Za-z]{3,16}", name):
        await update.message.reply_text(
            "❌ اسم نامعتبر!\nفقط حروف انگلیسی، ۳ تا ۱۶ حرف، بدون عدد و فاصله.\nدوباره بفرست:"
        )
        return

    if db.name_exists(name):
        await update.message.reply_text(f"❌ اسم «{name}» قبلاً استفاده شده!\nیه اسم دیگه بفرست:")
        return

    code = db.create_user(user_id, name)
    await update.message.reply_text(
        f"✅ حساب شما ساخته شد!\n\n"
        f"🎭 اسم خاص: `{name}`\n"
        f"🔢 کد کاربری: `{code}`\n"
        f"💰 سکه اولیه: ۱۰۰\n"
        f"🎰 اسپین اولیه: ۱\n\n"
        f"از منوی زیر استفاده کن:",
        parse_mode="Markdown"
    )
    await main_menu(update, context, from_message=True)

# ================== منوی اصلی ==================
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_message=False):
    keyboard = [
        [InlineKeyboardButton("🎮 بازی ها", callback_data="menu_games")],
        [InlineKeyboardButton("📖 راهنما", callback_data="menu_help")],
        [InlineKeyboardButton("💵 واریز", callback_data="menu_deposit")],
        [InlineKeyboardButton("💸 برداشت", callback_data="menu_withdraw")],
        [InlineKeyboardButton("👤 حساب کاربری", callback_data="menu_account")],
        [InlineKeyboardButton("🛠 پنل ادمینی", callback_data="menu_admin")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="menu_support")],
    ]
    text = "🏠 منوی اصلی:\nیکی از گزینه‌ها را انتخاب کنید:"
    markup = InlineKeyboardMarkup(keyboard)

    if from_message:
        await update.message.reply_text(text, reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await main_menu(update, context)

# ================== منوهای ساده ==================
async def menu_help(update, context):
    q = update.callback_query
    await q.answer()
    text = (
        "📖 *راهنمای ربات*\n\n"
        "🎮 *بازی‌ها:*\n"
        "• سنگ کاغذ قیچی — ۱.۵×\n"
        "• گل یا پوچ — ۱.۵×\n"
        "• تاس (زوج/فرد) — ۱.۵×\n"
        "• حدس عدد (۱ تا ۱۰۰) — ۲×\n"
        "• اسپین (چرخ شانسی) — ضرایب مختلف\n"
        "• فوتبال/بسکتبال/دارت — ۱.۵×\n\n"
        "💰 *واریز:*\n"
        f"سکه‌ها را به خاص `{config.BITA_ID}` واریز و عکس را برای پشتیبانی بفرستید.\n\n"
        "💸 *برداشت:*\n"
        "از «حساب کاربری» پیام را برای پشتیبانی بفرستید.\n\n"
        f"📞 پشتیبانی: {config.SUPPORT_ID}"
    )
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def menu_deposit(update, context):
    q = update.callback_query
    await q.answer()
    text = (
        "💵 *واریز سکه*\n\n"
        f"سکه‌ها را به خاص `{config.BITA_ID}` واریز کنید و عکس واریزی را برای پشتیبان بفرستید (فقط عکس).\n\n"
        f"📞 پشتیبانی: {config.SUPPORT_ID}\n\n"
        "⏳ منتظر بمانید تا سکه‌ها واریز شود."
    )
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def menu_withdraw(update, context):
    q = update.callback_query
    await q.answer()
    text = (
        "💸 *برداشت سکه*\n\n"
        "روی «👤 حساب کاربری» بزنید و پیام را برای پشتیبانی بفرستید تا سکه گیفت شود.\n\n"
        f"📞 پشتیبانی: {config.SUPPORT_ID}"
    )
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def menu_support(update, context):
    q = update.callback_query
    await q.answer()
    text = f"📞 *پشتیبانی*\n\n{config.SUPPORT_ID}\n\n⏳ لطفاً منتظر بمانید، پاسخ می‌دهیم."
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# ================== حساب کاربری ==================
async def menu_account(update, context):
    q = update.callback_query
    await q.answer()
    user = db.get_user(q.from_user.id)
    if not user:
        return await q.edit_message_text("❌ اول حساب بساز!")
    text = (
        "👤 *حساب کاربری شما*\n"
        "━━━━━━━━━━━━━━━━\n"
        f"🎭 اسم خاص: `{user[1]}`\n"
        f"🔢 کد کاربری: `{user[2]}`\n"
        f"💰 سکه: `{user[3]}`\n"
        f"🎰 اسپین: `{user[4]}`\n"
        f"✅ برد: `{user[5]}`\n"
        f"❌ باخت: `{user[6]}`\n"
        "━━━━━━━━━━━━━━━━"
    )
    kb = [
        [InlineKeyboardButton("🎰 اسپین روزانه", callback_data="daily_spin")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def daily_spin(update, context):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    user = db.get_user(user_id)
    today = datetime.now().strftime("%Y-%m-%d")

    if user[7] == today:
        return await q.answer("⏳ امروز اسپین روزانه‌ت رو گرفتی! فردا دوباره بیا.", show_alert=True)

    # انتخاب نتیجه تصادفی
    rewards = config.DAILY_SPIN_REWARDS
    total = sum(w for _, w in rewards)
    r = random.uniform(0, total)
    upto = 0
    reward = 0
    for amount, weight in rewards:
        upto += weight
        if r <= upto:
            reward = amount
            break

    new_coins = user[3] + reward
    db.update_user(user_id, coins=new_coins, last_daily_spin=today)

    if reward > 0:
        text = f"🎉 تبریک! برنده {reward} سکه شدی!\n\n💰 سکه فعلی: {new_coins}"
    else:
        text = f"😢 متاسفانه پوچ بود!\n\n💰 سکه فعلی: {new_coins}"

    await q.edit_message_text(text)
    await main_menu(update, context)
