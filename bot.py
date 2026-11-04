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

# ================== حساب کاربری و اسپین روزانه ==================
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

# ================== بخش بازی‌ها ==================
async def menu_games(update, context):
    q = update.callback_query
    await q.answer()
    kb = [
        [InlineKeyboardButton("✂️ سنگ کاغذ قیچی", callback_data="game_rps")],
        [InlineKeyboardButton("✊ گل یا پوچ", callback_data="game_gol")],
        [InlineKeyboardButton("🎲 تاس (زوج/فرد)", callback_data="game_tas")],
        [InlineKeyboardButton("🔢 حدس عدد", callback_data="game_guess")],
        [InlineKeyboardButton("🎰 اسپین", callback_data="game_spin")],
        [InlineKeyboardButton("⚽️ توپ فوتبال", callback_data="game_football")],
        [InlineKeyboardButton("🏀 بسکتبال", callback_data="game_basketball")],
        [InlineKeyboardButton("🎯 دارت", callback_data="game_dart")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ]
    await q.edit_message_text("🎮 یک بازی را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

async def ask_bet(update, context, game):
    q = update.callback_query
    await q.answer()
    context.user_data["current_game"] = game
    await q.edit_message_text(
        f"💰 مقدار سکه شرط‌بندی را بنویسید:\n"
        f"(بین {config.MIN_BET} تا {config.MAX_BET:,} سکه)\n\n"
        "برای لغو /start را بزنید."
    )

async def receive_bet(update, context):
    game = context.user_data.get("current_game")
    if not game:
        return
    try:
        bet = int(update.message.text.strip())
    except ValueError:
        return await update.message.reply_text("❌ لطفاً فقط عدد بفرستید:")
    
    if bet < config.MIN_BET or bet > config.MAX_BET:
        return await update.message.reply_text(f"❌ مقدار باید بین {config.MIN_BET} تا {config.MAX_BET:,} باشد:")
    
    user = db.get_user(update.effective_user.id)
    if user[3] < bet:
        return await update.message.reply_text("❌ سکه کافی ندارید!")
    
    context.user_data["bet"] = bet

    if game == "rps":
        kb = [
            [InlineKeyboardButton("🪨 سنگ", callback_data="rps_rock"), InlineKeyboardButton("📄 کاغذ", callback_data="rps_paper"), InlineKeyboardButton("✂️ قیچی", callback_data="rps_scissors")],
        ]
        await update.message.reply_text("انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
    elif game == "gol":
        kb = [
            [InlineKeyboardButton("✊ دست راست", callback_data="gol_right"), InlineKeyboardButton("✊ دست چپ", callback_data="gol_left")],
        ]
        await update.message.reply_text("تو کدوم دسته؟", reply_markup=InlineKeyboardMarkup(kb))
    elif game == "tas":
        kb = [[InlineKeyboardButton("زوج", callback_data="tas_even"), InlineKeyboardButton("فرد", callback_data="tas_odd")]]
        await update.message.reply_text("زوج یا فرد؟", reply_markup=InlineKeyboardMarkup(kb))
    elif game == "guess":
        await update.message.reply_text("🔢 یک عدد بین ۱ تا ۱۰۰ حدس بزن:")
    elif game in ["football", "basketball", "dart"]:
        kb = [[InlineKeyboardButton("🚀 شوت/پرتاب کن", callback_data=f"play_{game}")]]
        await update.message.reply_text("برای شانس خودت بزن:", reply_markup=InlineKeyboardMarkup(kb))

async def finish_game(update, context, won, multiplier=1.5):
    q = update.callback_query
    user_id = q.from_user.id
    user = db.get_user(user_id)
    bet = context.user_data.get("bet", 0)

    if won:
        win_amount = int(bet * multiplier)
        new_coins = user[3] + win_amount
        db.update_user(user_id, coins=new_coins, wins=user[5] + 1)
        text = f"🎉 برنده شدی! {win_amount} سکه گرفتی.\n💰 سکه فعلی: {new_coins}"
    else:
        new_coins = user[3] - bet
        db.update_user(user_id, coins=new_coins, losses=user[6] + 1)
        text = f"😢 باختی! {bet} سکه از دست دادی.\n💰 سکه فعلی: {new_coins}"

    await q.edit_message_text(text)
    await main_menu(update, context)

# هندلرهای بازی‌ها
async def game_rps(update, context):
    await ask_bet(update, context, "rps")

async def play_rps(update, context):
    q = update.callback_query
    await q.answer()
    user_choice = q.data.split("_")[1]
    bot_choice = random.choice(["rock", "paper", "scissors"])
    
    wins = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
    won = wins[user_choice] == bot_choice
    tie = user_choice == bot_choice
    
    emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
    text_prefix = f"شما: {emojis[user_choice]} | ربات: {emojis[bot_choice]}\n\n"
    
    if tie:
        await q.edit_message_text(f"{text_prefix}🤝 مساوی! سکه‌ات برنگشت.")
        await main_menu(update, context)
    else:
        await finish_game(update, context, won, config.RPS_WIN_RATE)

async def game_gol(update, context):
    await ask_bet(update, context, "gol")

async def play_gol(update, context):
    q = update.callback_query
    await q.answer()
    user_choice = q.data.split("_")[1]
    bot_choice = random.choice(["right", "left"])
    won = user_choice == bot_choice
    await finish_game(update, context, won, config.GOL_WIN_RATE)

async def game_tas(update, context):
    await ask_bet(update, context, "tas")

async def play_tas(update, context):
    q = update.callback_query
    await q.answer()
    user_choice = q.data.split("_")[1] # even or odd
    dice = random.randint(1, 6)
    is_even = dice % 2 == 0
    won = (user_choice == "even" and is_even) or (user_choice == "odd" and not is_even)
    await q.edit_message_text(f"🎲 تاس: {dice}\n\n")
    await finish_game(update, context, won, config.TAS_WIN_RATE)

async def game_guess(update, context):
    await ask_bet(update, context, "guess")
    context.user_data["target_number"] = random.randint(1, 100)

async def play_guess(update, context):
    try:
        guess = int(update.message.text.strip())
    except ValueError:
        return await update.message.reply_text("❌ فقط عدد بفرست:")
    
    target = context.user_data.get("target_number")
    won = guess == target
    
    class FakeQuery:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
        async def answer(self): pass
        async def edit_message_text(self, text, **kwargs): await self.message.reply_text(text, **kwargs)

    fake_update = Update(0, message=update.message)
    fake_update.callback_query = FakeQuery(update.message)
    
    if won:
        await update.message.reply_text(f"🎯 درست بود! عدد {target} بود.")
        await finish_game(fake_update, context, True, config.GUESS_WIN_RATE)
    else:
        await update.message.reply_text(f"❌ اشتباه بود! عدد {target} بود.")
        await finish_game(fake_update, context, False, config.GUESS_WIN_RATE)

async def game_football(update, context): await ask_bet(update, context, "football")
async def game_basketball(update, context): await ask_bet(update, context, "basketball")
async def game_dart(update, context): await ask_bet(update, context, "dart")

async def play_sport(update, context):
    q = update.callback_query
    await q.answer()
    won = random.random() < 0.4 # 40% chance to win
    await finish_game(update, context, won, config.SPORT_WIN_RATE)

async def game_spin(update, context):
    q = update.callback_query
    await q.answer()
    user = db.get_user(q.from_user.id)
    if user[4] < 1:
        return await q.answer("❌ اسپین نداری! منتظر جایزه روزانه باش.", show_alert=True)
    
    db.update_user(q.from_user.id, spins=user[4] - 1)
    
    multipliers = config.GAME_SPIN_MULTIPLIERS
    total = sum(w for _, w in multipliers)
    r = random.uniform(0, total)
    upto = 0
    mult = 0
    for m, weight in multipliers:
        upto += weight
        if r <= upto:
            mult = m
            break
            
    if mult == 0:
        text = "🎰 اسپین: پوچ! 😢"
    else:
        text = f"🎰 اسپین: ضریب {mult}× !\n🎉 {mult} برابر سکه گرفتی!"
    
    class FakeQuery:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
        async def answer(self): pass
        async def edit_message_text(self, text, **kwargs): await self.message.reply_text(text, **kwargs)
            
    fake_update = Update(0, message=q.message)
    fake_update.callback_query = FakeQuery(q.message)

    if mult > 0:
        bet = config.MIN_BET # Default for game spin if no bet asked, but better to ask bet. For simplicity, using min bet.
        user = db.get_user(q.from_user.id)
        # For spin game, let's just give 100 coins base if won
        win_amount = int(100 * mult)
        db.update_user(q.from_user.id, coins=user[3] + win_amount)
        await q.edit_message_text(text + f"\n💰 سکه فعلی: {user[3] + win_amount}")
    else:
        await q.edit_message_text(text)
    await main_menu(update, context)

# ================== پنل ادمینی ==================
async def menu_admin(update, context):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != config.ADMIN_ID:
        return await q.answer("⛔️ شما دسترسی ندارید!", show_alert=True)
    
    await q.edit_message_text("🔐 لطفاً رمز عبور پنل ادمینی را وارد کنید:")
    context.user_data["admin_auth"] = False

async def check_admin_pass(update, context):
    if update.effective_user.id != config.ADMIN_ID: return
    if update.message.text.strip() == config.ADMIN_PASSWORD:
        context.user_data["admin_auth"] = True
        await update.message.reply_text("✅ رمز صحیح! کد کاربری (۴ رقمی) شخص را وارد کنید:")
    else:
        await update.message.reply_text("❌ رمز اشتباه است!")

async def admin_user_code(update, context):
    if not context.user_data.get("admin_auth"): return
    try:
        code = int(update.message.text.strip())
    except ValueError:
        return await update.message.reply_text("❌ کد باید ۴ رقمی باشد:")
    
    user = db.get_user_by_code(code)
    if not user:
        return await update.message.reply_text("❌ کاربری با این کد یافت نشد!")
    
    context.user_data["target_user"] = code
    await update.message.reply_text(
        f"👤 کاربر: {user[1]}\n💰 سکه: {user[3]}\n🎰 اسپین: {user[4]}\n\n"
        f"چه تغییری ایجاد شود؟ (مثال: +200 سکه، -50 سکه، +1 اسپین، -1 اسپین)"
    )

async def admin_action(update, context):
    if not context.user_data.get("admin_auth"): return
    code = context.user_data.get("target_user")
    if not code: return
    
    text = update.message.text.strip().lower()
    user = db.get_user_by_code(code)
    
    try:
        if "سکه" in text:
            amount = int(re.search(r'[+-]?\d+', text).group())
            new_coins = user[3] + amount
            if new_coins < 0: new_coins = 0
            db.update_user_by_code(code, coins=new_coins)
            await update.message.reply_text(f"✅ سکه‌های {user[1]} به {new_coins} تغییر یافت.")
        elif "اسپین" in text:
            amount = int(re.search(r'[+-]?\d+', text).group())
            new_spins = user[4] + amount
            if new_spins < 0: new_spins = 0
            db.update_user_by_code(code, spins=new_spins)
            await update.message.reply_text(f"✅ اسپین‌های {user[1]} به {new_spins} تغییر یافت.")
        else:
            await update.message.reply_text("❌ فرمت نامعتبر! (مثال: +200 سکه یا -1 اسپین)")
    except:
        await update.message.reply_text("❌ خطا در خواندن مقدار! دوباره تلاش کنید.")
    
    context.user_data["admin_auth"] = False
    context.user_data["target_user"] = None

# ================== مدیریت پیام‌ها ==================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    # اگه ادمین بود و توی حالت تایید رمز بود
    if user_id == config.ADMIN_ID and context.user_data.get("admin_auth") is False:
        return await check_admin_pass(update, context)
    if user_id == config.ADMIN_ID and context.user_data.get("admin_auth") is True and context.user_data.get("target_user") is None:
        return await admin_user_code(update, context)
    if user_id == config.ADMIN_ID and context.user_data.get("target_user"):
        return await admin_action(update, context)

    # اگه کاربر در حال ساخت حسابه
    if not user:
        return await receive_name(update, context)
    
    # اگه توی بازی حدس عدده
    if context.user_data.get("current_game") == "guess" and "target_number" in context.user_data:
        return await play_guess(update, context)
    
    # اگه توی حالت گرفتن شرط بود
    if context.user_data.get("current_game") and "bet" not in context.user_data:
        return await receive_bet(update, context)

# ================== اجرای ربات ==================
def main():
    db.init_db()
    app = Application.builder().token(config.BOT_TOKEN).build()

    # کامندها
    app.add_handler(CommandHandler("start", start))

    # کال‌بک‌ها
    app.add_handler(CallbackQueryHandler(check_join, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(create_account, pattern="^create_account$"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(menu_help, pattern="^menu_help$"))
    app.add_handler(CallbackQueryHandler(menu_deposit, pattern="^menu_deposit$"))
    app.add_handler(CallbackQueryHandler(menu_withdraw, pattern="^menu_withdraw$"))
    app.add_handler(CallbackQueryHandler(menu_account, pattern="^menu_account$"))
    app.add_handler(CallbackQueryHandler(menu_support, pattern="^menu_support$"))
    app.add_handler(CallbackQueryHandler(daily_spin, pattern="^daily_spin$"))
    app.add_handler(CallbackQueryHandler(menu_games, pattern="^menu_games$"))
    app.add_handler(CallbackQueryHandler(menu_admin, pattern="^menu_admin$"))

    # بازی‌ها
    app.add_handler(CallbackQueryHandler(game_rps, pattern="^game_rps$"))
    app.add_handler(CallbackQueryHandler(play_rps, pattern="^rps_"))
    app.add_handler(CallbackQueryHandler(game_gol, pattern="^game_gol$"))
    app.add_handler(CallbackQueryHandler(play_gol, pattern="^gol_"))
    app.add_handler(CallbackQueryHandler(game_tas, pattern="^game_tas$"))
    app.add_handler(CallbackQueryHandler(play_tas, pattern="^tas_"))
    app.add_handler(CallbackQueryHandler(game_guess, pattern="^game_guess$"))
    app.add_handler(CallbackQueryHandler(game_spin, pattern="^game_spin$"))
    app.add_handler(CallbackQueryHandler(game_football, pattern="^game_football$"))
    app.add_handler(CallbackQueryHandler(game_basketball, pattern="^game_basketball$"))
    app.add_handler(CallbackQueryHandler(game_dart, pattern="^game_dart$"))
    app.add_handler(CallbackQueryHandler(play_sport, pattern="^play_"))

    # پیام‌های متنی
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    logger.info("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
