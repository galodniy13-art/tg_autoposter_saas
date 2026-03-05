import asyncio
import json
import os
import re
import threading
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from http.server import BaseHTTPRequestHandler, HTTPServer

import feedparser
import requests
from dotenv import load_dotenv

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from mode_ui import build_mode_buttons, mode_set_text
from keyboards import (
    build_lang_keyboard,
    build_main_menu_minimal,
    build_setup_submenu,
    build_modes_menu,
    build_payment_menu,
)

from texts import TEXTS as UI_TEXTS
from telegram.constants import ChatMemberStatus
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ===================== Paths / Env =====================
BASE_DIR = Path(__file__).parent
CLIENTS_DIR = BASE_DIR / "clients"
STYLES_DIR = BASE_DIR / "styles"

# local .env is used on your laptop; on Railway use Variables (env vars)
load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("BOT_TOKEN", "").strip()

PAY_CONTACTS = os.getenv("PAY_CONTACTS", "").strip()

def env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default

# Owner IDs: comma separated list, example: "123,456"
OWNER_TELEGRAM_IDS = set()
_raw_owner_ids = os.getenv("OWNER_TELEGRAM_IDS", "").strip()
if _raw_owner_ids:
    for x in _raw_owner_ids.split(","):
        x = x.strip()
        if x.isdigit():
            OWNER_TELEGRAM_IDS.add(int(x))

# Pricing constants
BASIC_USD = env_int("BASIC_USD", 9)
PRO_USD = env_int("PRO_USD", 19)
ELITE_USD = env_int("ELITE_USD", 39)

BASIC_RUB = env_int("BASIC_RUB", 990)
PRO_RUB = env_int("PRO_RUB", 1990)
ELITE_RUB = env_int("ELITE_RUB", 3990)

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
        "btn_lang": "🌍 Language / Язык",
"btn_setup": "⚙️ Setup",
"btn_setchannel": "📌 Set channel",
"btn_addfeed": "🧾 Add feed",
"btn_setstyle": "✍️ Set style",
"btn_preview": "🧪 Preview",
"btn_post": "🚀 Post now",
"btn_on": "🤖 Autopost ON",
"btn_off": "🛑 OFF",
        "btn_pay": "💳 Payment",
"btn_status": "ℹ️ Status",
"btn_schedule": "🕒 Schedule",
"btn_showstyle": "📄 Show style",
"btn_resetstyle": "♻️ Reset style",
"btn_unsetchannel": "🧹 Unset channel",
"btn_materials": "📚 Materials",
        "menu_title": "✅ Menu. Choose what you want to do:",
"setup_check": (
    "⚙️ Setup checklist:\n\n"
    "1) Channel connected?\n"
    "   Use: /setchannel @yourchannel\n\n"
    "2) Mode chosen?\n"
    "   /mode rss  or  /mode creator\n\n"
    "3) RSS mode: feeds added?\n"
    "   /addfeed https://site.com/rss\n\n"
    "4) Style set?\n"
    "   /setstyle <paste your style prompt>\n\n"
    "5) Test preview:\n"
    "   /previewonce\n\n"
    "6) Paid posting:\n"
    "   Ask admin to activate, then /fetchonce or /autoposton"
),
"ui_addfeed": "Paste your RSS link like:\n/addfeed https://site.com/rss",
"ui_setchannel": "Type your channel username like:\n/setchannel @yourchannel\n\nBot must be admin in the channel.",
"ui_setstyle": "Paste your style prompt like:\n/setstyle <your text>\n\nExample: language, tone, length, emojis, forbidden topics.",
"ui_pay": "Payment / activation:\n{pay}",
"ui_schedule": "Schedule:\n{schedule}\n\nCommands:\n/schedule\n/schedule add 09:00\n/schedule remove 09:00\n/schedule clear\n/schedule on\n/schedule off",
"ui_materials": "📚 Useful materials:\n• Prompt guide (RU): https://telegra.ph/Instrukciya-po-polzovaniyu-botom-i-poleznye-materialy-02-27\n• RSS feed ideas (EN): https://rss.app/new-rss-feed/create-twitter-rss-feed",
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
        "btn_lang": "🌍 Язык",
"btn_setup": "⚙️ Настройка",
"btn_setchannel": "📌 Канал",
"btn_addfeed": "🧾 Лента (RSS)",
"btn_setstyle": "✍️ Стиль",
"btn_preview": "🧪 Превью",
"btn_post": "🚀 Опубликовать",
"btn_on": "🤖 Автопост ВКЛ",
"btn_off": "🛑 ВЫКЛ",
        "btn_pay": "💳 Оплата",
"btn_status": "ℹ️ Статус",
"btn_schedule": "🕒 Расписание",
"btn_showstyle": "📄 Показать стиль",
"btn_resetstyle": "♻️ Сбросить стиль",
"btn_unsetchannel": "🧹 Отключить канал",
"btn_materials": "📚 Материалы",
        "menu_title": "✅ Меню. Выберите действие:",
"setup_check": (
    "⚙️ Чеклист настройки:\n\n"
    "1) Канал подключён?\n"
    "   /setchannel @вашканал\n\n"
    "2) Режим выбран?\n"
    "   /mode rss  или  /mode creator\n\n"
    "3) RSS-режим: ленты добавлены?\n"
    "   /addfeed https://site.com/rss\n\n"
    "4) Стиль задан?\n"
    "   /setstyle <вставьте prompt>\n\n"
    "5) Тест превью:\n"
    "   /previewonce\n\n"
    "6) Публикации (платно):\n"
    "   Активация админом, потом /fetchonce или /autoposton"
),
"ui_addfeed": "Вставьте RSS ссылку так:\n/addfeed https://site.com/rss",
"ui_setchannel": "Напишите юзернейм канала так:\n/setchannel @вашканал\n\nБот должен быть админом канала.",
"ui_setstyle": "Вставьте prompt стиля так:\n/setstyle <ваш текст>\n\nПример: язык, тон, длина, эмодзи, запреты.",
"ui_pay": "Оплата / активация:\n{pay}",
"ui_schedule": "Расписание:\n{schedule}\n\nКоманды:\n/schedule\n/schedule add 09:00\n/schedule remove 09:00\n/schedule clear\n/schedule on\n/schedule off",
"ui_materials": "📚 Полезные материалы:\n• Инструкция и создание промптов (RU): https://telegra.ph/Instrukciya-po-polzovaniyu-botom-i-poleznye-materialy-02-27\n• Идеи RSS-лент (EN): https://rss.app/new-rss-feed/create-twitter-rss-feed",
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


def ui_text(cfg: dict, key: str) -> str:
    lang = (cfg.get("language") or "en").lower()
    if lang not in UI_TEXTS:
        lang = "en"
    return UI_TEXTS[lang].get(key, UI_TEXTS["en"].get(key, key))


def creative_mode_allowed(cfg: dict) -> bool:
    return subscription_ok(cfg) and (cfg.get("subscription_plan") in {"PRO", "ELITE"})

def detect_lang(update: Update | None, cfg: dict | None = None) -> str:
    cfg = cfg or {}
    user = update.effective_user if update else None
    language_code = (getattr(user, "language_code", "") or "").lower()
    if language_code.startswith("ru"):
        return "ru"

    cfg_lang = (cfg.get("language") or "").lower()
    if cfg_lang in ("en", "ru"):
        return cfg_lang
    return "en"


def subscription_offer_text(lang: str) -> str:
    if lang not in UI_TEXTS:
        lang = "en"
    return UI_TEXTS[lang]["payment_offer"]
def pay_line(update: Update | None, cfg: dict) -> str:
    lang = detect_lang(update, cfg)
    return subscription_offer_text(lang)

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
    "schedule_enabled": False,
    "schedule_times": [],
    "last_schedule_date": None,
    "last_schedule_time": None,

    "daily_limit": 10,
    "daily_count": 0,
    "daily_date": str(date.today()),

    "max_dedupe": 1500,
    "fetch_entries_per_feed": 15,

    "style_file": DEFAULT_STYLE_FILE,
    "subscription_until": None,  # YYYY-MM-DD
    "subscription_plan": "FREE",
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
        "Не выдумывай факты.\n"
    )

def sanitize_llm_post(text: str, link: str) -> str:
    t = (text or "").replace("\r", "").strip()

    # remove any URLs model included (we add exactly one at end)
    t = re.sub(r"https?://\S+", "", t).strip()
    # remove numbering prefixes
    t = re.sub(r"(?m)^\s*\d+\s*[\)\.\-:]\s*", "", t).strip()
    # remove link label leftovers
    t = re.sub(r"(?im)^\s*(ссылка|link)\s*:\s*.*$", "", t)
    t = re.sub(r"(?im)^\s*\[\s*link\s*\]\s*$", "", t)
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
        "Rewrite this into a natural short Telegram post in the same style and language. "
        "Do not invent facts beyond the summary. Include the source URL once at the end.\n\n"
        f"Title: {title}\n"
        f"Summary: {summary}\n"
        f"Source URL: {link}\n"
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
        f"Title: {title}\n"
        f"Summary: {summary}\n"
        f"Source URL: {link}\n\n"
        "Rewrite this as a natural short Telegram post in the system style. "
        "Do not invent facts beyond the summary. Include the source URL once at the end."
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
        "Write one original Telegram post in the system style and in the user's language. "
        "Natural tone, no external news, no links.\n\n"
        f"Creator profile:\n{profile}\n"
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

def ui_text(cfg: dict | None, key: str) -> str:
    lang = ((cfg or {}).get("language") or "en").lower()
    if lang not in UI_TEXTS:
        lang = "en"
    return UI_TEXTS[lang].get(key, UI_TEXTS["en"].get(key, key))


def build_main_menu(cfg: dict) -> InlineKeyboardMarkup:
    lang = (cfg.get("language") or "en").lower()
    if lang not in UI_TEXTS:
        lang = "en"
    return build_main_menu_minimal(UI_TEXTS[lang])


def build_setup_menu(cfg: dict) -> InlineKeyboardMarkup:
    lang = (cfg.get("language") or "en").lower()
    if lang not in UI_TEXTS:
        lang = "en"
    return build_setup_submenu(UI_TEXTS[lang])
    keyboard = [
        [InlineKeyboardButton(ui_text(cfg, "btn_lang"), callback_data="ui:lang")],
        [InlineKeyboardButton(tr(cfg, "btn_setup"), callback_data="ui:setup")],
        [InlineKeyboardButton(ui_text(cfg, "btn_modes"), callback_data="ui:modes")],
        build_mode_buttons(cfg),
        [
            InlineKeyboardButton(tr(cfg, "btn_setchannel"), callback_data="ui:setchannel"),
            InlineKeyboardButton(tr(cfg, "btn_unsetchannel"), callback_data="ui:unsetchannel"),
        ],
        [
            InlineKeyboardButton(tr(cfg, "btn_addfeed"), callback_data="ui:addfeed"),
            InlineKeyboardButton(tr(cfg, "btn_schedule"), callback_data="ui:schedule"),
        ],
        [
            InlineKeyboardButton(tr(cfg, "btn_setstyle"), callback_data="ui:setstyle"),
            InlineKeyboardButton(tr(cfg, "btn_showstyle"), callback_data="ui:showstyle"),
        ],
        [
            InlineKeyboardButton(tr(cfg, "btn_resetstyle"), callback_data="ui:resetstyle"),
            InlineKeyboardButton(tr(cfg, "btn_preview"), callback_data="ui:preview"),
        ],
        [InlineKeyboardButton(tr(cfg, "btn_post"), callback_data="ui:fetchonce")],
        [
            InlineKeyboardButton(tr(cfg, "btn_pay"), callback_data="ui:pay"),
            InlineKeyboardButton(tr(cfg, "btn_status"), callback_data="ui:status"),
        ],
        [InlineKeyboardButton(tr(cfg, "btn_materials"), callback_data="ui:materials")],
    ]
    return InlineKeyboardMarkup(keyboard)


def ui_pack(cfg: dict) -> dict:
    lang = (cfg.get("language") or "en").lower()
    return UI_TEXTS.get(lang, UI_TEXTS["en"])


def build_main_menu_clean(cfg: dict) -> InlineKeyboardMarkup:
    return build_main_menu_minimal(ui_pack(cfg))


def build_setup_menu(cfg: dict) -> InlineKeyboardMarkup:
    return build_setup_submenu(ui_pack(cfg), bool(cfg.get("autopost_enabled")))


def build_lang_menu() -> InlineKeyboardMarkup:
    return build_lang_keyboard()


async def reply_ui(update: Update, text: str, cfg: dict, show_menu: bool = True) -> None:
    markup = build_main_menu_clean(cfg) if show_menu else None

    if update.callback_query:
        q = update.callback_query
        await q.answer()
        try:
            await q.edit_message_text(text=text, reply_markup=markup)
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=markup)
        return

    if update.message:
        await update.message.reply_text(text=text, reply_markup=markup)


async def send_menu(update: Update, cfg: dict, text: str) -> None:
    await reply_ui(update, text, cfg, show_menu=True)


def validate_hhmm(value: str) -> bool:
    if not re.fullmatch(r"\d{2}:\d{2}", value or ""):
        return False
    hh, mm = value.split(":", 1)
    return 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59


def schedule_summary(cfg: dict) -> str:
    enabled = "ON" if cfg.get("schedule_enabled") else "OFF"
    times = cfg.get("schedule_times", [])
    times_text = ", ".join(times) if times else "(empty)"
    return f"Status: {enabled}\nTimes: {times_text}"


def feeds_overview(cfg: dict) -> str:
    feeds = cfg.get("feeds", [])
    if not feeds:
        return "No feeds. Add one: /addfeed <url>"
    return "🧾 Feeds:\n" + "\n".join([f"{i+1}) {u}" for i, u in enumerate(feeds)])


def build_feeds_menu(cfg: dict) -> InlineKeyboardMarkup:
    rows = []
    for idx, url in enumerate(cfg.get("feeds", []), start=1):
        short = (url[:28] + "…") if len(url) > 29 else url
        rows.append([InlineKeyboardButton(f"❌ {idx}", callback_data=f"ui:delfeed:{idx}"), InlineKeyboardButton(short, callback_data="ui:addfeed")])
    rows.append([InlineKeyboardButton("➕ " + tr(cfg, "btn_addfeed"), callback_data="ui:addfeed")])
    return InlineKeyboardMarkup(rows)

# ===================== Commands =====================
async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not context.args:
        await update.message.reply_text(ui_text(cfg, "choose_lang"), reply_markup=build_lang_menu())
        return

    choice = context.args[0].strip().lower()
    if choice not in ("en", "ru"):
        await update.message.reply_text(ui_text(cfg, "choose_lang"), reply_markup=build_lang_menu())
        return

    cfg["language"] = choice
    save_client(user_id, cfg)
    await send_menu(update, cfg, tr(cfg, "menu_title") + "\n\n" + pay_line(update, cfg))

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not cfg.get("language"):
        await update.message.reply_text(ui_text(cfg, "choose_lang"), reply_markup=build_lang_menu())
        return

    lang = (cfg.get("language") or "en").lower()
    if lang not in UI_TEXTS:
        lang = "en"
    await send_menu(update, cfg, UI_TEXTS[lang]["start_welcome"])

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = ensure_daily_counter(load_client(user_id))
    sub = cfg.get("subscription_until") or "inactive"

    text = (
        f"👤 Your ID: {user_id}\n"
        f"🌍 Lang: {cfg.get('language')}\n"
        f"🧩 Mode: {cfg.get('mode')}\n"
        f"📌 Channel: {cfg.get('channel') or 'not set'}\n"
        f"🧾 Feeds: {len(cfg.get('feeds', []))}\n"
        f"🤖 Autopost: {'ON' if cfg.get('autopost_enabled') else 'OFF'}\n"
        f"🕒 Schedule: {'ON' if cfg.get('schedule_enabled') else 'OFF'} ({', '.join(cfg.get('schedule_times', [])) or 'empty'})\n"
        f"⏱ Interval: {cfg.get('interval_minutes')} min\n"
        f"📅 Daily: {cfg.get('daily_count')}/{cfg.get('daily_limit')} (date {cfg.get('daily_date')})\n"
        f"💳 Subscription until: {sub}\n"
        f"🧠 LLM_PROVIDER: {LLM_PROVIDER}"
    )
    await reply_ui(update, text, cfg, show_menu=True)

async def materials_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    await send_menu(update, cfg, tr(cfg, "ui_materials"))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not cfg.get("language"):
        await update.message.reply_text(ui_text(cfg, "choose_lang"), reply_markup=build_lang_menu())
        return

    await send_menu(update, cfg, tr(cfg, "menu_title") + "\n\n" + pay_line(update, cfg))

async def ui_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    user_id = q.from_user.id
    cfg = load_client(user_id)

    data = q.data or ""

    if data == "ui:lang":
        await q.answer()
        await q.message.reply_text(
            ui_text(cfg, "choose_lang"),
            reply_markup=build_lang_menu(),
        )
        return

    elif data.startswith("ui:setlang:"):
        choice = data.split(":", 2)[2].strip().lower()
        if choice in ("en", "ru"):
            cfg["language"] = choice
            save_client(user_id, cfg)
            await reply_ui(
                update,
                tr(cfg, "lang_set") + "\n\n" + tr(cfg, "menu_title") + "\n\n" + pay_line(update, cfg),
            )
            return
        await q.answer()
        return

if data == "ui:setup":
    try:
        await q.answer()
        await q.edit_message_text(
            text=ui_text(cfg, "setup_menu_title"),
            reply_markup=build_setup_menu(cfg),
        )
    except BadRequest:
        await q.message.reply_text(
            text=ui_text(cfg, "setup_menu_title"),
            reply_markup=build_setup_menu(cfg),
        )
    return

elif data == "ui:backmain":
    await send_menu(
        update,
        cfg,
        tr(cfg, "menu_title") + "\n\n" + pay_line(update, cfg),
    )
    return

elif data == "ui:autoposttoggle":
    cfg["autopost_enabled"] = not bool(cfg.get("autopost_enabled"))
    save_client(user_id, cfg)
    await q.answer()
    try:
        await q.edit_message_text(
            text=ui_text(cfg, "setup_menu_title"),
            reply_markup=build_setup_menu(cfg),
        )
    except BadRequest:
        await q.message.reply_text(
            text=ui_text(cfg, "setup_menu_title"),
            reply_markup=build_setup_menu(cfg),
        )
    return

    if data == "ui:modes":
        lang = (cfg.get("language") or "en").lower()
        if lang not in UI_TEXTS:
            lang = "en"
        await send_menu(update, cfg, UI_TEXTS[lang].get("modes_help", UI_TEXTS["en"].get("modes_help", "")))
        return

    if data == "ui:help":
        await send_menu(update, cfg, tr(cfg, "setup_check"))
        return

    if data == "ui:feedsdelete":
        text = feeds_overview(cfg)
        try:
            await q.answer()
            await q.edit_message_text(text=text, reply_markup=build_feeds_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_feeds_menu(cfg))
        return

    if data == "ui:setchannel":
        await send_menu(update, cfg, tr(cfg, "ui_setchannel"))
        return

    if data == "ui:addfeed":
        text = tr(cfg, "ui_addfeed") + "\n\n" + feeds_overview(cfg)
        try:
            await q.answer()
            await q.edit_message_text(text=text, reply_markup=build_feeds_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_feeds_menu(cfg))
        return

    if data == "ui:unsetchannel":
        cfg["channel"] = None
        save_client(user_id, cfg)
        await send_menu(update, cfg, "✅ Channel cleared.")
        return

    if data == "ui:setstyle":
        await send_menu(update, cfg, tr(cfg, "ui_setstyle"))
        return

    if data == "ui:showstyle":
        cpath = custom_style_path(user_id)
        if cpath.exists() and cpath.read_text(encoding="utf-8", errors="ignore").strip():
            style_name = "custom"
        else:
            style_name = cfg.get("style_file") or DEFAULT_STYLE_FILE
        style = get_style_prompt(user_id, cfg)
        await send_menu(update, cfg, f"✍️ Current style ({style_name}):\n\n{style[:3000]}")
        return

    if data == "ui:resetstyle":
        cpath = custom_style_path(user_id)
        if cpath.exists():
            cpath.unlink()
        await send_menu(update, cfg, "✅ Custom style reset. Default style is active.")
        return

    if data == "ui:schedule":
        await send_menu(update, cfg, tr(cfg, "ui_schedule").format(schedule=schedule_summary(cfg)))
        return

    if data == "ui:pay":
        await send_menu(update, cfg, tr(cfg, "ui_pay").format(pay=pay_line(update, cfg)))
        return

    if data == "ui:materials":
        await send_menu(update, cfg, tr(cfg, "ui_materials"))
        return
    if data == "ui:modes":
        labels = {
            "mode_rss_ai": ui_text(cfg, "mode_rss_ai"),
            "mode_creative": ui_text(cfg, "mode_creative"),
        }
        await q.answer()
        await q.message.reply_text(ui_text(cfg, "modes_title"), reply_markup=build_modes_menu(labels))
        return

    if data == "ui:modepick:rss":
        cfg["mode"] = "rss"
        save_client(user_id, cfg)
        await send_menu(update, cfg, mode_set_text(cfg, "rss"))
        return

    if data == "ui:modepick:creator":
        if not creative_mode_allowed(cfg):
            labels = {"btn_payment": ui_text(cfg, "btn_payment")}
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "creative_locked") + "\n\n" + pay_line(update, cfg), reply_markup=build_payment_menu(labels))
            return
        cfg["mode"] = "creator"
        save_client(user_id, cfg)
        await send_menu(update, cfg, mode_set_text(cfg, "creator"))
        return


    if data.startswith("ui:delfeed:"):
        raw_idx = data.split(":", 2)[2]
        try:
            idx = int(raw_idx) - 1
        except ValueError:
            await send_menu(update, cfg, "Wrong feed index.")
            return
        feeds = cfg.get("feeds", [])
        if idx < 0 or idx >= len(feeds):
            await send_menu(update, cfg, "Wrong feed index.")
            return
        removed = feeds.pop(idx)
        cfg["feeds"] = feeds
        save_client(user_id, cfg)
        await send_menu(update, cfg, f"✅ Deleted feed:\n{removed}\n\n{feeds_overview(cfg)}")
        return

    if data.startswith("ui:mode:"):
        mode = data.split(":", 2)[2]
        if mode in ("rss", "creator", "both"):
            cfg["mode"] = mode
            save_client(user_id, cfg)
            await send_menu(update, cfg, mode_set_text(cfg, mode))
        return

    if data == "ui:status":
        await status_cmd(update, context)
        return

    if data == "ui:preview":
        await previewonce_cmd(update, context)
        return

    if data == "ui:fetchonce":
        await fetchonce_cmd(update, context)
        return

    if data == "ui:autoposton":
        await autoposton_cmd(update, context)
        return

    if data == "ui:autopostoff":
        await autopostoff_cmd(update, context)
        return

    await q.answer()

async def setup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not cfg.get("language"):
        await update.message.reply_text(ui_text(cfg, "choose_lang"), reply_markup=build_lang_menu())
        return

    await send_menu(update, cfg, tr(cfg, "setup_check"))

async def mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not context.args:
        await update.message.reply_text(UI_TEXTS["en"]["mode_usage"])
        return

    m = context.args[0].strip().lower()
    if m not in ("rss", "creator", "both"):
        await update.message.reply_text(UI_TEXTS["en"]["mode_usage"])
        return

    cfg["mode"] = m
    save_client(user_id, cfg)
    await update.message.reply_text(mode_set_text(cfg, m))

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
    await send_menu(update, cfg, "✅ Style updated (previous style replaced).")

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

async def unsetchannel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    cfg["channel"] = None
    save_client(user_id, cfg)
    await send_menu(update, cfg, "✅ Channel cleared.")


async def showstyle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    cpath = custom_style_path(user_id)

    if cpath.exists() and cpath.read_text(encoding="utf-8", errors="ignore").strip():
        style_name = "custom"
    else:
        style_name = cfg.get("style_file") or DEFAULT_STYLE_FILE

    style = get_style_prompt(user_id, cfg)
    await send_menu(update, cfg, f"✍️ Current style ({style_name}):\n\n{style[:3000]}")


async def resetstyle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cpath = custom_style_path(user_id)
    if cpath.exists():
        cpath.unlink()
    cfg = load_client(user_id)
    await send_menu(update, cfg, "✅ Custom style reset. Default style is active.")


async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not context.args:
        await send_menu(update, cfg, tr(cfg, "ui_schedule").format(schedule=schedule_summary(cfg)))
        return

    action = context.args[0].strip().lower()
    times = cfg.get("schedule_times", [])

    if action == "add":
        if len(context.args) < 2 or not validate_hhmm(context.args[1].strip()):
            await send_menu(update, cfg, "Usage: /schedule add HH:MM (24h)")
            return
        hhmm = context.args[1].strip()
        if hhmm not in times:
            times.append(hhmm)
        cfg["schedule_times"] = sorted(set(times))
        save_client(user_id, cfg)
        await send_menu(update, cfg, f"✅ Added slot {hhmm}.\n\n{schedule_summary(cfg)}")
        return

    if action == "remove":
        if len(context.args) < 2 or not validate_hhmm(context.args[1].strip()):
            await send_menu(update, cfg, "Usage: /schedule remove HH:MM")
            return
        hhmm = context.args[1].strip()
        cfg["schedule_times"] = [x for x in times if x != hhmm]
        save_client(user_id, cfg)
        await send_menu(update, cfg, f"✅ Removed slot {hhmm}.\n\n{schedule_summary(cfg)}")
        return

    if action == "clear":
        cfg["schedule_times"] = []
        cfg["last_schedule_date"] = None
        cfg["last_schedule_time"] = None
        save_client(user_id, cfg)
        await send_menu(update, cfg, f"✅ Schedule cleared.\n\n{schedule_summary(cfg)}")
        return

    if action == "on":
        cfg["schedule_enabled"] = True
        save_client(user_id, cfg)
        await send_menu(update, cfg, f"✅ Schedule ON.\n\n{schedule_summary(cfg)}")
        return

    if action == "off":
        cfg["schedule_enabled"] = False
        save_client(user_id, cfg)
        await send_menu(update, cfg, f"✅ Schedule OFF.\n\n{schedule_summary(cfg)}")
        return

    await send_menu(update, cfg, "Usage: /schedule [add HH:MM|remove HH:MM|clear|on|off]")


async def stylewizard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    if not context.args or context.args[0].strip().lower() not in ("rss", "creator"):
        await send_menu(update, cfg, "Usage: /stylewizard rss OR /stylewizard creator")
        return

    wizard_type = context.args[0].strip().lower()
    context.user_data["style_wizard"] = {"type": wizard_type, "step": 0, "answers": {}}

    if wizard_type == "rss":
        await update.message.reply_text("Style wizard (RSS)\nQ1/4: Language? (ru/en)")
        return

    await update.message.reply_text("Style wizard (Creator)\nQ1/5: Your niche? (e.g., nutrition, tarot)")


async def wizard_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = context.user_data.get("style_wizard")
    if not state:
        return

    user_id = update.effective_user.id
    cfg = load_client(user_id)
    text = (update.message.text or "").strip()
    if not text:
        return

    answers = state["answers"]
    step = state["step"]

    if state["type"] == "rss":
        if step == 0:
            answers["language"] = text
            state["step"] = 1
            await update.message.reply_text("Q2/4: Tone? (neutral/fun/strict/tabloid)")
            return
        if step == 1:
            answers["tone"] = text
            state["step"] = 2
            await update.message.reply_text("Q3/4: Length? (short/medium)")
            return
        if step == 2:
            answers["length"] = text
            state["step"] = 3
            await update.message.reply_text("Q4/4: Emojis? (none/light/many)")
            return

        answers["emojis"] = text
        prompt = (
            f"Language: {answers.get('language')}\n"
            f"Tone: {answers.get('tone')}\n"
            f"Length: {answers.get('length')}\n"
            f"Emojis: {answers.get('emojis')}\n"
            "Write natural Telegram posts from RSS summaries. Keep facts accurate and concise."
        )
        context.user_data.pop("style_wizard", None)
        await send_menu(update, cfg, f"✅ Wizard done.\n\nCopy and send:\n/setstyle {prompt}")
        return

    if step == 0:
        answers["niche"] = text
        state["step"] = 1
        await update.message.reply_text("Q2/5: Audience (1 sentence)?")
        return
    if step == 1:
        answers["audience"] = text
        state["step"] = 2
        await update.message.reply_text("Q3/5: Tone? (warm/bold/expert/playful)")
        return
    if step == 2:
        answers["tone"] = text
        state["step"] = 3
        await update.message.reply_text("Q4/5: CTA style? (DM keyword/link)")
        return
    if step == 3:
        answers["cta"] = text
        state["step"] = 4
        await update.message.reply_text("Q5/5: Forbidden claims/topics?")
        return

    answers["forbidden"] = text
    prompt = (
        f"Niche: {answers.get('niche')}\n"
        f"Audience: {answers.get('audience')}\n"
        f"Tone: {answers.get('tone')}\n"
        f"CTA style: {answers.get('cta')}\n"
        f"Forbidden: {answers.get('forbidden')}\n"
        "Write original Telegram posts for this creator. Be natural, practical, and avoid forbidden claims."
    )
    profile_tpl = (
        f"I am a creator in {answers.get('niche')}.\n"
        f"My audience: {answers.get('audience')}.\n"
        "I help with practical tips and clear next steps."
    )
    context.user_data.pop("style_wizard", None)
    await send_menu(
        update,
        cfg,
        "✅ Wizard done.\n\nCopy and send:\n"
        f"/setstyle {prompt}\n\n"
        "Then set profile:\n"
        f"/setprofile {profile_tpl}",
    )


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
    text = feeds_overview(cfg)
    feeds = cfg.get("feeds", [])

    if not feeds:
        await send_menu(update, cfg, text)
        return

    if update.callback_query:
        q = update.callback_query
        await q.answer()
        try:
            await q.edit_message_text(text=text, reply_markup=build_feeds_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_feeds_menu(cfg))
        return

    await update.message.reply_text(text, reply_markup=build_feeds_menu(cfg))
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
    await send_menu(update, cfg, f"✅ Deleted feed:\n{removed}\n\n{feeds_overview(cfg)}")

async def clearfeeds_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    cfg["feeds"] = []
    save_client(user_id, cfg)
    await update.message.reply_text("✅ All feeds removed.")

async def previewonce_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    mode = cfg.get("mode")

    if mode == "creator":
        msg = creator_make_post(user_id, cfg)
        await reply_ui(update, "🧪 Preview:\n\n" + msg, cfg, show_menu=True)
        return

    channel = cfg.get("channel")
    feeds = cfg.get("feeds", [])
    if not channel:
        await reply_ui(update, "Channel not set. Use /setchannel @channelusername", cfg, show_menu=True)
        return

    if mode == "both":
        creator_msg = creator_make_post(user_id, cfg)
        if not feeds:
            await reply_ui(update, "🧪 Preview (creator):\n\n" + creator_msg, cfg, show_menu=True)
            return
        best = pick_newest_unseen(cfg)
        if not best:
            await reply_ui(update, "🧪 Preview (creator):\n\n" + creator_msg, cfg, show_menu=True)
            return
        _, title, link, src = best
        summary = extract_summary_for_link(src, link)
        rss_msg = llm_generate_post(user_id, cfg, title, summary, link)
        await reply_ui(update, "🧪 Preview (RSS):\n\n" + rss_msg + "\n\n————\n🧪 Preview (Creator):\n\n" + creator_msg, cfg, show_menu=True)
        return

    if not feeds:
        await reply_ui(update, "No feeds. Add one: /addfeed <url>", cfg, show_menu=True)
        return

    best = pick_newest_unseen(cfg)
    if not best:
        await reply_ui(update, "No new items found (or everything already posted).", cfg, show_menu=True)
        return

    _, title, link, src = best
    summary = extract_summary_for_link(src, link)
    msg = llm_generate_post(user_id, cfg, title, summary, link)
    await reply_ui(update, "🧪 Preview:\n\n" + msg, cfg, show_menu=True)

async def fetchonce_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not subscription_ok(cfg):
        await reply_ui(update, pay_line(update, cfg), cfg, show_menu=True)
        return

    if not can_post_more(cfg):
        await reply_ui(update, "Daily limit reached.", cfg, show_menu=True)
        return

    channel = cfg.get("channel")
    if not channel:
        await reply_ui(update, "Channel not set. Use /setchannel @channelusername", cfg, show_menu=True)
        return

    mode = cfg.get("mode")
    feeds = cfg.get("feeds", [])

    if mode == "creator":
        msg = creator_make_post(user_id, cfg)
        await context.bot.send_message(chat_id=channel, text=msg)
        bump_daily_count(cfg)
        save_client(user_id, cfg)
        await reply_ui(update, "✅ Posted 1 creator post.", cfg, show_menu=True)
        return

    if mode == "both":
        best = pick_newest_unseen(cfg) if feeds else None
        if best:
            _, title, link, src = best
            summary = extract_summary_for_link(src, link)
            msg = llm_generate_post(user_id, cfg, title, summary, link)
            await context.bot.send_message(chat_id=channel, text=msg, disable_web_page_preview=False)
            cfg.setdefault("posted_urls", [])
            cfg["posted_urls"].append(link)
            cfg["posted_urls"] = cfg["posted_urls"][-int(cfg.get("max_dedupe", 1500)):]
            bump_daily_count(cfg)
            save_client(user_id, cfg)
            await reply_ui(update, "✅ Posted 1 RSS item (both mode).", cfg, show_menu=True)
            return

        msg = creator_make_post(user_id, cfg)
        await context.bot.send_message(chat_id=channel, text=msg)
        bump_daily_count(cfg)
        save_client(user_id, cfg)
        await reply_ui(update, "✅ Posted 1 creator post (both mode fallback).", cfg, show_menu=True)
        return

    if not feeds:
        await reply_ui(update, "No feeds. Add one: /addfeed <url>", cfg, show_menu=True)
        return

    best = pick_newest_unseen(cfg)
    if not best:
        await reply_ui(update, "No new items found (or everything already posted).", cfg, show_menu=True)
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
    await reply_ui(update, "✅ Posted 1 item.", cfg, show_menu=True)

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
    await reply_ui(update, "🤖 Autopost ON.", cfg, show_menu=True)

async def autopostoff_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    cfg["autopost_enabled"] = False
    save_client(user_id, cfg)
    await reply_ui(update, "🛑 Autopost OFF.", cfg, show_menu=True)

# ===================== Admin commands =====================
async def setsub_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if caller not in OWNER_TELEGRAM_IDS:
        await update.message.reply_text("Not authorized.")
        return

    if len(context.args) != 3:
        await update.message.reply_text(
            "Usage: /setsub <user_id> <plan> <days>\n"
            "Plans: BASIC, PRO, ELITE, FREE"
        )
        return

    uid_raw, plan_raw, days_raw = context.args[0].strip(), context.args[1].strip().upper(), context.args[2].strip()
    allowed = {"BASIC", "PRO", "ELITE", "FREE"}

    if not uid_raw.isdigit() or plan_raw not in allowed or not days_raw.isdigit():
        await update.message.reply_text(
            "Usage: /setsub <user_id> <plan> <days>\n"
            "Plans: BASIC, PRO, ELITE, FREE"
        )
        return

    days = int(days_raw)
    if plan_raw in {"BASIC", "PRO", "ELITE"} and not (1 <= days <= 3650):
        await update.message.reply_text(f"{plan_raw} days must be 1..3650")
        return
    if plan_raw == "FREE" and days != 0:
        await update.message.reply_text("FREE supports only 0 days")
        return

    uid = int(uid_raw)
    cfg = load_client(uid)
    cfg["subscription_plan"] = plan_raw

    if plan_raw == "FREE" and days == 0:
        cfg["subscription_until"] = None
        expires_text = "INACTIVE"
    else:
        expires_dt = datetime.now(timezone.utc).date() + timedelta(days=days)
        cfg["subscription_until"] = str(expires_dt)
        expires_text = cfg["subscription_until"]

    save_client(uid, cfg)

    await update.message.reply_text(
        "✅ Subscription updated\n"
        f"user_id: {uid}\n"
        f"plan: {plan_raw}\n"
        f"expires: {expires_text}"
    )

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
                use_schedule = bool(cfg.get("schedule_enabled") and cfg.get("schedule_times"))
                if use_schedule:
                    now_slot = now.strftime("%H:%M")
                    if now_slot not in set(cfg.get("schedule_times", [])):
                        continue
                    today = str(date.today())
                    if cfg.get("last_schedule_date") == today and cfg.get("last_schedule_time") == now_slot:
                        continue
                else:
                    prev = last_post_at.get(user_id)
                    if prev and (now - prev).total_seconds() < interval_min * 60:
                        continue

                mode = cfg.get("mode")
                feeds = cfg.get("feeds", [])

                if mode == "creator":
                    msg = creator_make_post(user_id, cfg)
                    await app.bot.send_message(chat_id=channel, text=msg)
                    bump_daily_count(cfg)
                    if use_schedule:
                        cfg["last_schedule_date"] = str(date.today())
                        cfg["last_schedule_time"] = now.strftime("%H:%M")
                    save_client(user_id, cfg)
                    last_post_at[user_id] = now
                    continue

                best = pick_newest_unseen(cfg) if feeds else None

                if mode == "both" and not best:
                    msg = creator_make_post(user_id, cfg)
                    await app.bot.send_message(chat_id=channel, text=msg)
                    bump_daily_count(cfg)
                    if use_schedule:
                        cfg["last_schedule_date"] = str(date.today())
                        cfg["last_schedule_time"] = now.strftime("%H:%M")
                    save_client(user_id, cfg)
                    last_post_at[user_id] = now
                    continue

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
                if use_schedule:
                    cfg["last_schedule_date"] = str(date.today())
                    cfg["last_schedule_time"] = now.strftime("%H:%M")
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
            "Не выдумывай факты.\n",
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
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("materials", materials_cmd))
    app.add_handler(CommandHandler("setup", setup_cmd))
    app.add_handler(CallbackQueryHandler(ui_callback))

    # setup
    app.add_handler(CommandHandler("mode", mode_cmd))
    app.add_handler(CommandHandler("setprofile", setprofile_cmd))
    app.add_handler(CommandHandler("setstyle", setstyle_cmd))
    app.add_handler(CommandHandler("stylewizard", stylewizard_cmd))
    app.add_handler(CommandHandler("showstyle", showstyle_cmd))
    app.add_handler(CommandHandler("resetstyle", resetstyle_cmd))
    app.add_handler(CommandHandler("setchannel", setchannel_cmd))
    app.add_handler(CommandHandler("unsetchannel", unsetchannel_cmd))
    app.add_handler(CommandHandler("schedule", schedule_cmd))
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
    app.add_handler(CommandHandler("setsub", setsub_cmd))
    app.add_handler(CommandHandler("activate", activate_cmd))
    app.add_handler(CommandHandler("deactivate", deactivate_cmd))
    app.add_handler(CommandHandler("setlimit", setlimit_cmd))
    app.add_handler(CommandHandler("setinterval", setinterval_admin_cmd))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wizard_text_handler))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
