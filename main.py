import asyncio
import json
import os
from pathlib import Path
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import feedparser
import requests
from dotenv import load_dotenv

from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import Application, CommandHandler, ContextTypes

# ========= Paths / Env =========
BASE_DIR = Path(__file__).parent
CLIENTS_DIR = BASE_DIR / "clients"
STYLES_DIR = BASE_DIR / "styles"

load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("BOT_TOKEN", "").strip()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct").strip()
PAY_CONTACTS = os.getenv("PAY_CONTACTS", "").strip()

# Admins can activate subscriptions (manual payments handled outside)
ADMIN_IDS = set()
_raw_admins = os.getenv("ADMIN_IDS", "").strip()
if _raw_admins:
    for x in _raw_admins.split(","):
        x = x.strip()
        if x.isdigit():
            ADMIN_IDS.add(int(x))

# ========= Defaults =========
DEFAULT_STYLE_FILE = "default_ru.txt"

DEFAULT_CLIENT = {
    "channel": None,
    "feeds": [],
    "posted_urls": [],
    "autopost_enabled": False,
    "interval_minutes": 30,
    "daily_limit": 5,
    "daily_count": 0,
    "daily_date": str(date.today()),
    "max_dedupe": 1500,
    "fetch_entries_per_feed": 15,
    "language": None,          # "en" or "ru"

    # style handling
    "style_file": DEFAULT_STYLE_FILE,     # file inside /styles
    "custom_style_file": None,            # file inside /clients, per-user

    # manual subscription
    "subscription_until": None,           # YYYY-MM-DD (inclusive)
}


# ========= Utilities =========
def ensure_dirs() -> None:
    CLIENTS_DIR.mkdir(parents=True, exist_ok=True)
    STYLES_DIR.mkdir(parents=True, exist_ok=True)

def client_path(user_id: int) -> Path:
    return CLIENTS_DIR / f"{user_id}.json"

def custom_style_path(user_id: int) -> Path:
    return CLIENTS_DIR / f"{user_id}_style.txt"

def load_client(user_id: int) -> dict:
    p = client_path(user_id)
    if not p.exists():
        cfg = dict(DEFAULT_CLIENT)
        save_client(user_id, cfg)
        return cfg

    try:
        cfg = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(cfg, dict):
            raise ValueError("client config is not dict")
    except Exception:
        broken = p.read_text(encoding="utf-8", errors="ignore")
        (CLIENTS_DIR / f"{user_id}.broken.json").write_text(broken, encoding="utf-8", errors="ignore")
        cfg = dict(DEFAULT_CLIENT)
        save_client(user_id, cfg)
        return cfg

    # fill missing keys
    for k, v in DEFAULT_CLIENT.items():
        cfg.setdefault(k, v)
    return cfg

def save_client(user_id: int, cfg: dict) -> None:
    client_path(user_id).write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

def clean_text(s: str) -> str:
    if not s:
        return ""
    return " ".join(str(s).replace("\n", " ").split()).strip()

def ensure_daily_counter(cfg: dict) -> dict:
    today = str(date.today())
    if cfg.get("daily_date") != today:
        cfg["daily_date"] = today
        cfg["daily_count"] = 0
    return cfg

def can_post_more(cfg: dict) -> bool:
    cfg = ensure_daily_counter(cfg)
    return int(cfg.get("daily_count", 0)) < int(cfg.get("daily_limit", 5))

def bump_daily_count(cfg: dict) -> None:
    cfg = ensure_daily_counter(cfg)
    cfg["daily_count"] = int(cfg.get("daily_count", 0)) + 1

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def subscription_ok(cfg: dict) -> bool:
    until = (cfg.get("subscription_until") or "").strip()
    if not until:
        return False
    try:
        d = datetime.strptime(until, "%Y-%m-%d").date()
    except Exception:
        return False
    return date.today() <= d

def normalize_url(url: str) -> str:
    """
    Remove tracking params so dedupe works across RSS variants.
    Examples: utm_*, at_medium, at_campaign, fbclid, gclid, etc.
    """
    parts = urlsplit(url)
    q = parse_qsl(parts.query, keep_blank_values=True)

    banned_exact = {
        "at_medium", "at_campaign", "at_bbc_team", "at_link_origin",
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "fbclid", "gclid", "igshid", "mc_cid", "mc_eid"
    }

    new_q = []
    for k, v in q:
        kl = k.lower()
        if kl in banned_exact:
            continue
        if kl.startswith("utm_"):
            continue
        new_q.append((k, v))

    new_query = urlencode(new_q, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, ""))

def get_style_prompt(user_id: int, cfg: dict) -> str:
    # 1) per-user custom style file in /clients (safe, not in JSON)
    cpath = custom_style_path(user_id)
    if cpath.exists():
        txt = cpath.read_text(encoding="utf-8", errors="ignore").strip()
        if txt:
            return txt

    # 2) named style file in /styles
    style_file = (cfg.get("style_file") or DEFAULT_STYLE_FILE).strip()
    spath = STYLES_DIR / style_file
    if spath.exists():
        return spath.read_text(encoding="utf-8", errors="ignore").strip()

    # 3) fallback
    return (
        "Ты автор телеграм-канала.\n"
        "Пиши коротко, без воды, естественным русским.\n"
        "Формат:\n"
        "1) Заголовок-строка\n"
        "2) 2–4 строки фактов\n"
        "3) ссылка в конце\n"
        "Лимит: до 900 символов.\n"
        "Факты не выдумывай.\n"
    )

def sanitize_llm_post(text: str, link: str) -> str:
    t = (text or "").replace("\r", "").strip()

    # Remove obvious junk markers
    bad_tokens = ["Хук", "Буллеты", "Мнение", "Ссылка", "Формат", "Итог"]
    for tok in bad_tokens:
        t = t.replace(tok + ":", "").replace(tok, "")

    # Split into non-empty lines
    lines = [ln.strip() for ln in t.split("\n") if ln.strip()]

    # If model returned one paragraph, split it into sentences
    if len(lines) < 4:
        import re
        s = " ".join(lines)
        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", s) if p.strip()]
        lines = parts

    # Build strict structure
    title = lines[0] if lines else "📌 Новость"
    body_candidates = lines[1:8]

    # Pick 3 short body lines
    body = []
    for ln in body_candidates:
        ln = ln.replace("•", "").strip()
        if len(ln) < 15:
            continue
        if len(ln) > 140:
            ln = ln[:140].rstrip() + "…"
        body.append(ln)
        if len(body) == 3:
            break

    while len(body) < 3:
        body.append("Подробности уточняются по источнику.")

    out = [title, "", body[0], body[1], body[2], "", f"🔗 {link}"]
    msg = "\n".join(out)
    return msg[:900]
def pick_newest_unseen(cfg: dict):
    feeds = cfg.get("feeds", [])
    posted = set(cfg.get("posted_urls", []))

    best = None  # (published_parsed, title, link, feed_url)
    per_feed = int(cfg.get("fetch_entries_per_feed", 15))

    for feed_url in feeds:
        fp = feedparser.parse(feed_url)
        entries = getattr(fp, "entries", []) or []
        for e in entries[:per_feed]:
            link = getattr(e, "link", None)
            if not link:
                continue
            link_n = normalize_url(link)

            if link_n in posted:
                continue

            title = getattr(e, "title", "Untitled")
            published = getattr(e, "published_parsed", None)
            key = (published or (0,), title)

            if best is None or key > ((best[0] or (0,)), best[1]):
                best = (published, title, link_n, feed_url)

    return best

def extract_summary_for_link(feed_url: str, link_normalized: str, limit: int = 20) -> str:
    fp = feedparser.parse(feed_url)
    entries = getattr(fp, "entries", []) or []
    for e in entries[:limit]:
        link = getattr(e, "link", None)
        if not link:
            continue
        if normalize_url(link) == link_normalized:
            return clean_text(getattr(e, "summary", "") or getattr(e, "description", "") or "")
    return ""

def ollama_generate_post(user_id: int, cfg: dict, title: str, summary: str, link: str) -> str:
    style_prompt = get_style_prompt(user_id, cfg)
    title = clean_text(title)
    summary = clean_text(summary)

    user_content = (
        f"ИСТОЧНИК:\n"
        f"Заголовок: {title}\n"
        f"Кратко: {summary}\n"
        f"Ссылка: {link}\n\n"
        f"ТРЕБОВАНИЯ:\n"
        f"- Язык: русский\n"
        f"- Факты только из текста\n"
        f"- Имена/клубы не коверкать\n"
        f"- Ссылка в конце\n"
        f"- До 900 символов\n"
    )

    prompt = style_prompt + "\n\n" + user_content
    payload = {
    "model": OLLAMA_MODEL,
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.2,
        "top_p": 0.9,
        "repeat_penalty": 1.15,
        "num_predict": 220
    }
}

    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    text = clean_text(data.get("response", ""))
    text = sanitize_llm_post(text, link)

    if link not in text:
        text = text + "\n🔗 " + link

    return text[:1500]


# ========= Commands =========
TEXTS = {
    "en": {
        "choose_lang": (
    "👋 Hi! Choose your language.\n\n"
    "✅ Tap one option below and the language will be set automatically:\n"
    "/lang en\n"
    "/lang ru\n\n"
    "If nothing happens, type it manually like: /lang en"
),
        "lang_set": "✅ Language saved.",
        "start_ready": (
    "✅ Bot is ready.\n\n"
    "How to set it up (2–3 minutes):\n\n"
    "1) Connect your channel\n"
    "   /setchannel @yourchannel\n"
    "   (Bot must be admin and allowed to post.)\n\n"
    "2) Add sources (RSS feeds)\n"
    "   /addfeed https://site.com/rss\n"
    "   Repeat /addfeed to add more.\n"
    "   Tip: RSS links often contain “rss” or “feed”.\n\n"
    "3) Set writing style (prompt)\n"
    "   /setstyle <paste your style text>\n"
    "   This is an instruction: tone, format, emojis, length.\n\n"
    "4) Preview (no posting)\n"
    "   /previewonce\n"
    "   You will see one generated post in this chat.\n\n"
    "5) Post once to your channel\n"
    "   /fetchonce\n\n"
    "Autopost (paid):\n"
    "Ask admin to activate your account, then enable:\n"
    "/autoposton\n\n"
    "Your ID (send this to admin):\n"
    "/status"
),
        "pay_msg": "💳 Subscription is required. Message: {contacts}",
        "no_contacts": "💳 Subscription is required. Ask admin for payment details.",
        "sub_inactive": "💳 Subscription inactive. Message admin to activate your account.",
    },
    "ru": {
        "choose_lang": (
    "👋 Привет! Выберите язык.\n\n"
    "✅ Нажмите на вариант ниже, язык установится автоматически:\n"
    "/lang ru\n"
    "/lang en\n\n"
    "Если не сработало, введите вручную, например: /lang ru"
),
        "lang_set": "✅ Язык сохранён.",
        "start_ready": (
    "✅ Бот готов.\n\n"
    "Как настроить (2–3 минуты):\n\n"
    "1) Подключите канал\n"
    "   /setchannel @вашканал\n"
    "   (Бот должен быть админом и иметь право публиковать.)\n\n"
    "2) Добавьте источники (RSS-ленты)\n"
    "   /addfeed https://site.com/rss\n"
    "   Повторяйте /addfeed, чтобы добавить ещё.\n"
    "   Подсказка: RSS-ссылки часто содержат “rss” или “feed”.\n\n"
    "3) Задайте стиль написания (prompt)\n"
    "   /setstyle <вставьте ваш текст-стиль>\n"
    "   Это инструкция: тон, формат, эмодзи, длина.\n\n"
    "4) Превью (ничего не публикует)\n"
    "   /previewonce\n"
    "   Бот покажет один пример поста прямо здесь.\n\n"
    "5) Опубликовать один раз в канал\n"
    "   /fetchonce\n\n"
    "Автопостинг (платно):\n"
    "Напишите админу для активации, потом включите:\n"
    "/autoposton\n\n"
    "Ваш ID (отправьте админу):\n"
    "/status"
),
        "pay_msg": "💳 Нужна подписка. Напишите: {contacts}",
        "no_contacts": "💳 Нужна подписка. Попросите у админа реквизиты для оплаты.",
        "sub_inactive": "💳 Подписка не активна. Напишите админу, чтобы включить.",
    },
}

def tr(cfg: dict, key: str) -> str:
    lang = (cfg.get("language") or "en").lower()
    if lang not in ("en", "ru"):
        lang = "en"
    return TEXTS[lang].get(key, TEXTS["en"].get(key, key))

def pay_line(cfg: dict) -> str:
    if PAY_CONTACTS:
        return tr(cfg, "pay_msg").format(contacts=PAY_CONTACTS)
    return tr(cfg, "no_contacts")

async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not context.args:
        await update.message.reply_text(tr(cfg, "choose_lang"))
        return

    choice = context.args[0].strip().lower()
    if choice not in ("en", "ru"):
        await update.message.reply_text(tr(cfg, "choose_lang"))
        return

    cfg["language"] = choice
    save_client(user_id, cfg)
    await update.message.reply_text(tr(cfg, "lang_set") + "\n\n" + tr(cfg, "start_ready") + "\n\n" + pay_line(cfg))
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not cfg.get("language"):
        await update.message.reply_text(TEXTS["en"]["choose_lang"])
        return

    await update.message.reply_text(tr(cfg, "start_ready") + "\n\n" + pay_line(cfg))

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    cfg = ensure_daily_counter(cfg)
    sub = cfg.get("subscription_until") or "inactive"

    await update.message.reply_text(
        f"👤 Your ID: {user_id}\n"
        f"📌 Channel: {cfg.get('channel') or 'not set'}\n"
        f"🧾 Feeds: {len(cfg.get('feeds', []))}\n"
        f"🧠 Dedupe stored: {len(cfg.get('posted_urls', []))}\n"
        f"🤖 Autopost: {'ON' if cfg.get('autopost_enabled') else 'OFF'}\n"
        f"⏱ Interval: {cfg.get('interval_minutes')} min\n"
        f"📅 Daily: {cfg.get('daily_count')}/{cfg.get('daily_limit')} (date {cfg.get('daily_date')})\n"
        f"💳 Subscription until: {sub}\n"
        f"🧠 Ollama model: {OLLAMA_MODEL}"
    )

async def setchannel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not context.args:
        await update.message.reply_text("Usage: /setchannel @channelusername")
        return

    channel = context.args[0].strip()
    if not channel.startswith("@"):
        await update.message.reply_text("Channel should look like @channelusername")
        return

    bot = context.bot
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=bot.id)
        if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            await update.message.reply_text(
                "Bot sees the channel, admin rights are missing.\n"
                "Add the bot as admin with permission to post messages, then retry."
            )
            return
    except Exception as e:
        await update.message.reply_text(
            "Channel access failed.\n"
            "Checklist:\n"
            "1) Channel is public (has @username)\n"
            "2) Bot is added as admin\n"
            "3) Username typed correctly\n"
            f"\nError: {type(e).__name__}"
        )
        return

    cfg["channel"] = channel
    save_client(user_id, cfg)
    await update.message.reply_text(f"✅ Channel saved: {channel}")

async def addfeed_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not context.args:
        await update.message.reply_text("Usage: /addfeed https://site.com/rss")
        return

    url = context.args[0].strip()
    feeds = cfg.get("feeds", [])

    if url in feeds:
        await update.message.reply_text("Already added.")
        return

    fp = feedparser.parse(url)
    if not getattr(fp, "entries", None):
        await update.message.reply_text("Feed read failed (no entries). Check the URL.")
        return

    feeds.append(url)
    cfg["feeds"] = feeds
    save_client(user_id, cfg)
    await update.message.reply_text(f"✅ Feed added. Total: {len(feeds)}")

async def feeds_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    feeds = cfg.get("feeds", [])

    if not feeds:
        await update.message.reply_text("No feeds. Add one: /addfeed <url>")
        return

    text = "🧾 Feeds:\n" + "\n".join([f"{i+1}) {u}" for i, u in enumerate(feeds)])
    await update.message.reply_text(text)

async def seed_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    feeds = cfg.get("feeds", [])
    if not feeds:
        await update.message.reply_text("No feeds. Add one: /addfeed <url>")
        return

    n = 10
    if context.args:
        try:
            n = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Usage: /seed 10")
            return

    if n < 1 or n > 50:
        await update.message.reply_text("Choose 1..50")
        return

    posted = list(cfg.get("posted_urls", []))
    posted_set = set(posted)
    added = 0

    for feed_url in feeds:
        fp = feedparser.parse(feed_url)
        entries = getattr(fp, "entries", []) or []
        for e in entries[:n]:
            link = getattr(e, "link", None)
            if link:
                link_n = normalize_url(link)
                if link_n not in posted_set:
                    posted.append(link_n)
                    posted_set.add(link_n)
                    added += 1

    max_dedupe = int(cfg.get("max_dedupe", 1500))
    cfg["posted_urls"] = posted[-max_dedupe:]
    save_client(user_id, cfg)

    await update.message.reply_text(f"🧠 Seeded. Added {added} URLs to dedupe.")

async def interval_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not context.args:
        await update.message.reply_text("Usage: /interval 30")
        return

    try:
        minutes = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Interval must be a number (minutes). Example: /interval 30")
        return

    if minutes < 5 or minutes > 1440:
        await update.message.reply_text("Choose 5..1440 minutes.")
        return

    cfg["interval_minutes"] = minutes
    save_client(user_id, cfg)

    await update.message.reply_text(f"⏱ Interval saved: {minutes} min.")

async def autoposton_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    cfg["autopost_enabled"] = True
    save_client(user_id, cfg)
    await update.message.reply_text("🤖 Autopost ON.")

async def autopostoff_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    cfg["autopost_enabled"] = False
    save_client(user_id, cfg)
    await update.message.reply_text("🛑 Autopost OFF.")

async def setstyle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    text = update.message.text or ""
    parts = text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text("Usage: /setstyle paste your style prompt text after the command")
        return

    style = parts[1].strip()
    custom_style_path(user_id).write_text(style, encoding="utf-8")
    cfg["custom_style_file"] = custom_style_path(user_id).name
    save_client(user_id, cfg)

    await update.message.reply_text("✅ Style saved for your account.")

async def previewonce_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    # preview works even without subscription
    channel = cfg.get("channel")
    feeds = cfg.get("feeds", [])

    if not channel:
        await update.message.reply_text("Channel not set. Use /setchannel @channelusername")
        return
    if not feeds:
        await update.message.reply_text("No feeds. Add one: /addfeed <url>")
        return

    best = pick_newest_unseen(cfg)
    if not best:
        await update.message.reply_text("No new items found (or everything already posted).")
        return

    _, title, link, src = best
    summary = extract_summary_for_link(src, link)

    try:
        msg = ollama_generate_post(user_id, cfg, title, summary, link)
    except Exception:
        msg = f"📰 {title}\n🔗 {link}"

    await update.message.reply_text("🧪 Preview:\n\n" + msg)

async def fetchonce_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not subscription_ok(cfg):
        await update.message.reply_text("💳 Subscription inactive. Ask admin to activate your account.")
        return

    if not can_post_more(cfg):
        await update.message.reply_text("Daily limit reached.")
        return

    channel = cfg.get("channel")
    feeds = cfg.get("feeds", [])

    if not channel:
        await update.message.reply_text("Channel not set. Use /setchannel @channelusername")
        return
    if not feeds:
        await update.message.reply_text("No feeds. Add one: /addfeed <url>")
        return

    best = pick_newest_unseen(cfg)
    if not best:
        await update.message.reply_text("No new items found (or everything already posted).")
        return

    _, title, link, src = best
    summary = extract_summary_for_link(src, link)

    try:
        msg = ollama_generate_post(user_id, cfg, title, summary, link)
    except Exception:
        msg = f"📰 {title}\n🔗 {link}"

    try:
        await context.bot.send_message(chat_id=channel, text=msg, disable_web_page_preview=False)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to post: {type(e).__name__}")
        return

    cfg.setdefault("posted_urls", [])
    cfg["posted_urls"].append(link)
    max_dedupe = int(cfg.get("max_dedupe", 1500))
    cfg["posted_urls"] = cfg["posted_urls"][-max_dedupe:]
    bump_daily_count(cfg)

    save_client(user_id, cfg)
    await update.message.reply_text("✅ Posted 1 item.")


# ========= Admin commands =========
async def activate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if not is_admin(caller):
        await update.message.reply_text("Admin only.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /activate <user_id> <days>")
        return

    uid_raw, days_raw = context.args[0].strip(), context.args[1].strip()
    if not uid_raw.isdigit() or not days_raw.isdigit():
        await update.message.reply_text("Usage: /activate <user_id> <days>")
        return

    uid = int(uid_raw)
    days = int(days_raw)
    if days < 1 or days > 3650:
        await update.message.reply_text("Days: 1..3650")
        return

    cfg = load_client(uid)
    until = date.today() + timedelta(days=days)
    cfg["subscription_until"] = str(until)
    save_client(uid, cfg)

    await update.message.reply_text(f"✅ Activated user {uid} until {until}")

async def deactivate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if not is_admin(caller):
        await update.message.reply_text("Admin only.")
        return

    if len(context.args) < 1 or not context.args[0].strip().isdigit():
        await update.message.reply_text("Usage: /deactivate <user_id>")
        return

    uid = int(context.args[0].strip())
    cfg = load_client(uid)
    cfg["subscription_until"] = None
    save_client(uid, cfg)

    await update.message.reply_text(f"🛑 Deactivated user {uid}")

async def setlimit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if not is_admin(caller):
        await update.message.reply_text("Admin only.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setlimit <user_id> <limit>")
        return

    uid_raw, limit_raw = context.args[0].strip(), context.args[1].strip()
    if not uid_raw.isdigit() or not limit_raw.isdigit():
        await update.message.reply_text("Usage: /setlimit <user_id> <limit>")
        return

    uid = int(uid_raw)
    limit = int(limit_raw)

    if limit < 1 or limit > 5000:
        await update.message.reply_text("Limit range: 1..5000")
        return

    cfg = load_client(uid)
    cfg["daily_limit"] = limit
    save_client(uid, cfg)

    await update.message.reply_text(f"✅ User {uid} daily_limit set to {limit}")

async def setinterval_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if not is_admin(caller):
        await update.message.reply_text("Admin only.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setinterval <user_id> <minutes>")
        return

    uid_raw, minutes_raw = context.args[0].strip(), context.args[1].strip()
    if not uid_raw.isdigit() or not minutes_raw.isdigit():
        await update.message.reply_text("Usage: /setinterval <user_id> <minutes>")
        return

    uid = int(uid_raw)
    minutes = int(minutes_raw)

    if minutes < 5 or minutes > 1440:
        await update.message.reply_text("Minutes range: 5..1440")
        return

    cfg = load_client(uid)
    cfg["interval_minutes"] = minutes
    save_client(uid, cfg)

    await update.message.reply_text(f"✅ User {uid} interval set to {minutes} minutes")


# ========= Autopost loop (no JobQueue) =========
async def autopost_loop(app: Application) -> None:
    """
    Loop runs forever.
    Every 60 seconds it checks all clients and posts when their interval allows it.
    """
    # per-user last post time memory (runtime only)
    last_post_at: dict[int, datetime] = {}

    while True:
        try:
            ensure_dirs()
            now = datetime.now()

            for p in CLIENTS_DIR.glob("*.json"):
                try:
                    user_id = int(p.stem)
                except Exception:
                    continue

                cfg = load_client(user_id)

                if not cfg.get("autopost_enabled"):
                    continue
                if not subscription_ok(cfg):
                    continue

                channel = cfg.get("channel")
                feeds = cfg.get("feeds", [])
                if not channel or not feeds:
                    continue
                if not can_post_more(cfg):
                    continue

                interval_min = int(cfg.get("interval_minutes", 30))
                prev = last_post_at.get(user_id)
                if prev and (now - prev).total_seconds() < interval_min * 60:
                    continue

                best = pick_newest_unseen(cfg)
                if not best:
                    continue

                _, title, link, src = best
                summary = extract_summary_for_link(src, link)

                try:
                    msg = ollama_generate_post(user_id, cfg, title, summary, link)
                except Exception:
                    msg = f"📰 {title}\n🔗 {link}"

                try:
                    await app.bot.send_message(chat_id=channel, text=msg, disable_web_page_preview=False)
                except Exception:
                    continue

                cfg.setdefault("posted_urls", [])
                cfg["posted_urls"].append(link)
                max_dedupe = int(cfg.get("max_dedupe", 1500))
                cfg["posted_urls"] = cfg["posted_urls"][-max_dedupe:]
                bump_daily_count(cfg)

                save_client(user_id, cfg)
                last_post_at[user_id] = now

        except Exception:
            # keep loop alive even if one cycle fails
            pass

        await asyncio.sleep(60)


async def on_startup(app: Application) -> None:
    ensure_dirs()

    # create default style file if missing
    default_style = STYLES_DIR / DEFAULT_STYLE_FILE
    if not default_style.exists():
        default_style.write_text(
            "Ты автор телеграм-канала.\n"
            "Пиши коротко, по делу, без мусора.\n"
            "Не выдумывай факты.\n"
            "Ссылка в конце.\n",
            encoding="utf-8",
        )

    # start loop
    asyncio.create_task(autopost_loop(app))


def main() -> None:
    ensure_dirs()
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN missing in .env")

    app = Application.builder().token(TOKEN).post_init(on_startup).build()

    # user commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("setchannel", setchannel_cmd))
    app.add_handler(CommandHandler("addfeed", addfeed_cmd))
    app.add_handler(CommandHandler("feeds", feeds_cmd))
    app.add_handler(CommandHandler("seed", seed_cmd))
    app.add_handler(CommandHandler("interval", interval_cmd))
    app.add_handler(CommandHandler("autoposton", autoposton_cmd))
    app.add_handler(CommandHandler("autopostoff", autopostoff_cmd))
    app.add_handler(CommandHandler("previewonce", previewonce_cmd))
    app.add_handler(CommandHandler("fetchonce", fetchonce_cmd))
    app.add_handler(CommandHandler("setstyle", setstyle_cmd))
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("lang", lang_cmd))

    # admin commands
    app.add_handler(CommandHandler("activate", activate_cmd))
    app.add_handler(CommandHandler("deactivate", deactivate_cmd))
    app.add_handler(CommandHandler("setlimit", setlimit_cmd))
    app.add_handler(CommandHandler("setinterval", setinterval_admin_cmd))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
