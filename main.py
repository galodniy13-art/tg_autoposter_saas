import asyncio
import json
import os
import re
import threading
from pathlib import Path
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from http.server import BaseHTTPRequestHandler, HTTPServer

import feedparser
import requests
from dotenv import load_dotenv

from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import Application, CommandHandler, ContextTypes

# ===================== Paths / Env =====================
BASE_DIR = Path(__file__).parent
CLIENTS_DIR = BASE_DIR / "clients"
STYLES_DIR = BASE_DIR / "styles"

# local .env is used on your laptop; on Railway use Variables (env vars)
load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("BOT_TOKEN", "").strip()

PAY_CONTACTS = os.getenv("PAY_CONTACTS", "").strip()

# Admin IDs: comma separated list, example: "123,456"
ADMIN_IDS = set()
_raw_admins = os.getenv("ADMIN_IDS", "").strip()
if _raw_admins:
    for x in _raw_admins.split(","):
        x = x.strip()
        if x.isdigit():
            ADMIN_IDS.add(int(x))

# LLM provider:
# - ollama (local)
# - openai_compat (DeepSeek / OpenRouter / any OpenAI-compatible)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

# Ollama settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct").strip()

# OpenAI-compatible settings (DeepSeek later):
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat").strip()

DEFAULT_STYLE_FILE = "default_ru.txt"

# ===================== Texts (EN/RU) =====================
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
            "2) Choose mode\n"
            "   /mode rss  (news repost)\n"
            "   /mode creator  (original text posts)\n\n"
            "3A) RSS mode: add sources\n"
            "   /addfeed https://site.com/rss\n"
            "   Repeat /addfeed to add more.\n\n"
            "3B) Creator mode: set profile (who you are + what you sell)\n"
            "   /setprofile <paste your profile text>\n\n"
            "4) Set writing style (prompt)\n"
            "   /setstyle <paste your style>\n\n"
            "5) Preview (no posting)\n"
            "   /previewonce\n\n"
            "6) Post once to channel\n"
            "   /fetchonce\n\n"
            "Autopost (paid): ask admin to activate, then:\n"
            "/autoposton\n\n"
            "Your ID (send to admin): /status"
        ),
        "pay_msg": "💳 Subscription is required. Message: {contacts}",
        "no_contacts": "💳 Subscription is required. Ask admin for payment details.",
        "sub_inactive": "💳 Subscription inactive. Message admin to activate your account.",
        "admin_only": "Admin only.",
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
            "2) Выберите режим\n"
            "   /mode rss  (репост новостей)\n"
            "   /mode creator  (оригинальные текстовые посты)\n\n"
            "3A) RSS-режим: добавьте источники\n"
            "   /addfeed https://site.com/rss\n"
            "   Повторяйте /addfeed, чтобы добавить ещё.\n\n"
            "3B) Creator-режим: задайте профиль (кто вы + что продаёте)\n"
            "   /setprofile <вставьте профиль>\n\n"
            "4) Задайте стиль (prompt)\n"
            "   /setstyle <вставьте стиль>\n\n"
            "5) Превью (ничего не публикует)\n"
            "   /previewonce\n\n"
            "6) Опубликовать один раз в канал\n"
            "   /fetchonce\n\n"
            "Автопостинг (платно): напишите админу для активации, потом:\n"
            "/autoposton\n\n"
            "Ваш ID (отправьте админу): /status"
        ),
        "pay_msg": "💳 Нужна подписка. Напишите: {contacts}",
        "no_contacts": "💳 Нужна подписка. Попросите у админа реквизиты для оплаты.",
        "sub_inactive": "💳 Подписка не активна. Напишите админу, чтобы включить.",
        "admin_only": "Только для админа.",
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

# ===================== Default client config =====================
DEFAULT_CLIENT = {
    "language": None,  # "en" / "ru"

    "mode": "rss",  # "rss" or "creator"
    "creator_profile": "",

    "channel": None,
    "feeds": [],
    "posted_urls": [],

    "autopost_enabled": False,
    "interval_minutes": 30,

    "daily_limit": 10,
    "daily_count": 0,
    "daily_date": str(date.today()),

    "max_dedupe": 1500,
    "fetch_entries_per_feed": 15,

    "style_file": DEFAULT_STYLE_FILE,
    "subscription_until": None,  # YYYY-MM-DD
}

# ===================== Storage helpers =====================
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
            raise ValueError("client config not dict")
    except Exception:
        broken = p.read_text(encoding="utf-8", errors="ignore")
        (CLIENTS_DIR / f"{user_id}.broken.json").write_text(broken, encoding="utf-8", errors="ignore")
        cfg = dict(DEFAULT_CLIENT)
        save_client(user_id, cfg)
        return cfg

    for k, v in DEFAULT_CLIENT.items():
        cfg.setdefault(k, v)
    return cfg

def save_client(user_id: int, cfg: dict) -> None:
    client_path(user_id).write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

# ===================== Utility =====================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def clean_text(s: str) -> str:
    if not s:
        return ""
    return " ".join(str(s).replace("\n", " ").split()).strip()

def normalize_url(url: str) -> str:
    parts = urlsplit(url)
    q = parse_qsl(parts.query, keep_blank_values=True)

    banned_exact = {
        "at_medium", "at_campaign", "at_bbc_team", "at_link_origin",
        "fbclid", "gclid", "igshid", "mc_cid", "mc_eid",
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    }

    new_q = []
    for k, v in q:
        kl = k.lower()
        if kl in banned_exact:
            continue
        if kl.startswith("utm_"):
            continue
        new_q.append((k, v))

    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(new_q, doseq=True), ""))

def ensure_daily_counter(cfg: dict) -> dict:
    today = str(date.today())
    if cfg.get("daily_date") != today:
        cfg["daily_date"] = today
        cfg["daily_count"] = 0
    return cfg

def can_post_more(cfg: dict) -> bool:
    cfg = ensure_daily_counter(cfg)
    return int(cfg.get("daily_count", 0)) < int(cfg.get("daily_limit", 10))

def bump_daily_count(cfg: dict) -> None:
    cfg = ensure_daily_counter(cfg)
    cfg["daily_count"] = int(cfg.get("daily_count", 0)) + 1

def subscription_ok(cfg: dict) -> bool:
    until = (cfg.get("subscription_until") or "").strip()
    if not until:
        return False
    try:
        d = datetime.strptime(until, "%Y-%m-%d").date()
    except Exception:
        return False
    return date.today() <= d

def get_style_prompt(user_id: int, cfg: dict) -> str:
    cpath = custom_style_path(user_id)
    if cpath.exists():
        txt = cpath.read_text(encoding="utf-8", errors="ignore").strip()
        if txt:
            return txt

    style_file = (cfg.get("style_file") or DEFAULT_STYLE_FILE).strip()
    spath = STYLES_DIR / style_file
    if spath.exists():
        return spath.read_text(encoding="utf-8", errors="ignore").strip()

    return (
        "Ты автор телеграм-канала.\n"
        "Пиши живо, по-человечески.\n"
        "Факты не выдумывай. Ссылку ставь в конце.\n"
    )

def sanitize_llm_post(text: str, link: str) -> str:
    t = (text or "").replace("\r", "").strip()

    # remove any URLs model included (we add exactly one at end)
    t = re.sub(r"https?://\S+", "", t).strip()
    # remove numbering prefixes
    t = re.sub(r"(?m)^\s*\d+\s*[\)\.\-:]\s*", "", t).strip()
    # collapse blank lines
    t = re.sub(r"\n{3,}", "\n\n", t).strip()

    if not t:
        t = "📌 Коротко: в источнике мало деталей."

    return (t.rstrip() + "\n\n" + f"🔗 {link}")[:900]

# ===================== RSS helpers =====================
def pick_newest_unseen(cfg: dict):
    feeds = cfg.get("feeds", [])
    posted = set(cfg.get("posted_urls", []))
    best = None  # (published, title, link_normalized, feed_url)

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

# ===================== LLM providers =====================
def ollama_generate_post(user_id: int, cfg: dict, title: str, summary: str, link: str) -> str:
    style_prompt = get_style_prompt(user_id, cfg)
    title = clean_text(title)
    summary = clean_text(summary)

    prompt = (
        style_prompt + "\n\n"
        "Сделай пост для Telegram по этим данным. Факты не выдумывай. Ссылку поставь в конце.\n\n"
        f"Заголовок: {title}\n"
        f"Текст: {summary}\n"
        f"Ссылка: {link}\n"
    )

    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    txt = clean_text(data.get("response", ""))
    return sanitize_llm_post(txt, link)

def openai_compat_generate_post(user_id: int, cfg: dict, title: str, summary: str, link: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY missing (set it in host variables)")

    style_prompt = get_style_prompt(user_id, cfg)
    title = clean_text(title)
    summary = clean_text(summary)

    user_content = (
        f"Заголовок: {title}\n"
        f"Текст: {summary}\n"
        f"Ссылка: {link}\n\n"
        "Сделай пост для Telegram по стилю system. Факты не выдумывай. Ссылку ставь в конце."
    )

    url = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": style_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
    }

    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    txt = data["choices"][0]["message"]["content"]
    return sanitize_llm_post(clean_text(txt), link)

def llm_generate_post(user_id: int, cfg: dict, title: str, summary: str, link: str) -> str:
    if LLM_PROVIDER == "openai_compat":
        return openai_compat_generate_post(user_id, cfg, title, summary, link)
    return ollama_generate_post(user_id, cfg, title, summary, link)

# ===================== Creator mode (text-only) =====================
def creator_make_post(user_id: int, cfg: dict) -> str:
    style_prompt = get_style_prompt(user_id, cfg)
    profile = (cfg.get("creator_profile") or "").strip()

    if not profile:
        # minimal fallback
        profile = "Эксперт/блогер. Пишет полезные короткие посты для своей аудитории."

    prompt = (
        style_prompt + "\n\n"
        "Ты пишешь оригинальный пост (НЕ новость). Текст для Telegram.\n"
        "Цель: полезный/интересный пост для аудитории автора.\n"
        "Без ссылок. Без выдуманных фактов про внешние новости.\n\n"
        f"Профиль автора:\n{profile}\n\n"
        "Сгенерируй 1 пост."
    )

    if LLM_PROVIDER == "openai_compat":
        url = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": style_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.85,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        txt = data["choices"][0]["message"]["content"]
        return clean_text(txt)[:900]

    # ollama creator
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return clean_text(data.get("response", ""))[:900]

# ===================== Commands =====================
async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not context.args:
        await update.message.reply_text(TEXTS["en"]["choose_lang"])
        return

    choice = context.args[0].strip().lower()
    if choice not in ("en", "ru"):
        await update.message.reply_text(TEXTS["en"]["choose_lang"])
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
    cfg = ensure_daily_counter(load_client(user_id))
    sub = cfg.get("subscription_until") or "inactive"

    await update.message.reply_text(
        f"👤 Your ID: {user_id}\n"
        f"🌍 Lang: {cfg.get('language')}\n"
        f"🧩 Mode: {cfg.get('mode')}\n"
        f"📌 Channel: {cfg.get('channel') or 'not set'}\n"
        f"🧾 Feeds: {len(cfg.get('feeds', []))}\n"
        f"🤖 Autopost: {'ON' if cfg.get('autopost_enabled') else 'OFF'}\n"
        f"⏱ Interval: {cfg.get('interval_minutes')} min\n"
        f"📅 Daily: {cfg.get('daily_count')}/{cfg.get('daily_limit')} (date {cfg.get('daily_date')})\n"
        f"💳 Subscription until: {sub}\n"
        f"🧠 LLM_PROVIDER: {LLM_PROVIDER}"
    )

async def mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not context.args:
        await update.message.reply_text("Usage: /mode rss OR /mode creator")
        return

    m = context.args[0].strip().lower()
    if m not in ("rss", "creator"):
        await update.message.reply_text("Usage: /mode rss OR /mode creator")
        return

    cfg["mode"] = m
    save_client(user_id, cfg)
    await update.message.reply_text(f"✅ Mode set: {m}")

async def setprofile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    txt = update.message.text or ""
    parts = txt.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text("Usage: /setprofile paste your profile text after the command")
        return

    cfg["creator_profile"] = parts[1].strip()
    save_client(user_id, cfg)
    await update.message.reply_text("✅ Profile saved for creator mode.")

async def setstyle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    txt = update.message.text or ""
    parts = txt.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text("Usage: /setstyle paste your style text after the command")
        return

    style = parts[1].strip()
    custom_style_path(user_id).write_text(style, encoding="utf-8")
    save_client(user_id, cfg)
    await update.message.reply_text("✅ Style saved.")

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

    await update.message.reply_text("🧾 Feeds:\n" + "\n".join([f"{i+1}) {u}" for i, u in enumerate(feeds)]))
async def delfeed_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    feeds = cfg.get("feeds", [])

    if not feeds:
        await update.message.reply_text("No feeds to delete.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /delfeed <number>. Example: /delfeed 1")
        return

    try:
        idx = int(context.args[0]) - 1
    except ValueError:
        await update.message.reply_text("Usage: /delfeed <number>. Example: /delfeed 1")
        return

    if idx < 0 or idx >= len(feeds):
        await update.message.reply_text(f"Wrong number. Use 1..{len(feeds)} (see /feeds).")
        return

    removed = feeds.pop(idx)
    cfg["feeds"] = feeds
    save_client(user_id, cfg)
    await update.message.reply_text(f"✅ Deleted feed:\n{removed}\n\nRemaining: {len(feeds)}")

async def clearfeeds_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    cfg["feeds"] = []
    save_client(user_id, cfg)
    await update.message.reply_text("✅ All feeds removed.")

async def previewonce_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if cfg.get("mode") == "creator":
        msg = creator_make_post(user_id, cfg)
        await update.message.reply_text("🧪 Preview:\n\n" + msg)
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
    msg = llm_generate_post(user_id, cfg, title, summary, link)
    await update.message.reply_text("🧪 Preview:\n\n" + msg)

async def fetchonce_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not subscription_ok(cfg):
        await update.message.reply_text(tr(cfg, "sub_inactive") + "\n" + pay_line(cfg))
        return

    if not can_post_more(cfg):
        await update.message.reply_text("Daily limit reached.")
        return

    channel = cfg.get("channel")
    if not channel:
        await update.message.reply_text("Channel not set. Use /setchannel @channelusername")
        return

    if cfg.get("mode") == "creator":
        msg = creator_make_post(user_id, cfg)
        await context.bot.send_message(chat_id=channel, text=msg)
        bump_daily_count(cfg)
        save_client(user_id, cfg)
        await update.message.reply_text("✅ Posted 1 creator post.")
        return

    feeds = cfg.get("feeds", [])
    if not feeds:
        await update.message.reply_text("No feeds. Add one: /addfeed <url>")
        return

    best = pick_newest_unseen(cfg)
    if not best:
        await update.message.reply_text("No new items found (or everything already posted).")
        return

    _, title, link, src = best
    summary = extract_summary_for_link(src, link)
    msg = llm_generate_post(user_id, cfg, title, summary, link)

    await context.bot.send_message(chat_id=channel, text=msg, disable_web_page_preview=False)

    cfg.setdefault("posted_urls", [])
    cfg["posted_urls"].append(link)
    cfg["posted_urls"] = cfg["posted_urls"][-int(cfg.get("max_dedupe", 1500)):]
    bump_daily_count(cfg)
    save_client(user_id, cfg)
    await update.message.reply_text("✅ Posted 1 item.")

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

# ===================== Admin commands =====================
async def activate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if not is_admin(caller):
        await update.message.reply_text(tr(load_client(caller), "admin_only"))
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
    cfg["subscription_until"] = str(date.today() + timedelta(days=days))
    save_client(uid, cfg)
    await update.message.reply_text(f"✅ Activated user {uid} until {cfg['subscription_until']}")

async def deactivate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if not is_admin(caller):
        await update.message.reply_text(tr(load_client(caller), "admin_only"))
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
        await update.message.reply_text(tr(load_client(caller), "admin_only"))
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
        await update.message.reply_text(tr(load_client(caller), "admin_only"))
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

# ===================== Autopost loop =====================
async def autopost_loop(app: Application) -> None:
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
                if not can_post_more(cfg):
                    continue

                channel = cfg.get("channel")
                if not channel:
                    continue

                interval_min = int(cfg.get("interval_minutes", 30))
                prev = last_post_at.get(user_id)
                if prev and (now - prev).total_seconds() < interval_min * 60:
                    continue

                # creator mode
                if cfg.get("mode") == "creator":
                    msg = creator_make_post(user_id, cfg)
                    await app.bot.send_message(chat_id=channel, text=msg)
                    bump_daily_count(cfg)
                    save_client(user_id, cfg)
                    last_post_at[user_id] = now
                    continue

                # rss mode
                feeds = cfg.get("feeds", [])
                if not feeds:
                    continue

                best = pick_newest_unseen(cfg)
                if not best:
                    continue

                _, title, link, src = best
                summary = extract_summary_for_link(src, link)
                msg = llm_generate_post(user_id, cfg, title, summary, link)

                await app.bot.send_message(chat_id=channel, text=msg, disable_web_page_preview=False)

                cfg.setdefault("posted_urls", [])
                cfg["posted_urls"].append(link)
                cfg["posted_urls"] = cfg["posted_urls"][-int(cfg.get("max_dedupe", 1500)):]
                bump_daily_count(cfg)
                save_client(user_id, cfg)
                last_post_at[user_id] = now

        except Exception:
            pass

        await asyncio.sleep(60)

# ===================== Health server (optional) =====================
def start_health_server() -> None:
    port = int(os.getenv("PORT", "8080"))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/health"):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"ok")
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            return

    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

async def on_startup(app: Application) -> None:
    ensure_dirs()

    default_style = STYLES_DIR / DEFAULT_STYLE_FILE
    if not default_style.exists():
        default_style.write_text(
            "Ты автор телеграм-канала. Пиши живо и по-человечески.\n"
            "Факты не выдумывай. Ссылку ставь в конце.\n",
            encoding="utf-8",
        )

    # Start background task
    asyncio.create_task(autopost_loop(app))

def main() -> None:
    ensure_dirs()

    if not TOKEN:
        raise RuntimeError("BOT_TOKEN missing (set BOT_TOKEN env var in Railway Variables)")

    # Health server helps many hosts; harmless locally
    threading.Thread(target=start_health_server, daemon=True).start()

    app = Application.builder().token(TOKEN).post_init(on_startup).build()

    # core
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("lang", lang_cmd))
    app.add_handler(CommandHandler("status", status_cmd))

    # setup
    app.add_handler(CommandHandler("mode", mode_cmd))
    app.add_handler(CommandHandler("setprofile", setprofile_cmd))
    app.add_handler(CommandHandler("setstyle", setstyle_cmd))
    app.add_handler(CommandHandler("setchannel", setchannel_cmd))
    app.add_handler(CommandHandler("addfeed", addfeed_cmd))
    app.add_handler(CommandHandler("feeds", feeds_cmd))
    app.add_handler(CommandHandler("delfeed", delfeed_cmd))
    app.add_handler(CommandHandler("clearfeeds", clearfeeds_cmd))

    # posting
    app.add_handler(CommandHandler("previewonce", previewonce_cmd))
    app.add_handler(CommandHandler("fetchonce", fetchonce_cmd))
    app.add_handler(CommandHandler("interval", interval_cmd))
    app.add_handler(CommandHandler("autoposton", autoposton_cmd))
    app.add_handler(CommandHandler("autopostoff", autopostoff_cmd))

    # admin
    app.add_handler(CommandHandler("activate", activate_cmd))
    app.add_handler(CommandHandler("deactivate", deactivate_cmd))
    app.add_handler(CommandHandler("setlimit", setlimit_cmd))
    app.add_handler(CommandHandler("setinterval", setinterval_admin_cmd))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()


