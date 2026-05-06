import asyncio
import html
import hashlib
import io
import json
import logging
import math
import os
import re
import threading
import tempfile
import time
from html.parser import HTMLParser
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode
from http.server import BaseHTTPRequestHandler, HTTPServer

import feedparser
import requests
from dotenv import load_dotenv
from PIL import Image

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, Update

from mode_ui import mode_set_text
from keyboards import (
    build_lang_keyboard,
    build_main_menu_minimal,
    build_setup_submenu,
    build_modes_menu,
    build_payment_menu,
    build_channel_management_menu,
    build_creative_menu,
    build_creative_publish_settings_menu,
    build_creative_intake_menu,
    build_creative_campaigns_menu,
    build_creative_advanced_menu,
    build_creative_variety_menu,
    build_creative_variation_level_menu,
    build_creative_post_types_menu,
    build_rss_ai_menu,
    build_rss_output_menu,
    build_creative_output_menu,
    build_creative_content_plan_menu,
    build_creative_content_plan_item_picker_menu,
    build_creative_source_center_menu,
    build_creative_source_list_menu,
    build_creative_source_delete_menu,
    build_creative_visual_support_menu,
    build_asset_management_menu,
    build_emoji_management_menu,
    build_feed_management_menu,
    build_feed_delete_menu,
    build_quiet_hours_menu,
    build_quiet_hours_delete_menu,
    build_channel_delete_menu,
    build_channel_picker_menu,
    build_scheduling_menu,
    build_mode_schedule_menu,
    build_prompt_builder_review_menu,
    build_copy_style_review_menu,
    build_style_setup_menu,
)

from texts import TEXTS as UI_TEXTS
from telegram.constants import ChatMemberStatus, ParseMode
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
CLIENT_ASSETS_DIR = BASE_DIR / "client_assets"

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
_raw_llm_provider = os.getenv("LLM_PROVIDER", "openai_compat").strip().lower()
if _raw_llm_provider in {"deepseek", "openai", "deepseek_compat"}:
    LLM_PROVIDER = "openai_compat"
elif _raw_llm_provider in {"openai_compat", "ollama"}:
    LLM_PROVIDER = _raw_llm_provider
else:
    LLM_PROVIDER = "openai_compat"

# Ollama settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct").strip()

# OpenAI-compatible settings (DeepSeek):
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1").strip()
OPENAI_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat").strip()
FEED_CREATION_ENDPOINT = os.getenv("FEED_CREATION_ENDPOINT", "").strip()
X_RSS_FALLBACKS = os.getenv("X_RSS_FALLBACKS", "").strip()

DEFAULT_STYLE_FILE = "default_ru.txt"
CREATIVE_POST_TYPES = ["educational", "opinion", "story", "checklist", "question", "myth_vs_fact", "mini_case"]
CREATIVE_VARIATION_LEVELS = {"low", "balanced", "high"}
logger = logging.getLogger(__name__)

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
        "btn_pay": "💳 Buy posting plan",
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
    "   /addfeed [your link]\n\n"
    "4) Style set?\n"
    "   /setstyle <paste your style prompt>\n\n"
    "5) Test preview:\n"
    "   /previewonce\n\n"
    "6) Paid posting:\n"
    "   Ask admin to activate, then /fetchonce or /autoposton"
),
"ui_addfeed": "Send a direct RSS link or an X/Twitter profile link and I will process it automatically.",
"ui_setchannel": "Add the bot to your channel as an admin, then forward one message from that channel here.\nI will use that forwarded message to connect the channel.",
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
            "   /addfeed [your link]\n"
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
        "btn_pay": "💳 Купить пакет постов",
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
    "   /addfeed [ваша ссылка]\n\n"
    "4) Стиль задан?\n"
    "   /setstyle <вставьте prompt>\n\n"
    "5) Тест превью:\n"
    "   /previewonce\n\n"
    "6) Публикации (платно):\n"
    "   Активация админом, потом /fetchonce или /autoposton"
),
"ui_addfeed": "Отправьте прямую RSS-ссылку или ссылку на профиль X/Twitter — я обработаю её автоматически.",
"ui_setchannel": "Добавьте бота в канал как администратора, а затем перешлите сюда одно сообщение из этого канала.\nЯ использую это пересланное сообщение, чтобы подключить канал.",
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
            "   /addfeed [ваша ссылка]\n"
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


def rss_mode_allowed(cfg: dict) -> bool:
    return int(cfg.get("rss_daily_limit", 0) or 0) > 0


def creative_mode_allowed(cfg: dict) -> bool:
    return creative_monthly_limit(cfg) > 0


def mode_limit(cfg: dict, mode: str) -> int:
    if mode == "creator":
        return creative_monthly_limit(cfg)
    return int(cfg.get("rss_daily_limit", 0) or 0)


def mode_access_allowed(cfg: dict, mode: str) -> bool:
    return mode_limit(cfg, mode) > 0


def mode_paywall_text(cfg: dict, mode: str) -> str:
    if mode == "creator":
        return ui_text(cfg, "creative_locked") + "\n\n" + ui_text(cfg, "creative_paywall")
    return ui_text(cfg, "rss_locked") + "\n\n" + ui_text(cfg, "rss_paywall")


async def enforce_mode_paywall(update: Update, cfg: dict, mode: str) -> bool:
    if mode_access_allowed(cfg, mode):
        return True

    labels = {"btn_payment": ui_text(cfg, "btn_payment")}
    text = mode_paywall_text(cfg, mode)
    if update.callback_query:
        q = update.callback_query
        await q.answer()
        await q.message.reply_text(text, reply_markup=build_payment_menu(labels))
    elif update.message:
        await update.message.reply_text(text, reply_markup=build_payment_menu(labels))
    return False

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
    "rss_prompt": "",
    "creative_prompt": "",

    "channel": None,
    "channels": [],
    "channel_labels": {},
    "channel_meta": {},
    "channel_slots": 0,
    "feed_limit_per_channel": 2,
    "feeds": [],
    "posted_urls": [],
    "posted_story_fingerprints": [],
    "posted_item_meta": [],
    "include_rss_source_link": False,
    "use_rss_feed_image": True,
    "rss_cta_enabled": False,
    "rss_cta_text": "",
    "rss_cta_entities": [],
    "rss_bold_title": False,
    "rss_custom_emojis_text": "",
    "rss_custom_emojis_entities": [],
    "rss_custom_emojis_link": "",
    "rss_template_file_id": "",
    "rss_template_image_path": "",
    "rss_watermark_file_id": "",
    "rss_watermark_image_path": "",
    "rss_watermark_scale_pct": 15.0,
    "rss_watermark_margin_pct": 4.0,
    "creative_template_file_id": "",
    "creative_template_image_path": "",
    "creative_watermark_file_id": "",
    "creative_watermark_image_path": "",
    "creative_bold_title": False,
    "creative_custom_emojis_text": "",
    "creative_custom_emojis_entities": [],
    "creative_custom_emojis_link": "",

    "autopost_enabled": False,
    "rss_autopost_enabled": False,
    "rss_paused": False,
    "rss_pause_started_at": None,
    "creative_autopost_enabled": False,
    "interval_minutes": 30,
    "rss_use_interval": False,
    "creative_use_interval": False,
    "rss_last_interval_run_at": None,
    "creative_last_interval_run_at": None,
    "rss_interval_next_run_at": None,
    "creative_interval_next_run_at": None,
    "rss_quiet_hours_start": "",
    "rss_quiet_hours_end": "",
    "creative_quiet_hours_start": "",
    "creative_quiet_hours_end": "",
    "rss_quiet_hours_windows": [],
    "creative_quiet_hours_windows": [],
    "schedule_enabled": False,
    "schedule_times": [],
    "last_schedule_date": None,
    "last_schedule_time": None,
    "rss_schedule_enabled": False,
    "rss_schedule_times": [],
    "rss_last_schedule_date": None,
    "rss_last_schedule_time": None,
    "creative_schedule_enabled": False,
    "creative_schedule_times": [],
    "creative_last_schedule_date": None,
    "creative_last_schedule_time": None,
    "rss_scheduled_next_allowed_at": None,
    "creative_scheduled_next_allowed_at": None,
    "timezone_offset_hours": 0,
    "channel_timezone_offset_hours": None,
    "rss_freshness_minutes": 180,
    "rss_important_freshness_minutes": 480,
    "rss_important_keywords": [],
    "rss_candidate_queue": [],

    "daily_limit": 10,
    "daily_count": 0,
    "daily_date": str(date.today()),
    "rss_daily_limit": 0,
    "creative_daily_limit": 0,
    "creative_monthly_limit": 0,
    "creative_monthly_period": None,
    "creative_monthly_count": 0,
    "creative_variation_level": "balanced",
    "creative_post_types": list(CREATIVE_POST_TYPES),
    "creative_avoid_repetition": True,
    "creative_last_post_type_idx": -1,
    "creative_content_plan": [],
    "creative_topic_pillars": [],
    "creative_idea_bank": [],
    "creative_channel_intake": {},
    "creative_campaigns": [],
    "creative_active_campaign_id": None,
    "creative_inspiration_links": [],
    "creative_source_snippets": [],
    "last_visual_idea": "",
    "last_visual_search_query": "",
    "last_visual_ai_prompt": "",

    "max_dedupe": 1500,
    "fetch_entries_per_feed": 15,

    "style_file": DEFAULT_STYLE_FILE,
    "subscription_until": None,  # YYYY-MM-DD
    "subscription_plan": "FREE",
    "channel_settings": {},
}

CHANNEL_SCOPED_KEYS = (
    "rss_autopost_enabled",
    "rss_paused",
    "rss_pause_started_at",
    "creative_autopost_enabled",
    "rss_prompt",
    "creative_prompt",
    "feed_limit_per_channel",
    "feeds",
    "posted_urls",
    "posted_story_fingerprints",
    "posted_item_meta",
    "include_rss_source_link",
    "use_rss_feed_image",
    "rss_cta_enabled",
    "rss_cta_text",
    "rss_cta_entities",
    "rss_bold_title",
    "rss_custom_emojis_text",
    "rss_custom_emojis_entities",
    "rss_custom_emojis_link",
    "rss_template_file_id",
    "rss_template_image_path",
    "rss_watermark_file_id",
    "rss_watermark_image_path",
    "rss_watermark_scale_pct",
    "rss_watermark_margin_pct",
    "creative_template_file_id",
    "creative_template_image_path",
    "creative_watermark_file_id",
    "creative_watermark_image_path",
    "creative_bold_title",
    "creative_custom_emojis_text",
    "creative_custom_emojis_entities",
    "creative_custom_emojis_link",
    "rss_schedule_enabled",
    "rss_schedule_times",
    "rss_last_schedule_date",
    "rss_last_schedule_time",
    "creative_schedule_enabled",
    "creative_schedule_times",
    "creative_last_schedule_date",
    "creative_last_schedule_time",
    "rss_scheduled_next_allowed_at",
    "creative_scheduled_next_allowed_at",
    "channel_timezone_offset_hours",
    "interval_minutes",
    "rss_use_interval",
    "creative_use_interval",
    "rss_last_interval_run_at",
    "creative_last_interval_run_at",
    "rss_interval_next_run_at",
    "creative_interval_next_run_at",
    "rss_quiet_hours_start",
    "rss_quiet_hours_end",
    "creative_quiet_hours_start",
    "creative_quiet_hours_end",
    "rss_quiet_hours_windows",
    "creative_quiet_hours_windows",
    "rss_freshness_minutes",
    "rss_important_freshness_minutes",
    "rss_important_keywords",
    "rss_candidate_queue",
    "creative_variation_level",
    "creative_post_types",
    "creative_avoid_repetition",
    "creative_last_post_type_idx",
    "creative_content_plan",
    "creative_topic_pillars",
    "creative_idea_bank",
    "creative_channel_intake",
    "creative_campaigns",
    "creative_active_campaign_id",
    "creative_inspiration_links",
    "creative_source_snippets",
    "last_visual_idea",
    "last_visual_search_query",
    "last_visual_ai_prompt",
)

# ===================== Storage helpers =====================
def ensure_dirs() -> None:
    CLIENTS_DIR.mkdir(parents=True, exist_ok=True)
    STYLES_DIR.mkdir(parents=True, exist_ok=True)
    CLIENT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

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

    before_normalize = json.dumps(cfg, ensure_ascii=False, sort_keys=True)
    for k, v in DEFAULT_CLIENT.items():
        cfg.setdefault(k, v)
    if (cfg.get("mode") or "").strip().lower() == "creative":
        cfg["mode"] = "creator"
    normalize_channels(cfg)
    ensure_channel_settings(cfg)
    apply_active_channel_settings(cfg)
    normalize_legacy_prompts(cfg)
    # Persist one-time upgrades so legacy client JSON files move to canonical schema.
    if json.dumps(cfg, ensure_ascii=False, sort_keys=True) != before_normalize:
        save_client(user_id, cfg)
    return cfg

def save_client(user_id: int, cfg: dict) -> None:
    for k, v in DEFAULT_CLIENT.items():
        cfg.setdefault(k, v)
    normalize_channels(cfg)
    ensure_channel_settings(cfg)
    normalize_legacy_prompts(cfg)
    persist_active_channel_settings(cfg)
    client_path(user_id).write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_legacy_prompts(cfg: dict) -> None:
    legacy_prompt = ""
    for legacy_key in ("prompt", "style_prompt"):
        candidate = (cfg.get(legacy_key) or "").strip()
        if candidate:
            legacy_prompt = candidate
            break
    if not legacy_prompt:
        return

    for mode in ("rss", "creative"):
        key = prompt_key_for_mode(mode)
        if not (cfg.get(key) or "").strip():
            cfg[key] = legacy_prompt

    for bucket in (cfg.get("channel_settings") or {}).values():
        if not isinstance(bucket, dict):
            continue
        for mode in ("rss", "creative"):
            key = prompt_key_for_mode(mode)
            if not (bucket.get(key) or "").strip():
                bucket[key] = legacy_prompt


def normalize_channels(cfg: dict) -> list[str]:
    raw_channels = cfg.get("channels")
    if isinstance(raw_channels, str):
        raw_channels = [raw_channels]
    if not isinstance(raw_channels, list):
        raw_channels = []

    if cfg.get("channel"):
        raw_channels = [cfg.get("channel")] + raw_channels

    normalized: list[str] = []
    seen: set[str] = set()
    for item in raw_channels:
        if not isinstance(item, str):
            continue
        ch = item.strip()
        if not ch:
            continue
        if ch in seen:
            continue
        seen.add(ch)
        normalized.append(ch)

    cfg["channels"] = normalized
    cfg["channel"] = normalized[0] if normalized else None
    return normalized


def _copy_scoped_value(value):
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def ensure_channel_settings(cfg: dict) -> dict:
    channel_settings = cfg.get("channel_settings")
    if not isinstance(channel_settings, dict):
        channel_settings = {}
    has_existing_buckets = any(isinstance(v, dict) and v for v in channel_settings.values())
    legacy_seed_channel = cfg.get("channel") if (not has_existing_buckets and cfg.get("channel")) else None
    for channel in cfg.get("channels", []):
        bucket = channel_settings.get(channel)
        if not isinstance(bucket, dict):
            bucket = {}
            channel_settings[channel] = bucket
            if legacy_seed_channel and channel == legacy_seed_channel:
                for key in CHANNEL_SCOPED_KEYS:
                    if key in cfg:
                        bucket[key] = _copy_scoped_value(cfg.get(key))
        for key in CHANNEL_SCOPED_KEYS:
            if key not in bucket and key in DEFAULT_CLIENT:
                bucket[key] = _copy_scoped_value(DEFAULT_CLIENT.get(key))
    for channel in list(channel_settings.keys()):
        if channel not in cfg.get("channels", []):
            channel_settings.pop(channel, None)
    cfg["channel_settings"] = channel_settings
    return channel_settings


def persist_active_channel_settings(cfg: dict) -> None:
    channel = cfg.get("channel")
    if not channel:
        return
    channel_settings = ensure_channel_settings(cfg)
    bucket = channel_settings.setdefault(channel, {})
    for key in CHANNEL_SCOPED_KEYS:
        if key in cfg:
            bucket[key] = _copy_scoped_value(cfg.get(key))


def apply_active_channel_settings(cfg: dict) -> None:
    channel = cfg.get("channel")
    if not channel:
        return
    channel_settings = ensure_channel_settings(cfg)
    bucket = channel_settings.get(channel) or {}
    for key in CHANNEL_SCOPED_KEYS:
        if key in bucket:
            cfg[key] = _copy_scoped_value(bucket[key])
        elif key in DEFAULT_CLIENT:
            cfg[key] = _copy_scoped_value(DEFAULT_CLIENT.get(key))


def switch_active_channel(cfg: dict, channel: str) -> None:
    current = cfg.get("channel")
    if current == channel:
        return
    if current:
        persist_active_channel_settings(cfg)
    cfg["channel"] = channel
    apply_active_channel_settings(cfg)


def mode_autopost_enabled(cfg: dict, mode: str) -> bool:
    if mode == "creative":
        if "creative_autopost_enabled" in cfg:
            return bool(cfg.get("creative_autopost_enabled"))
        return bool(cfg.get("autopost_enabled"))

    if mode == "rss":
        if "rss_autopost_enabled" in cfg:
            return bool(cfg.get("rss_autopost_enabled"))
        return bool(cfg.get("autopost_enabled"))

    return mode_autopost_enabled(cfg, "rss") or mode_autopost_enabled(cfg, "creative")


def set_mode_autopost_enabled(cfg: dict, mode: str, enabled: bool) -> None:
    if mode == "creative":
        cfg["creative_autopost_enabled"] = bool(enabled)
    elif mode == "rss":
        cfg["rss_autopost_enabled"] = bool(enabled)
    else:
        cfg["rss_autopost_enabled"] = bool(enabled)
        cfg["creative_autopost_enabled"] = bool(enabled)
    cfg["autopost_enabled"] = mode_autopost_enabled(cfg, "rss") or mode_autopost_enabled(cfg, "creative")


def rss_posting_paused(cfg: dict) -> bool:
    return bool(cfg.get("rss_paused", False))


def set_rss_posting_paused(cfg: dict, paused: bool) -> None:
    cfg["rss_paused"] = bool(paused)
    if paused:
        cfg["rss_pause_started_at"] = datetime.now(timezone.utc).isoformat()
    else:
        cfg["rss_pause_started_at"] = None

# ===================== Utility =====================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS or user_id in OWNER_TELEGRAM_IDS

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

def _mode_daily_keys(mode: str) -> tuple[str, str]:
    if mode == "creator":
        return "creative_daily_date", "creative_daily_count"
    return "rss_daily_date", "rss_daily_count"

def ensure_mode_daily_counter(cfg: dict, mode: str) -> dict:
    today = str(date.today())
    date_key, count_key = _mode_daily_keys(mode)
    if cfg.get(date_key) != today:
        cfg[date_key] = today
        cfg[count_key] = 0
    return cfg


def _current_month_key() -> str:
    return date.today().strftime("%Y-%m")


def creative_monthly_limit(cfg: dict) -> int:
    explicit = int(cfg.get("creative_monthly_limit", 0) or 0)
    if explicit > 0:
        return explicit
    legacy_daily = int(cfg.get("creative_daily_limit", 0) or 0)
    if legacy_daily > 0:
        return legacy_daily * 30
    return 0


def ensure_creative_monthly_counter(cfg: dict) -> dict:
    month_key = _current_month_key()
    if cfg.get("creative_monthly_period") != month_key:
        cfg["creative_monthly_period"] = month_key
        cfg["creative_monthly_count"] = 0
    return cfg

def can_post_more(cfg: dict, mode: str) -> bool:
    if mode == "creator":
        cfg = ensure_creative_monthly_counter(cfg)
        return int(cfg.get("creative_monthly_count", 0) or 0) < creative_monthly_limit(cfg)
    cfg = ensure_mode_daily_counter(cfg, mode)
    _, count_key = _mode_daily_keys(mode)
    return int(cfg.get(count_key, 0) or 0) < mode_limit(cfg, mode)

def bump_daily_count(cfg: dict, mode: str | None = None) -> None:
    mode = (mode or cfg.get("mode") or "rss").strip().lower()
    if mode not in ("rss", "creator"):
        mode = "rss"
    if mode == "creator":
        cfg = ensure_creative_monthly_counter(cfg)
        cfg["creative_monthly_count"] = int(cfg.get("creative_monthly_count", 0) or 0) + 1
        return
    cfg = ensure_mode_daily_counter(cfg, mode)
    _, count_key = _mode_daily_keys(mode)
    cfg[count_key] = int(cfg.get(count_key, 0) or 0) + 1

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


def get_mode_prompt(user_id: int, cfg: dict, mode: str) -> str:
    key = prompt_key_for_mode(mode)
    prompt = (cfg.get(key) or "").strip()
    if prompt:
        return prompt

    # backward compatibility: older shared prompt fields
    for legacy_key in ("prompt", "style_prompt"):
        legacy_prompt = (cfg.get(legacy_key) or "").strip()
        if legacy_prompt:
            return legacy_prompt

    cpath = custom_style_path(user_id)
    if cpath.exists():
        txt = cpath.read_text(encoding="utf-8", errors="ignore").strip()
        if txt:
            return txt

    if mode == "creative":
        return "Write a Telegram-ready post in plain text. No JSON, no code blocks."
    return "Rewrite the source into a Telegram-ready post in plain text. No JSON, no code blocks."


def prompt_key_for_mode(mode: str) -> str:
    return "creative_prompt" if mode == "creative" else "rss_prompt"


def set_mode_prompt(cfg: dict, mode: str, prompt: str) -> None:
    cfg[prompt_key_for_mode(mode)] = prompt


def style_setup_text(user_id: int, cfg: dict, mode: str) -> str:
    current = get_mode_prompt(user_id, cfg, mode).strip()
    if current:
        preview = ui_text(cfg, "style_setup_current_prefix").format(prompt=current[:1500])
    else:
        preview = ui_text(cfg, "style_setup_empty")
    return f"{ui_text(cfg, 'style_setup_title')}\n\n{preview}"

def sanitize_llm_post(text: str, cfg: dict, link: str) -> str:
    t = (text or "").replace("\r", "").strip()

    # trim common wrapper formatting
    t = re.sub(r"(?is)^```[a-z0-9_\-]*\s*", "", t).strip()
    t = re.sub(r"(?is)\s*```$", "", t).strip()
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()

    include_source_link = bool(cfg.get("include_rss_source_link", True))
    if not include_source_link:
        # Respect RSS output setting: remove links and common source-attribution tails.
        t = re.sub(r"https?://\S+", "", t)
        t = re.sub(r"(?im)^\s*(source|источник)\s*:\s*.*$", "", t)
        t = re.sub(r"(?im)^\s*(via|через)\s+@\w+\s*$", "", t)
        t = re.sub(r"\n{3,}", "\n\n", t).strip()

    if not t:
        t = "📌 Коротко: в источнике мало деталей."

    return t[:900]


def _feed_url(feed_entry) -> str:
    if isinstance(feed_entry, dict):
        return str(feed_entry.get("url") or "").strip()
    return str(feed_entry or "").strip()


def _feed_name(feed_entry) -> str:
    if isinstance(feed_entry, dict):
        return str(feed_entry.get("name") or "").strip()
    return ""


def _find_feed_by_url(feeds: list, url: str) -> bool:
    target = (url or "").strip()
    return any(_feed_url(item) == target for item in feeds)


def feed_limit_per_channel(cfg: dict) -> int:
    return 1


def _looks_like_direct_feed_url(url: str) -> bool:
    raw = (url or "").strip().lower()
    return bool(re.search(r"(rss|atom|feed|\.xml)(?:$|[/?#])", raw))


def _is_x_profile_url(url: str) -> bool:
    normalized, username, _ = _normalize_x_profile_url(url)
    return bool(normalized and username)


def _normalize_x_profile_url(url: str) -> tuple[str | None, str | None, str | None]:
    try:
        parsed = urlsplit((url or "").strip())
    except Exception:
        return None, None, "invalid_x_profile_url"
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https"}:
        return None, None, "invalid_x_profile_url"
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host not in {"x.com", "twitter.com", "mobile.twitter.com", "mobile.x.com"}:
        return None, None, "invalid_x_profile_url"
    path = (parsed.path or "").strip("/")
    if not path:
        return None, None, "username_parse_failed"
    parts = [part for part in path.split("/") if part]
    if len(parts) >= 2 and parts[1].lower() == "status":
        return None, None, "x_status_url_not_supported"
    if len(parts) != 1:
        return None, None, "username_parse_failed"
    username = parts[0]
    if not re.fullmatch(r"[A-Za-z0-9_]{1,15}", username):
        return None, None, "username_parse_failed"
    normalized = f"https://x.com/{username}"
    return normalized, username, None


def _candidate_is_valid_http_url(url: str) -> bool:
    parsed = urlsplit((url or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _looks_like_html_response(content_type: str, body: str) -> bool:
    ct = (content_type or "").lower()
    prefix = (body or "").lstrip()[:256].lower()
    return "text/html" in ct or prefix.startswith("<!doctype html") or prefix.startswith("<html")


def _looks_like_xml_response(content_type: str, body: str) -> bool:
    ct = (content_type or "").lower()
    if any(token in ct for token in ("xml", "rss", "atom")):
        return True
    prefix = (body or "").lstrip()[:256].lower()
    return (
        prefix.startswith("<?xml")
        or prefix.startswith("<rss")
        or prefix.startswith("<feed")
        or prefix.startswith("<rdf:rdf")
    )


def _raw_body_has_feed_items(body: str) -> bool:
    sample = (body or "").lower()
    return "<item" in sample or "<entry" in sample


def _feed_title(feed_data) -> str:
    feed_meta = getattr(feed_data, "feed", None) or {}
    return str(_entry_get(feed_meta, "title", "") or "").strip()


def _feed_entries_count(feed_data) -> int:
    entries = getattr(feed_data, "entries", None) or []
    return len(entries)


def _validate_candidate_feed_url(candidate: str) -> tuple[bool, str]:
    logger.info("[FEED_VALIDATE_START] candidate=%s", candidate)
    logger.info("[FEED_URL] %s", candidate)
    if not _candidate_is_valid_http_url(candidate):
        logger.info("[FEED_VALIDATE_FAIL] candidate=%s reason=candidate_feed_invalid", candidate)
        return False, "candidate_feed_invalid"
    try:
        parsed = feedparser.parse(candidate)
    except Exception as exc:
        logger.info("[FEED_VALIDATE_FAIL] candidate=%s reason=parse_failed error=%s", candidate, exc)
        logger.info("[FEED_VALIDATION_RESULT] invalid reason=parse_failed")
        return False, "parse_failed"
    title = _feed_title(parsed)
    entries_count = _feed_entries_count(parsed)
    logger.info("[FEED_ENTRIES_COUNT] %s", entries_count)
    logger.info("[FEED_TITLE] %s", title or "-")
    if title or entries_count > 0:
        logger.info("[FEED_VALIDATE_OK] candidate=%s", candidate)
        logger.info("[FEED_VALIDATION_RESULT] valid")
        return True, ""
    try:
        resp = requests.get(candidate, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        logger.info("[FEED_HTTP_STATUS] %s", resp.status_code)
        logger.info("[FEED_CONTENT_TYPE] %s", resp.headers.get("Content-Type", ""))
    except Exception as exc:
        logger.info("[FEED_VALIDATE_FAIL] candidate=%s reason=request_error error=%s", candidate, exc)
        code = getattr(getattr(exc, "response", None), "status_code", None)
        logger.info("[FEED_VALIDATION_RESULT] invalid reason=request_error")
        return False, f"http_error_{code}" if code else "request_error"
    body = resp.text
    if not _looks_like_xml_response(resp.headers.get("Content-Type", ""), body) and _looks_like_html_response(resp.headers.get("Content-Type", ""), body):
        logger.info("[FEED_VALIDATE_FAIL] candidate=%s reason=response_not_xml", candidate)
        logger.info("[FEED_VALIDATION_RESULT] invalid reason=response_not_xml")
        return False, "response_not_xml"
    try:
        parsed = feedparser.parse(resp.content)
    except Exception as exc:
        logger.info("[FEED_VALIDATE_FAIL] candidate=%s reason=parse_failed error=%s", candidate, exc)
        logger.info("[FEED_VALIDATION_RESULT] invalid reason=parse_failed")
        return False, "parse_failed"
    title = _feed_title(parsed)
    entries_count = _feed_entries_count(parsed)
    raw_has_items = _raw_body_has_feed_items(body)
    logger.info("[FEED_ENTRIES_COUNT] %s", entries_count)
    logger.info("[FEED_TITLE] %s", title or "-")
    if title or entries_count > 0 or raw_has_items:
        logger.info("[FEED_VALIDATE_OK] candidate=%s", candidate)
        logger.info("[FEED_VALIDATION_RESULT] valid")
        return True, ""
    logger.info("[FEED_VALIDATE_FAIL] candidate=%s reason=feed_parsed_but_empty", candidate)
    logger.info("[FEED_VALIDATION_RESULT] invalid reason=feed_parsed_but_empty")
    return False, "feed_parsed_but_empty"


def _feed_validation_reason_text(reason: str | None) -> str:
    code = (reason or "").strip()
    if not code:
        return "Feed validation failed."
    if code.startswith("http_error_"):
        status = code.replace("http_error_", "", 1) or "unknown"
        return f"HTTP error {status}"
    if code == "response_not_xml":
        return "Response is not valid XML"
    if code == "feed_parsed_but_empty":
        return "Feed parsed but contains 0 entries"
    if code == "request_error":
        return "Request error while fetching feed"
    if code in {"parse_failed", "candidate_feed_invalid"}:
        return "Feed parsing failed"
    if code == "candidate_feed_empty":
        return "Feed parsed but contains 0 entries"
    return code


def _feed_validation_error_message(cfg: dict, reason: str | None) -> str:
    return f"{ui_text(cfg, 'feed_read_failed')}\n\nReason: {_feed_validation_reason_text(reason)}"


def _feed_recovery_user_message(cfg: dict, reason: str | None, *, x_attempt: bool = False) -> str:
    code = (reason or "").strip()
    if code == "x_status_url_not_supported":
        return ui_text(cfg, "feed_recovery_x_status")
    if code in {"invalid_x_profile_url", "username_parse_failed"} and x_attempt:
        return ui_text(cfg, "feed_recovery_x_profile_invalid")
    if code == "feed_parsed_but_empty":
        return ui_text(cfg, "feed_recovery_empty")
    if code == "response_not_xml":
        return ui_text(cfg, "feed_recovery_unsupported")
    if code.startswith("http_error_") or code == "request_error":
        return ui_text(cfg, "feed_recovery_unreachable")
    if code in {"primary_provider_failed", "fallback_provider_failed"}:
        return ui_text(cfg, "feed_recovery_x_transform_failed")
    return ui_text(cfg, "feed_recovery_invalid")


def _resolve_x_fallback_provider_url(provider: str, normalized_x_url: str, username: str) -> tuple[str | None, str]:
    base = (provider or "").strip()
    if not base:
        return None, ""
    if "{username}" in base or "{url}" in base:
        return base.replace("{username}", username).replace("{url}", normalized_x_url), base
    if _candidate_is_valid_http_url(base):
        if base.endswith("/"):
            return f"{base}{username}", base
        return f"{base}/{username}", base
    return None, base


def _built_in_x_fallbacks() -> list[str]:
    return [
        "https://rsshub.app/twitter/user/{username}",
        "https://nitter.poast.org/{username}/rss",
        "https://nitter.net/{username}/rss",
    ]


def _feed_has_entries(feed_data) -> bool:
    return _feed_entries_count(feed_data) > 0


def _feed_has_metadata(feed_data) -> bool:
    return bool(_feed_title(feed_data))


def _entry_has_content(entry) -> bool:
    for key in ("link", "guid", "id", "title", "description", "summary"):
        value = str(_entry_get(entry, key, "") or "").strip()
        if value:
            return True
    content_items = _entry_get(entry, "content")
    if isinstance(content_items, list):
        for item in content_items:
            value = str(_entry_get(item, "value", "") or "").strip()
            if value:
                return True
    return False


def _entry_primary_link(entry) -> str:
    return str(
        _entry_get(entry, "link", "")
        or _entry_get(entry, "guid", "")
        or _entry_get(entry, "id", "")
        or ""
    ).strip()


def _find_native_feed_from_site(url: str) -> str | None:
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        html = resp.text or ""
    except Exception:
        return None

    candidates: list[str] = []
    for match in re.finditer(
        r'<link[^>]+rel=["\'][^"\']*alternate[^"\']*["\'][^>]*>',
        html,
        flags=re.IGNORECASE,
    ):
        tag = match.group(0)
        if not re.search(r'type=["\'](?:application|text)/(?:rss\+xml|atom\+xml|xml)["\']', tag, flags=re.IGNORECASE):
            continue
        href_match = re.search(r'href=["\']([^"\']+)["\']', tag, flags=re.IGNORECASE)
        if href_match:
            candidates.append(urljoin(url, href_match.group(1).strip()))

    for fallback in ("/feed", "/rss", "/rss.xml", "/feed.xml", "/atom.xml"):
        candidates.append(urljoin(url, fallback))

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            parsed = feedparser.parse(candidate)
        except Exception:
            continue
        if _feed_has_entries(parsed):
            return candidate
    return None


def _create_feed_via_external_service(endpoint: str, source_url: str) -> tuple[str | None, str | None]:
    if not endpoint:
        return None, "primary_endpoint_missing"
    try:
        logger.info("Calling feed creation service endpoint=%s source_url=%s", endpoint, source_url)
        resp = requests.get(endpoint, params={"url": source_url}, timeout=20)
        resp.raise_for_status()
        data = resp.json() if "application/json" in (resp.headers.get("Content-Type") or "").lower() else {}
    except Exception as exc:
        logger.warning("Feed creation request failed endpoint=%s source_url=%s: %s", endpoint, source_url, exc)
        return None, "primary_provider_failed"
    candidate = _extract_feed_url_from_response(data)
    if not candidate:
        logger.info("Feed creation response did not contain feed url for source_url=%s", source_url)
        return None, "primary_provider_failed"
    return candidate, None


def _extract_feed_url_from_response(data) -> str | None:
    if not isinstance(data, dict):
        return None
    for key in ("feed_url", "rss_url", "url"):
        candidate = str(data.get(key) or "").strip()
        if candidate:
            return candidate
    nested = data.get("data")
    if isinstance(nested, dict):
        for key in ("feed_url", "rss_url", "url"):
            candidate = str(nested.get(key) or "").strip()
            if candidate:
                return candidate
    return None


def _feed_auto_fail_message(cfg: dict, user_id: int, reason: str | None) -> str:
    if reason == "x_status_url_not_supported":
        return ui_text(cfg, "feed_x_profile_only")
    message = ui_text(cfg, "feed_auto_failed")
    if is_admin(user_id) and reason:
        return f"{message}\n\nX transform failed: {reason}"
    return message


def _create_x_profile_feed(normalized_x_url: str, username: str) -> tuple[str | None, str]:
    last_reason = "fallback_provider_failed"
    if FEED_CREATION_ENDPOINT:
        endpoint_base = FEED_CREATION_ENDPOINT.rstrip("/")
        endpoint_candidate = f"{endpoint_base}/twitter/user/{username}"
        if endpoint_candidate:
            logger.info("[X_LINK_DETECTED] username=%s profile=%s", username, normalized_x_url)
            logger.info("[X_USERNAME] %s", username)
            logger.info("[X_RSS_URL_FINAL] %s", endpoint_candidate)
            logger.info("[RSSHUB_TRANSFORM] source=%s candidate=%s", normalized_x_url, endpoint_candidate)
            valid, invalid_reason = _validate_candidate_feed_url(endpoint_candidate)
            if valid:
                logger.info(
                    "X feed provider success: provider=primary_endpoint_base source=%s candidate=%s",
                    normalized_x_url,
                    endpoint_candidate,
                )
                return endpoint_candidate, ""
            last_reason = invalid_reason
            logger.info("[FEED_VALIDATE_FAIL] candidate=%s reason=%s", endpoint_candidate, invalid_reason or "candidate_feed_invalid")
        else:
            last_reason = "primary_endpoint_missing"
    else:
        last_reason = "primary_endpoint_missing"

    fallback_sources = [item.strip() for item in X_RSS_FALLBACKS.split(",") if item.strip()] if X_RSS_FALLBACKS else _built_in_x_fallbacks()
    for provider in fallback_sources:
        fallback_url, provider_name = _resolve_x_fallback_provider_url(provider, normalized_x_url, username)
        if not fallback_url:
            last_reason = "fallback_provider_failed"
            continue
        valid, reason = _validate_candidate_feed_url(fallback_url)
        if valid:
            logger.info("X feed provider success: provider=%s source=%s candidate=%s", provider_name, normalized_x_url, fallback_url)
            return fallback_url, ""
        last_reason = reason or "fallback_provider_failed"
    return None, last_reason


def resolve_feed_input_url(raw_url: str) -> tuple[str | None, str, str | None, bool]:
    url = (raw_url or "").strip()
    if not url:
        return None, "invalid", "invalid_x_profile_url", False

    direct_valid, direct_reason = _validate_candidate_feed_url(url)
    if direct_valid:
        return url, "direct", None, False

    if _looks_like_direct_feed_url(url):
        return None, "invalid", direct_reason or "candidate_feed_invalid", False

    normalized_x_url, x_username, normalize_reason = _normalize_x_profile_url(url)
    if not normalized_x_url:
        return None, "invalid", normalize_reason or direct_reason or "candidate_feed_invalid", False
    logger.info("[X_LINK_DETECTED] source=%s normalized=%s username=%s", url, normalized_x_url, x_username)

    created, reason = _create_x_profile_feed(normalized_x_url, x_username)
    if created:
        return created, "created", None, True

    logger.info("X profile feed creation failed: source=%s reason=%s", normalized_x_url, reason)
    return None, "failed", reason or "fallback_provider_failed", True


async def process_feed_input(update: Update, context: ContextTypes.DEFAULT_TYPE, cfg: dict, user_id: int, raw_url: str, *, from_plain_text: bool = False) -> None:
    url = (raw_url or "").strip()
    logger.info("[ADD_FEED_PROCESS] user_id=%s from_plain_text=%s input=%s", user_id, from_plain_text, url)
    feeds = cfg.get("feeds", [])
    limit = feed_limit_per_channel(cfg)

    if _find_feed_by_url(feeds, url):
        logger.info("[FEED_VALIDATE_FAIL] user_id=%s reason=duplicate_feed url=%s", user_id, url)
        context.user_data.pop("awaiting_feed_add", None)
        await update.message.reply_text(ui_text(cfg, "feed_duplicate"))
        return
    if len(feeds) >= limit:
        logger.info("[FEED_VALIDATE_FAIL] user_id=%s reason=feed_limit_reached limit=%s", user_id, limit)
        context.user_data.pop("awaiting_feed_add", None)
        await update.message.reply_text(ui_text(cfg, "feed_limit_reached").format(limit=limit))
        return

    await update.message.reply_text(ui_text(cfg, "feed_processing"))
    feed_url, status, reason, is_x_attempt = resolve_feed_input_url(url)
    if not feed_url:
        context.user_data.pop("awaiting_feed_add", None)
        logger.info("[FEED_VALIDATE_FAIL] user_id=%s status=%s reason=%s input=%s", user_id, status, reason or "unknown", url)
        if status == "failed" and is_admin(user_id):
            await update.message.reply_text(f"{_feed_auto_fail_message(cfg, user_id, reason)}\n\nReason: {_feed_validation_reason_text(reason)}")
        else:
            await update.message.reply_text(_feed_recovery_user_message(cfg, reason, x_attempt=is_x_attempt))
        return

    context.user_data["awaiting_feed_add"] = "name"
    context.user_data["pending_feed_url"] = feed_url
    logger.info("[FEED_VALIDATE_OK] user_id=%s input=%s resolved=%s is_x=%s", user_id, url, feed_url, is_x_attempt)
    await update.message.reply_text(ui_text(cfg, "feed_name_prompt"))

# ===================== RSS helpers =====================
def _entry_time_struct(entry):
    return _entry_get(entry, "published_parsed") or _entry_get(entry, "updated_parsed")


def _entry_time_iso(entry) -> str:
    t = _entry_time_struct(entry)
    try:
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc).isoformat()
    except Exception:
        pass
    return ""


def _story_title_normalized(title: str) -> str:
    cleaned = clean_text(title).lower()
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    cleaned = re.sub(r"[^a-zа-яё0-9\s]", " ", cleaned, flags=re.IGNORECASE)
    return " ".join(cleaned.split())


def _story_title_fingerprint(title: str) -> str:
    normalized = _story_title_normalized(title)
    if not normalized:
        return ""
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:20]


def _story_similarity(left: str, right: str) -> float:
    lt = set(_story_title_normalized(left).split())
    rt = set(_story_title_normalized(right).split())
    if not lt or not rt:
        return 0.0
    return len(lt & rt) / max(1, len(lt | rt))


def _pruned_posted_meta(cfg: dict) -> list[dict]:
    raw = cfg.get("posted_item_meta")
    if not isinstance(raw, list):
        return []
    now = datetime.now(timezone.utc)
    pruned: list[dict] = []
    for item in raw[-max(10, int(cfg.get("max_dedupe", 1500) or 1500)):]:
        if not isinstance(item, dict):
            continue
        ts = str(item.get("posted_at") or "").strip()
        if ts:
            try:
                posted_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if now - posted_dt > timedelta(days=4):
                    continue
            except Exception:
                pass
        pruned.append(item)
    return pruned


def _assess_rss_candidate_relevance(title: str, summary: str, published_struct, now_utc: datetime) -> tuple[bool, int]:
    text = clean_text(f"{title} {summary}")
    title_words = re.findall(r"[A-Za-zА-Яа-яЁё0-9]{2,}", clean_text(title))
    all_words = re.findall(r"[A-Za-zА-Яа-яЁё0-9]{2,}", text)
    has_subject = bool(re.search(r"\b[A-ZА-ЯЁ][a-zа-яё]{2,}\b", title or ""))
    has_digits = bool(re.search(r"\d", text))

    context_ok = len(title_words) >= 4 and len(all_words) >= 10 and (len(clean_text(title)) >= 24 or len(clean_text(summary)) >= 90)
    if not context_ok and not (has_subject and has_digits and len(all_words) >= 8):
        return False, -100

    lower = text.lower()
    momentum = bool(re.search(r"\b(live|reaction|reacts|comment|post-?match|after the game|fan reaction|x\.com|twitter|thread)\b", lower))
    analysis = bool(re.search(r"\b(analysis|recap|report|breakdown|explained|preview|tactical)\b", lower))
    breaking = bool(re.search(r"\b(breaking|official|confirmed|lineup|injury|final score|wins|signed|transfer)\b", lower))
    low_signal = bool(re.search(r"\b(opinion|rumor|rumour|hot take|fan(s)?|debate|watch along)\b", lower))
    importance = (2 if breaking else 0) + (1 if analysis else 0) + (1 if has_digits else 0) - (1 if low_signal else 0)
    if importance <= 0:
        return False, -80

    if published_struct:
        try:
            published_dt = datetime.fromtimestamp(time.mktime(published_struct), tz=timezone.utc)
            age = now_utc - published_dt
            max_age = timedelta(hours=6 if momentum else (72 if analysis else 36))
            if age > max_age:
                return False, -60
        except Exception:
            pass

    score = importance * 10 + min(len(all_words), 45)
    if momentum:
        score -= 5
    return True, score


def _record_posted_rss_item(cfg: dict, link: str, title: str, feed_url: str, published_struct=None) -> None:
    cfg.setdefault("posted_urls", [])
    cfg["posted_urls"].append(link)
    cfg["posted_urls"] = cfg["posted_urls"][-int(cfg.get("max_dedupe", 1500)):]

    normalized_title = _story_title_normalized(title)
    fingerprint = _story_title_fingerprint(title)
    domain = (urlsplit(feed_url).netloc or urlsplit(link).netloc or "").lower()
    item_meta = _pruned_posted_meta(cfg)
    item_meta.append(
        {
            "url": link,
            "title": clean_text(title)[:300],
            "normalized_title": normalized_title[:220],
            "fingerprint": fingerprint,
            "source_domain": domain[:120],
            "published_at": _entry_time_iso({"published_parsed": published_struct}) if published_struct else "",
            "posted_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    limit = max(10, int(cfg.get("max_dedupe", 1500) or 1500))
    cfg["posted_item_meta"] = item_meta[-limit:]
    cfg["posted_story_fingerprints"] = [x.get("fingerprint") for x in cfg["posted_item_meta"] if isinstance(x, dict) and x.get("fingerprint")]


def pick_newest_unseen(cfg: dict):
    candidates = collect_rss_candidates(cfg)
    if not candidates:
        return None
    top = candidates[0]
    return top["published"], top["title"], top["link"], top["feed_url"]


def _candidate_identity_token(link_n: str, title: str) -> str:
    fp_title = _story_title_fingerprint(title)
    return fp_title or hashlib.sha1(link_n.encode("utf-8")).hexdigest()[:20]


def collect_rss_candidates(cfg: dict) -> list[dict]:
    feeds = cfg.get("feeds", [])
    posted = set(cfg.get("posted_urls", []))
    posted_meta = _pruned_posted_meta(cfg)
    cfg["posted_item_meta"] = posted_meta
    cfg["posted_story_fingerprints"] = [x.get("fingerprint") for x in posted_meta if x.get("fingerprint")]
    candidates: list[dict] = []

    per_feed = int(cfg.get("fetch_entries_per_feed", 15))
    now_utc = datetime.now(timezone.utc)
    logger.info("[MULTIFEED_MERGE] stage=start feeds=%s per_feed=%s", len(feeds), per_feed)
    for feed_entry in feeds:
        feed_url = _feed_url(feed_entry)
        if not feed_url:
            continue
        fp = feedparser.parse(feed_url)
        entries = getattr(fp, "entries", []) or []
        for e in entries[:per_feed]:
            link = _entry_primary_link(e)
            if not link:
                continue
            link_n = normalize_url(link)
            if link_n in posted:
                continue

            title = getattr(e, "title", "Untitled")
            summary = clean_text(_entry_get(e, "summary", "") or _entry_get(e, "description", "") or "")
            published = getattr(e, "published_parsed", None)
            is_important, _ = classify_candidate_importance(cfg, title, summary)
            if not candidate_is_fresh(cfg, published, now_utc, "initial_scan", is_important=is_important):
                continue
            is_relevant, score = _assess_rss_candidate_relevance(title, summary, published, now_utc)
            if not is_relevant:
                continue

            fp_title = _story_title_fingerprint(title)
            skip_duplicate_story = False
            for posted_item in posted_meta:
                if not isinstance(posted_item, dict):
                    continue
                posted_fp = str(posted_item.get("fingerprint") or "")
                posted_title = str(posted_item.get("title") or "")
                if fp_title and posted_fp and fp_title == posted_fp:
                    skip_duplicate_story = True
                    break
                if posted_title and _story_similarity(posted_title, title) >= 0.86:
                    skip_duplicate_story = True
                    break
            if skip_duplicate_story:
                continue

            candidates.append(
                {
                    "score": score,
                    "published": published,
                    "title": title,
                    "link": link_n,
                    "feed_url": feed_url,
                    "identity": _candidate_identity_token(link_n, title),
                    "summary": summary,
                    "important": is_important,
                }
            )

    deduped: dict[str, dict] = {}
    for item in candidates:
        token = str(item.get("identity") or "")
        prev = deduped.get(token)
        if not prev or (item["score"], item["published"] or (0,), item["title"]) > (prev["score"], prev["published"] or (0,), prev["title"]):
            deduped[token] = item
    merged = list(deduped.values())
    merged.sort(key=lambda x: (x["score"], x["published"] or (0,), x["title"]), reverse=True)
    logger.info("[MULTIFEED_MERGE] stage=done raw=%s deduped=%s selected=%s", len(candidates), len(merged), len(merged[:1]))
    return merged


def _queue_items(cfg: dict) -> list[dict]:
    raw = cfg.get("rss_candidate_queue")
    if not isinstance(raw, list):
        return []
    cleaned: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        link = str(item.get("link") or "").strip()
        title = str(item.get("title") or "").strip()
        feed_url = str(item.get("feed_url") or "").strip()
        if not link or not title or not feed_url:
            continue
        cleaned.append(item)
    return cleaned


def queue_candidate(cfg: dict, candidate: dict, reason: str) -> None:
    queue = _queue_items(cfg)
    token = str(candidate.get("identity") or _candidate_identity_token(candidate["link"], candidate["title"]))
    if any(str(x.get("identity") or "") == token for x in queue):
        return
    published_iso = _entry_time_iso({"published_parsed": candidate.get("published")}) if candidate.get("published") else ""
    queue.append(
        {
            "identity": token,
            "link": candidate["link"],
            "title": candidate["title"],
            "feed_url": candidate["feed_url"],
            "score": int(candidate.get("score") or 0),
            "published_at": published_iso,
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "summary": str(candidate.get("summary") or ""),
            "important": bool(candidate.get("important", False)),
        }
    )
    cfg["rss_candidate_queue"] = queue[-200:]
    logger.info("[CANDIDATE_QUEUED] reason=%s link=%s", reason, candidate["link"])


def _queue_item_is_fresh(cfg: dict, item: dict, now_utc: datetime) -> bool:
    published_raw = str(item.get("published_at") or "").strip()
    is_important = bool(item.get("important", False))
    if not published_raw:
        return True
    try:
        published_dt = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
    except Exception:
        return True
    age_min = max(0.0, (now_utc - published_dt).total_seconds() / 60.0)
    threshold = allowed_freshness_threshold(cfg, is_important)
    logger.info("[CANDIDATE_AGE] source=queue age_min=%.1f threshold_min=%s important=%s", age_min, threshold, is_important)
    if age_min > threshold:
        logger.info("[CANDIDATE_SKIPPED_STALE] source=queue link=%s age_min=%.1f threshold_min=%s important=%s", item.get("link"), age_min, threshold, is_important)
        return False
    return True


def dequeue_best_candidate(cfg: dict) -> dict | None:
    now_utc = datetime.now(timezone.utc)
    queue = _queue_items(cfg)
    fresh_queue = [item for item in queue if _queue_item_is_fresh(cfg, item, now_utc)]
    if len(fresh_queue) != len(queue):
        cfg["rss_candidate_queue"] = fresh_queue
    if not fresh_queue:
        return None
    fresh_queue.sort(key=lambda x: (bool(x.get("important", False)), int(x.get("score") or 0), str(x.get("published_at") or "")), reverse=True)
    best = fresh_queue.pop(0)
    cfg["rss_candidate_queue"] = fresh_queue
    logger.info("[MULTIFEED_SELECTION] source=queue_pick link=%s important=%s", best.get("link"), bool(best.get("important", False)))
    return {
        "published": None,
        "title": str(best.get("title") or ""),
        "link": str(best.get("link") or ""),
        "feed_url": str(best.get("feed_url") or ""),
        "summary": str(best.get("summary") or ""),
        "important": bool(best.get("important", False)),
        "score": int(best.get("score") or 0),
        "identity": str(best.get("identity") or ""),
    }


def pick_best_candidate_for_cycle(cfg: dict, merged_candidates: list[dict], blocked_now: bool) -> dict | None:
    now_utc = datetime.now(timezone.utc)
    combined: list[dict] = []

    for queued in _queue_items(cfg):
        if _queue_item_is_fresh(cfg, queued, now_utc):
            combined.append(dict(queued))

    for candidate in merged_candidates:
        identity = str(candidate.get("identity") or _candidate_identity_token(str(candidate.get("link") or ""), str(candidate.get("title") or "")))
        published = candidate.get("published")
        published_iso = _entry_time_iso({"published_parsed": published}) if published else ""
        combined.append(
            {
                "identity": identity,
                "link": str(candidate.get("link") or ""),
                "title": str(candidate.get("title") or ""),
                "feed_url": str(candidate.get("feed_url") or ""),
                "score": int(candidate.get("score") or 0),
                "published_at": published_iso,
                "summary": str(candidate.get("summary") or ""),
                "important": bool(candidate.get("important", False)),
                "reason": "fresh_scan",
                "published": published,
            }
        )

    deduped: dict[str, dict] = {}
    for item in combined:
        token = str(item.get("identity") or "")
        prev = deduped.get(token)
        if not prev or (bool(item.get("important", False)), int(item.get("score") or 0), str(item.get("published_at") or "")) > (
            bool(prev.get("important", False)),
            int(prev.get("score") or 0),
            str(prev.get("published_at") or ""),
        ):
            deduped[token] = item

    valid_items: list[dict] = []
    for item in deduped.values():
        published_struct = item.get("published")
        if published_struct is None and item.get("published_at"):
            try:
                dt = datetime.fromisoformat(str(item.get("published_at")).replace("Z", "+00:00"))
                published_struct = dt.utctimetuple()
            except Exception:
                published_struct = None
        if candidate_is_fresh(cfg, published_struct, now_utc, "cycle_eval", is_important=bool(item.get("important", False))):
            valid_items.append(item)

    valid_items.sort(
        key=lambda x: (bool(x.get("important", False)), int(x.get("score") or 0), str(x.get("published_at") or ""), str(x.get("title") or "")),
        reverse=True,
    )
    logger.info(
        "[MULTIFEED_SELECTION] blocked=%s incoming=%s deduped=%s valid=%s",
        blocked_now,
        len(merged_candidates),
        len(deduped),
        len(valid_items),
    )

    if blocked_now:
        cfg["rss_candidate_queue"] = valid_items[-200:]
        logger.info("[BLOCKED_HOURS_ACTIVE] queued=%s", len(valid_items))
        return None

    if not valid_items:
        cfg["rss_candidate_queue"] = []
        return None

    winner = valid_items[0]
    leftovers = valid_items[1:]
    cfg["rss_candidate_queue"] = leftovers[-200:]
    logger.info(
        "[MULTIFEED_SELECTION] winner=%s important=%s score=%s leftovers=%s",
        winner.get("link"),
        bool(winner.get("important", False)),
        int(winner.get("score") or 0),
        len(leftovers),
    )
    return {
        "published": winner.get("published"),
        "title": str(winner.get("title") or ""),
        "link": str(winner.get("link") or ""),
        "feed_url": str(winner.get("feed_url") or ""),
        "summary": str(winner.get("summary") or ""),
        "important": bool(winner.get("important", False)),
    }

def extract_summary_for_link(feed_url: str, link_normalized: str, limit: int = 20) -> str:
    fp = feedparser.parse(feed_url)
    entries = getattr(fp, "entries", []) or []
    for e in entries[:limit]:
        link = _entry_primary_link(e)
        if not link:
            continue
        if normalize_url(link) == link_normalized:
            return clean_text(_entry_get(e, "summary", "") or _entry_get(e, "description", "") or "")
    return ""


def extract_rss_context_for_link(feed_url: str, link_normalized: str, limit: int = 20) -> dict:
    fp = feedparser.parse(feed_url)
    entries = getattr(fp, "entries", []) or []
    for e in entries[:limit]:
        link = _entry_primary_link(e)
        if not link:
            continue
        if normalize_url(link) != link_normalized:
            continue
        summary = clean_text(_entry_get(e, "summary", "") or _entry_get(e, "description", "") or "")
        content_chunks = []
        content = _entry_get(e, "content", []) or []
        for item in content:
            if isinstance(item, dict):
                value = clean_text(item.get("value") or "")
                if value:
                    content_chunks.append(value)
        content_text = clean_text("\n\n".join(content_chunks))

        source_parts = []
        source_data = _entry_get(e, "source")
        if isinstance(source_data, dict):
            source_parts.extend([source_data.get("title") or "", source_data.get("href") or ""])
        elif source_data:
            source_parts.append(str(source_data))
        source_parts.extend([
            _entry_get(e, "author", "") or "",
            _entry_get(e, "publisher", "") or "",
            _entry_get(e, "tags", "") or "",
        ])
        source_meta = clean_text(" | ".join([str(x) for x in source_parts if x]))

        return {
            "summary": summary,
            "content": content_text,
            "source_meta": source_meta,
            "source_url": clean_text(link),
        }
    return {"summary": "", "content": "", "source_meta": "", "source_url": ""}


def assess_rss_context(title: str, summary: str, content: str, source_meta: str, link: str, feed_url: str = "") -> tuple[bool, bool, str]:
    title_c = clean_text(title)
    summary_c = clean_text(summary)
    content_c = clean_text(content)
    source_c = clean_text(source_meta)
    combined = clean_text("\n".join([title_c, summary_c, content_c]))
    text_len = len(combined)
    alpha_words = re.findall(r"[A-Za-zА-Яа-яЁё]{3,}", combined)
    has_digits = bool(re.search(r"\d", combined))
    has_mentions = bool(re.search(r"[@#]", combined))
    vague_markers = re.findall(r"(?i)\b(link in bio|new post|story|watch this|check this|coming soon|more soon|stay tuned|new update)\b", combined)
    social_signal = bool(re.search(r"(?i)(instagram|instagr\.am|twitter|x\.com|t\.co|facebook|tiktok)", " ".join([feed_url, link, source_c])))
    low_info = text_len < 160 or len(alpha_words) < 18
    very_vague = len(vague_markers) >= 2 or (has_mentions and len(alpha_words) < 22)
    weak_context = low_info or (social_signal and (very_vague or not has_digits and len(alpha_words) < 30))
    return weak_context, social_signal, combined[:1500]


def build_rss_generation_input(feed_url: str, link: str, title: str) -> tuple[str, str, bool, bool]:
    context_data = extract_rss_context_for_link(feed_url, link)
    summary = context_data.get("summary") or ""
    weak_context, social_source, source_context = assess_rss_context(
        title,
        summary,
        context_data.get("content") or "",
        context_data.get("source_meta") or "",
        context_data.get("source_url") or link,
        feed_url,
    )
    return summary, source_context, weak_context, social_source


def _entry_get(entry, key, default=None):
    if isinstance(entry, dict):
        return entry.get(key, default)
    return getattr(entry, key, default)


def _safe_int(value) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def _normalize_image_url(url: str, base_url: str = "") -> str | None:
    raw = html.unescape((url or "").strip())
    if not raw:
        return None
    if raw.startswith("//"):
        raw = "https:" + raw
    raw = re.sub(r"\s+", "", raw)
    full = urljoin(base_url, raw)
    full = html.unescape(full).strip()
    parsed = urlsplit(full)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    logger.info("[IMG_URL_NORMALIZED] raw=%s normalized=%s", (url or "")[:180], full[:240])
    return full


def _looks_like_image_resource(url: str) -> bool:
    parsed = urlsplit(url or "")
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False

    path = (parsed.path or "").lower()
    if re.search(r"\.(jpg|jpeg|png|webp|gif|bmp|svg|avif|heic|heif|tiff?)$", path):
        return True
    if re.search(r"\.(html?|php|asp|aspx|json|xml|txt)$", path):
        return False

    query_l = (parsed.query or "").lower()
    if any(k in query_l for k in ("format=", "fm=", "ext=", "image=", "img=", "name=orig", "name=large", "name=4096x4096")):
        return True
    if any(p in path for p in ("/media/", "/image/", "/images/", "/img/", "/photo/", "/photos/")):
        return True

    return True


def _is_thumbnailish_url(url: str) -> bool:
    return bool(re.search(r"(?i)(thumb|thumbnail|sprite|icon|avatar|\bsmall\b|\bmini\b|\b120x\b|\b150x\b)", url or ""))


def _is_too_small(width: int | None, height: int | None) -> bool:
    if width and height:
        return width < 120 or height < 120 or (width * height < 20000)
    return False


def _rss_image_quality_issue(img: Image.Image, image_url: str = "") -> str | None:
    w, h = img.size
    if w < 260 or h < 260:
        return "too_small_dim"
    if w * h < 160000:
        return "too_small_area"

    ratio = w / max(1, h)
    if ratio < 0.62 or ratio > 2.8:
        return "extreme_aspect_ratio"

    max_side = max(w, h)
    min_side = min(w, h)
    square_ratio = (max_side / max(1, min_side)) if min_side else 999
    if square_ratio <= 1.15 and max_side <= 480:
        return "small_square_like_logo"

    if re.search(r"(?i)(logo|avatar|favicon|icon|profile|brandmark)", image_url or "") and max_side <= 720:
        return "logo_like_url"

    try:
        sample = img.convert("RGB").resize((64, 64), Image.Resampling.BILINEAR)
        palette = sample.getcolors(maxcolors=128)
        if palette is not None and len(palette) <= 10 and square_ratio <= 1.2 and max_side <= 720:
            return "flat_palette_logo_like"
    except Exception:
        pass

    return None


def _candidate_score(priority: int, url: str, width: int | None, height: int | None) -> tuple[int, int, int, int]:
    area = (width or 0) * (height or 0)
    has_size = 1 if width and height else 0
    non_thumb = 0 if _is_thumbnailish_url(url) else 1
    return (priority, has_size, area, non_thumb)


def _extract_og_image(article_url: str) -> str | None:
    try:
        r = requests.get(
            article_url,
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TGAutoPosterBot/1.0)"},
        )
        r.raise_for_status()
        html = r.text or ""
    except Exception:
        return None

    m = re.search(
        r"<meta[^>]+(?:property|name)=[\"']og:image[\"'][^>]+content=[\"']([^\"']+)[\"']",
        html,
        flags=re.IGNORECASE,
    )
    if not m:
        m = re.search(
            r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]+(?:property|name)=[\"']og:image[\"']",
            html,
            flags=re.IGNORECASE,
        )
    if not m:
        return None
    return _normalize_image_url(m.group(1), article_url)


class _FirstImageHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.first_image_url: str | None = None

    def handle_starttag(self, tag, attrs):
        if self.first_image_url or (tag or "").lower() != "img":
            return
        attrs_map = {str(k).lower(): (v or "") for k, v in attrs}
        candidate = attrs_map.get("src") or attrs_map.get("data-src") or attrs_map.get("data-original") or attrs_map.get("data-lazy-src")
        if candidate:
            self.first_image_url = candidate


def _extract_first_image_from_html(html_fragment: str, base_url: str = "") -> str | None:
    if not html_fragment:
        return None
    parser = _FirstImageHTMLParser()
    try:
        parser.feed(html.unescape(html_fragment))
    except Exception:
        return None
    if not parser.first_image_url:
        return None
    return _normalize_image_url(parser.first_image_url, base_url)


def _download_image_to_tempfile(image_url: str, marker: str = "normal") -> tuple[Path | None, str | None]:
    logger.info("[IMG_DOWNLOAD_START] marker=%s url=%s", marker, image_url)
    try:
        resp = requests.get(
            image_url,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TGAutoPosterBot/1.0)"},
        )
        resp.raise_for_status()
        content_type = (resp.headers.get("Content-Type") or "").lower()
        raw = io.BytesIO(resp.content)
        img = Image.open(raw)
        img.load()
        fmt = (img.format or "").upper()
        out_ext = ".jpg"
        save_format = "JPEG"
        if fmt == "PNG":
            out_ext = ".png"
            save_format = "PNG"
        with tempfile.NamedTemporaryFile(delete=False, suffix=out_ext) as tmp:
            temp_path = Path(tmp.name)
        image_to_save = img.convert("RGBA") if save_format == "PNG" else img.convert("RGB")
        image_to_save.save(temp_path, format=save_format, quality=92, optimize=True)
        logger.info(
            "[IMG_DOWNLOAD_OK] marker=%s url=%s content_type=%s detected_format=%s output=%s",
            marker,
            image_url,
            content_type or "unknown",
            fmt or "unknown",
            save_format,
        )
        return temp_path, None
    except Exception as exc:
        logger.warning("[IMG_DOWNLOAD_FAIL] marker=%s url=%s reason=%s", marker, image_url, exc)
        return None, "download_or_decode_failed"


def _watermark_ratios(cfg: dict, mode: str = "rss") -> tuple[float, float, float]:
    scale_pct = cfg.get(f"{mode}_watermark_scale_pct", 12.0)
    margin_pct = cfg.get(f"{mode}_watermark_margin_pct", 3.5)
    try:
        scale_ratio = float(scale_pct) / 100.0
    except (TypeError, ValueError):
        scale_ratio = 0.12
    try:
        margin_ratio = float(margin_pct) / 100.0
    except (TypeError, ValueError):
        margin_ratio = 0.035
    scale_ratio = min(0.11, max(0.06, scale_ratio))
    margin_ratio = min(0.07, max(0.03, margin_ratio))
    margin_y_ratio = min(0.08, max(0.03, margin_ratio * 1.05))
    return scale_ratio, margin_ratio, margin_y_ratio


def _select_compose_strategy(
    canvas_w: int,
    canvas_h: int,
    source_w: int,
    source_h: int,
) -> tuple[str, str | None, str, dict]:
    margin_x = max(8, int(canvas_w * 0.08))
    margin_y = max(8, int(canvas_h * 0.08))
    area_w = max(1, canvas_w - 2 * margin_x)
    area_h = max(1, canvas_h - 2 * margin_y)
    source_ratio = source_w / max(1, source_h)
    area_ratio = area_w / max(1, area_h)
    aspect_mismatch = abs(math.log(max(0.01, source_ratio / max(0.01, area_ratio))))

    contain_scale = min(area_w / max(1, source_w), area_h / max(1, source_h))
    contain_w = max(1, int(source_w * contain_scale))
    contain_h = max(1, int(source_h * contain_scale))
    rendered_area_ratio = (contain_w * contain_h) / max(1, canvas_w * canvas_h)
    min_render_side_ratio = min(contain_w / max(1, canvas_w), contain_h / max(1, canvas_h))

    fit_mode = "contain"
    if 0.85 <= source_ratio <= 1.9 and aspect_mismatch <= 0.16:
        fit_mode = "cover"
    elif source_ratio < 0.70 or source_ratio > 2.30:
        fit_mode = "padded_contain"

    reject_reason = None
    if min(source_w, source_h) < 300:
        reject_reason = "source_too_small_pixels"
    elif rendered_area_ratio < 0.33:
        reject_reason = "rendered_area_too_small"
    elif min(contain_w, contain_h) < 320:
        reject_reason = "rendered_min_side_too_small"
    elif min_render_side_ratio < 0.38:
        reject_reason = "rendered_relative_size_too_small"
    elif aspect_mismatch > 1.05 and source_ratio < 0.75:
        reject_reason = "severe_aspect_mismatch_portrait"

    mode = "use_background" if reject_reason is None else "use_original"
    metrics = {
        "margin_x": margin_x,
        "margin_y": margin_y,
        "area_w": area_w,
        "area_h": area_h,
        "source_ratio": source_ratio,
        "area_ratio": area_ratio,
        "aspect_mismatch": aspect_mismatch,
        "rendered_area_ratio": rendered_area_ratio,
        "contain_w": contain_w,
        "contain_h": contain_h,
        "min_render_side_ratio": min_render_side_ratio,
    }
    return mode, reject_reason, fit_mode, metrics


def _apply_watermark_to_canvas(
    canvas: Image.Image,
    watermark_path: Path | None,
    cfg: dict,
    mode: str = "rss",
    branch: str = "unknown",
) -> bool:
    logger.info("[WM_ENABLED] branch=%s enabled=%s", branch, bool(watermark_path))
    if not watermark_path or not watermark_path.exists() or not watermark_path.is_file():
        logger.warning("[WM_APPLY_FAIL] branch=%s reason=watermark_file_missing path=%s", branch, watermark_path)
        return False
    try:
        wm = Image.open(watermark_path).convert("RGBA")
        canvas_w, canvas_h = canvas.size
        logger.info("[CANVAS_SIZE] branch=%s width=%s height=%s", branch, canvas_w, canvas_h)

        scale_ratio, margin_x_ratio, margin_y_ratio = _watermark_ratios(cfg, mode)
        target_w = max(24, int(canvas_w * scale_ratio))
        target_w = min(target_w, max(24, int(canvas_w * 0.16)))
        target_h = max(1, int(target_w * (wm.height / max(1, wm.width))))
        max_h = max(16, int(canvas_h * 0.18))
        if target_h > max_h:
            adjust = max_h / max(1, target_h)
            target_h = max(1, int(target_h * adjust))
            target_w = max(1, int(target_w * adjust))
        wm_resized = wm.resize((target_w, target_h), Image.Resampling.LANCZOS)

        margin_x = max(4, int(canvas_w * margin_x_ratio))
        margin_y = max(4, int(canvas_h * margin_y_ratio))
        pos_x = canvas_w - wm_resized.width - margin_x
        pos_y = canvas_h - wm_resized.height - margin_y
        pos_x = max(0, pos_x)
        pos_y = max(0, pos_y)

        logger.info(
            "[WM_SCALE] branch=%s width_ratio=%.4f target_width=%s target_height=%s",
            branch,
            scale_ratio,
            wm_resized.width,
            wm_resized.height,
        )
        logger.info(
            "[WM_MARGIN] branch=%s margin_x=%s margin_y=%s margin_x_ratio=%.4f margin_y_ratio=%.4f",
            branch,
            margin_x,
            margin_y,
            margin_x_ratio,
            margin_y_ratio,
        )
        logger.info(
            "[WM_POSITION] branch=%s corner=bottom_right x=%s y=%s",
            branch,
            pos_x,
            pos_y,
        )

        canvas.paste(wm_resized, (pos_x, pos_y), wm_resized)
        logger.info("[WM_APPLY_OK] branch=%s", branch)
        return True
    except Exception as exc:
        logger.warning("[WM_APPLY_FAIL] branch=%s reason=%s", branch, exc)
        return False


def _watermark_original_image_with_status(
    cfg: dict,
    image_url: str,
    watermark_path: Path | None,
    mode: str = "rss",
    branch: str = "original_fallback",
) -> tuple[Path | None, str | None]:
    logger.info("[IMG_BRANCH] branch=%s", branch)
    downloaded_path, err = _download_image_to_tempfile(image_url, marker="wm_original")
    if not downloaded_path:
        return None, err or "source_download_failed"
    try:
        img = Image.open(downloaded_path).convert("RGBA")
    except Exception as exc:
        try:
            downloaded_path.unlink(missing_ok=True)
        except Exception:
            pass
        return None, f"source_decode_failed:{exc}"
    finally:
        try:
            downloaded_path.unlink(missing_ok=True)
        except Exception:
            pass

    logger.info("[CANVAS_SIZE] branch=%s width=%s height=%s", branch, img.width, img.height)
    logger.info("[SRC_IMAGE_SIZE] branch=%s width=%s height=%s", branch, img.width, img.height)
    logger.info("[SRC_ASPECT] branch=%s ratio=%.4f", branch, img.width / max(1, img.height))
    logger.info("[COMPOSE_MODE] branch=%s mode=use_original", branch)
    logger.info("[COMPOSE_USE_ORIGINAL] branch=%s reason=watermark_on_original", branch)
    logger.info("[FIT_MODE] branch=%s mode=source_original", branch)
    if not _apply_watermark_to_canvas(img, watermark_path, cfg, mode=mode, branch=branch):
        logger.warning("[WM_APPLY_FAIL] branch=%s reason=watermark_apply_failed_fallback_to_unwatermarked", branch)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            temp_path = Path(tmp.name)
        img.convert("RGB").save(temp_path, format="JPEG", quality=92, optimize=True)
        logger.info("[FINAL_RENDER_OK] branch=%s output=%s", branch, temp_path)
        return temp_path, None
    except Exception as exc:
        return None, f"save_failed:{exc}"


def extract_image_url_for_link(feed_url: str, link_normalized: str, limit: int = 20) -> str | None:
    logger.info("[IMG_EXTRACT_START] feed=%s link=%s", feed_url, link_normalized)
    fp = feedparser.parse(feed_url)
    entries = getattr(fp, "entries", []) or []
    for e in entries[:limit]:
        link = _entry_primary_link(e)
        if not link or normalize_url(link) != link_normalized:
            continue

        best_url = None
        best_score = None

        def consider(url: str, priority: int, width=None, height=None, base_url: str = "", marker: str = ""):
            nonlocal best_url, best_score
            normalized = _normalize_image_url(url, base_url)
            if not normalized:
                return
            if not _looks_like_image_resource(normalized):
                return
            w = _safe_int(width)
            h = _safe_int(height)
            if _is_too_small(w, h):
                return
            score = _candidate_score(priority, normalized, w, h)
            if best_score is None or score > best_score:
                best_score = score
                best_url = normalized
                if marker:
                    logger.info("%s url=%s", marker, normalized)

        media_content = _entry_get(e, "media_content", []) or []
        for item in media_content:
            if not isinstance(item, dict):
                continue
            consider(
                item.get("url") or "",
                priority=800,
                width=item.get("width"),
                height=item.get("height"),
                base_url=link,
                marker="[IMG_FOUND_MEDIA_CONTENT]",
            )

        media_thumbnail = _entry_get(e, "media_thumbnail", []) or []
        for item in media_thumbnail:
            if not isinstance(item, dict):
                continue
            consider(
                item.get("url") or "",
                priority=700,
                width=item.get("width"),
                height=item.get("height"),
                base_url=link,
                marker="[IMG_FOUND_MEDIA_THUMBNAIL]",
            )

        enclosure = _entry_get(e, "enclosure", {}) or {}
        if isinstance(enclosure, dict):
            consider(
                enclosure.get("href") or enclosure.get("url") or "",
                priority=650,
                width=enclosure.get("width"),
                height=enclosure.get("height"),
                base_url=link,
                marker="[IMG_FOUND_ENCLOSURE]",
            )

        media_content = _entry_get(e, "media_content", []) or []
        for item in media_content:
            if not isinstance(item, dict):
                continue
            consider(item.get("url") or "", priority=600, width=item.get("width"), height=item.get("height"), base_url=link, marker="[IMG_FOUND_MEDIA_CONTENT]")

        enclosures = _entry_get(e, "enclosures", []) or []
        for item in enclosures:
            if not isinstance(item, dict):
                continue
            url = item.get("url") or ""
            etype = (item.get("type") or "").lower()
            if "image" in etype or not etype:
                consider(url, priority=550, width=item.get("width"), height=item.get("height"), base_url=link, marker="[IMG_FOUND_ENCLOSURE]")

        image_obj = _entry_get(e, "image", {}) or {}
        if isinstance(image_obj, dict):
            consider(
                image_obj.get("href") or image_obj.get("url") or "",
                priority=500,
                base_url=link,
                marker="[IMG_FOUND_IMAGE_FIELD]",
            )

        html_sources: list[tuple[str, str, int]] = []
        content_items = _entry_get(e, "content", []) or []
        for item in content_items:
            if isinstance(item, dict):
                value = (item.get("value") or "").strip()
                if value:
                    html_sources.append((value, "[IMG_FOUND_CONTENT_HTML]", 450))
        summary_html = _entry_get(e, "summary", "") or ""
        if summary_html:
            html_sources.append((summary_html, "[IMG_FOUND_SUMMARY_HTML]", 400))
        description_html = _entry_get(e, "description", "") or ""
        if description_html:
            html_sources.append((description_html, "[IMG_FOUND_DESCRIPTION_HTML]", 350))

        for html_chunk, marker, priority in html_sources:
            img_url = _extract_first_image_from_html(html_chunk, link)
            if img_url:
                consider(img_url, priority=priority, base_url=link, marker=marker)

        if best_url:
            if _is_thumbnailish_url(best_url):
                logger.info("[IMG_PIPELINE_RESULT] stage=extract result=reject_thumbnail_like url=%s", best_url)
                return None
            logger.info("[IMG_PIPELINE_RESULT] stage=extract result=image_found source=%s", best_url)
            return best_url

        og_image = _extract_og_image(link)
        if og_image:
            if _is_thumbnailish_url(og_image):
                logger.info("[IMG_PIPELINE_RESULT] stage=extract result=reject_og_thumbnail_like url=%s", og_image)
                return None
            logger.info("[IMG_PIPELINE_RESULT] stage=extract result=og_image url=%s", og_image)
            return og_image

        break
    logger.info("[IMG_PIPELINE_RESULT] stage=extract result=no_image")
    return None


def format_rss_message(cfg: dict, msg: str, link: str) -> str:
    return build_rss_message_payload(cfg, msg, link)[0]


def _message_entity_to_dict(entity: MessageEntity) -> dict:
    data = entity.to_dict()
    return {k: v for k, v in data.items() if v is not None}


def _load_message_entities(data: list | None, offset_shift: int = 0, min_offset: int = 0, max_offset: int | None = None) -> list[MessageEntity]:
    entities: list[MessageEntity] = []
    for item in data or []:
        if not isinstance(item, dict):
            continue
        try:
            offset = int(item.get("offset", 0))
            length = int(item.get("length", 0))
        except (TypeError, ValueError):
            continue
        if length <= 0:
            continue
        start = offset + offset_shift
        end = start + length
        if start < min_offset:
            continue
        if max_offset is not None and end > max_offset:
            continue
        payload = dict(item)
        payload["offset"] = start - min_offset
        payload["length"] = length
        try:
            entities.append(MessageEntity(**payload))
        except TypeError:
            continue
    return entities


def _first_nonempty_line_bounds(text: str) -> tuple[int, int] | None:
    start = 0
    for line in text.splitlines(keepends=True):
        end = start + len(line)
        content = line.rstrip("\r\n")
        if content.strip():
            return start, start + len(content)
        start = end
    return None


def _utf16_len(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def apply_bold_title(text: str, entities: list[MessageEntity]) -> list[MessageEntity]:
    bounds = _first_nonempty_line_bounds(text)
    if not bounds:
        return entities
    start, end = bounds
    utf16_start = _utf16_len(text[:start])
    utf16_end = _utf16_len(text[:end])
    title_has_bold = any(
        e.type == MessageEntity.BOLD and e.offset <= utf16_start and (e.offset + e.length) >= utf16_end
        for e in entities
    )
    if title_has_bold:
        return entities
    return entities + [MessageEntity(type=MessageEntity.BOLD, offset=utf16_start, length=utf16_end - utf16_start)]


def emoji_style_note(cfg: dict, mode: str) -> str:
    text = (cfg.get(f"{mode}_custom_emojis_text") or "").strip()
    if not text:
        return ""
    return f"Preferred emoji style: you may naturally use these emoji when relevant: {text}\n"


def build_rss_message_payload(cfg: dict, msg: str, link: str) -> tuple[str, list[MessageEntity]]:
    return msg, []


async def send_rss_to_channel(bot, cfg: dict, channel: str, msg: str, link: str, image_url: str | None, temp_file: Path | None = None) -> None:
    final_text, final_entities = build_rss_message_payload(cfg, msg, link)
    used_temp_files: list[Path] = []
    if temp_file:
        used_temp_files.append(temp_file)
    try:
        if not image_url and not temp_file:
            raise RuntimeError("RSS image is required, but no image was prepared")
        caption = final_text
        photo_candidates: list[Path | str] = []
        if temp_file:
            photo_candidates.append(temp_file)
        elif image_url:
            photo_candidates.append(image_url)
        if image_url and not temp_file:
            fallback_file, _ = _download_image_to_tempfile(image_url, marker="send_fallback_upload")
            if fallback_file:
                photo_candidates.append(fallback_file)
                used_temp_files.append(fallback_file)

        last_exc: Exception | None = None
        for idx, photo_input in enumerate(photo_candidates):
            try:
                logger.info("[TG_SEND_PHOTO] attempt=%s input_type=%s", idx + 1, type(photo_input).__name__)
                caption_entities = _load_message_entities([_message_entity_to_dict(e) for e in final_entities], max_offset=1024)
                await bot.send_photo(chat_id=channel, photo=photo_input, caption=caption[:1024], caption_entities=caption_entities or None)
                logger.info("[IMG_PIPELINE_RESULT] stage=telegram_send result=photo")
                return
            except Exception as exc:
                last_exc = exc
                logger.warning("[IMG_DOWNLOAD_FAIL] marker=tg_send_photo_attempt reason=%s", exc)
        raise RuntimeError(f"Failed to send RSS photo: {last_exc}")
    finally:
        for path in used_temp_files:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass


async def _ensure_asset_path(bot, cfg: dict, user_id: int, mode: str, asset_type: str) -> str:
    path_key = f"{mode}_{asset_type}_image_path"
    existing_rel = str(cfg.get(path_key) or "").strip()
    if existing_rel:
        existing_abs = BASE_DIR / existing_rel
        if existing_abs.exists() and existing_abs.is_file():
            return existing_rel

    file_id = str(cfg.get(f"{mode}_{asset_type}_file_id") or "").strip()
    if not file_id:
        return ""

    try:
        file_obj = await bot.get_file(file_id)
        ext = "png" if asset_type == "watermark" else "jpg"
        target_abs, target_rel = asset_paths(user_id, mode, asset_type, ext)
        target_abs.parent.mkdir(parents=True, exist_ok=True)
        await file_obj.download_to_drive(str(target_abs))
        cfg[path_key] = target_rel
        return target_rel
    except Exception:
        logger.exception("Failed to download %s %s asset", mode, asset_type)
        return ""


def _compose_rss_image_with_status(
    template_path: Path,
    rss_image_url: str,
    watermark_path: Path | None = None,
    cfg: dict | None = None,
) -> tuple[Path | None, str | None]:
    logger.info("[IMG_BRANCH] branch=template_compose")
    logger.info("[IMG_PROCESS_START] stage=template_compose url=%s", rss_image_url)
    base = None
    rss_img = None
    try:
        base = Image.open(template_path).convert("RGBA")
    except Exception:
        logger.warning("RSS preview template load failed: %s", template_path)
        return None, "template_load_failed"

    downloaded_path, _ = _download_image_to_tempfile(rss_image_url, marker="compose_template")
    if not downloaded_path:
        logger.warning("[IMG_PROCESS_FAIL] stage=template_compose reason=rss_image_unusable")
        return None, "rss_image_unusable"
    try:
        rss_img = Image.open(downloaded_path).convert("RGBA")
    except Exception:
        logger.warning("[IMG_PROCESS_FAIL] stage=template_compose reason=rss_image_unusable")
        return None, "rss_image_unusable"
    finally:
        try:
            downloaded_path.unlink(missing_ok=True)
        except Exception:
            pass

    quality_issue = _rss_image_quality_issue(rss_img, rss_image_url)
    if quality_issue:
        logger.info("RSS image rejected for composition (%s): %s", quality_issue, rss_image_url)
        return None, "rss_image_rejected"

    try:
        canvas_w, canvas_h = base.size
        logger.info("[CANVAS_SIZE] branch=template_compose width=%s height=%s", canvas_w, canvas_h)
        logger.info("[SRC_IMAGE_SIZE] branch=template_compose width=%s height=%s", rss_img.width, rss_img.height)

        compose_mode, reject_reason, fit_mode, metrics = _select_compose_strategy(
            canvas_w=canvas_w,
            canvas_h=canvas_h,
            source_w=rss_img.width,
            source_h=rss_img.height,
        )
        logger.info(
            "[SRC_ASPECT] branch=template_compose ratio=%.4f mismatch=%.4f",
            metrics["source_ratio"],
            metrics["aspect_mismatch"],
        )
        logger.info(
            "[COMPOSE_MODE] branch=template_compose mode=%s fit_mode=%s rendered_area_ratio=%.4f min_render_side_ratio=%.4f",
            compose_mode,
            fit_mode,
            metrics["rendered_area_ratio"],
            metrics["min_render_side_ratio"],
        )
        if reject_reason:
            logger.info("[COMPOSE_REJECT_BACKGROUND] branch=template_compose reason=%s", reject_reason)
            logger.info("[COMPOSE_USE_ORIGINAL] branch=template_compose reason=%s", reject_reason)
            return None, "compose_unsuitable_background"
        logger.info("[COMPOSE_USE_BACKGROUND] branch=template_compose fit_mode=%s", fit_mode)
        logger.info(
            "[FIT_MODE] branch=template_compose mode=%s source_ratio=%.4f area_ratio=%.4f",
            fit_mode,
            metrics["source_ratio"],
            metrics["area_ratio"],
        )

        margin_x = metrics["margin_x"]
        margin_y = metrics["margin_y"]
        area_w = metrics["area_w"]
        area_h = metrics["area_h"]

        if fit_mode == "cover":
            scale = max(area_w / max(1, rss_img.width), area_h / max(1, rss_img.height))
            fitted_w = max(1, int(rss_img.width * scale))
            fitted_h = max(1, int(rss_img.height * scale))
            fitted = rss_img.resize((fitted_w, fitted_h), Image.Resampling.LANCZOS)
            crop_x = max(0, (fitted_w - area_w) // 2)
            crop_y = max(0, (fitted_h - area_h) // 2)
            fitted = fitted.crop((crop_x, crop_y, crop_x + area_w, crop_y + area_h))
            fitted_w, fitted_h = area_w, area_h
        else:
            scale = min(area_w / max(1, rss_img.width), area_h / max(1, rss_img.height))
            fitted_w = max(1, int(rss_img.width * scale))
            fitted_h = max(1, int(rss_img.height * scale))
            fitted = rss_img.resize((fitted_w, fitted_h), Image.Resampling.LANCZOS)
            if fit_mode == "padded_contain":
                panel_pad_x = max(6, int(canvas_w * 0.01))
                panel_pad_y = max(6, int(canvas_h * 0.01))
                panel = Image.new(
                    "RGBA",
                    (min(area_w, fitted_w + 2 * panel_pad_x), min(area_h, fitted_h + 2 * panel_pad_y)),
                    (0, 0, 0, 56),
                )
                panel_x = margin_x + max(0, (area_w - panel.width) // 2)
                panel_y = margin_y + max(0, (area_h - panel.height) // 2)
                base.paste(panel, (panel_x, panel_y), panel)
        paste_x = margin_x + max(0, (area_w - fitted_w) // 2)
        paste_y = margin_y + max(0, (area_h - fitted_h) // 2)
        base.paste(fitted, (paste_x, paste_y), fitted)

        if watermark_path and not _apply_watermark_to_canvas(base, watermark_path, cfg or {}, mode="rss", branch="template_compose"):
            logger.warning("[WM_APPLY_FAIL] branch=template_compose reason=watermark_apply_failed_fallback_to_unwatermarked")

        composed = base.convert("RGB")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            temp_path = Path(tmp.name)
        composed.save(temp_path, format="JPEG", quality=92, optimize=True)
        logger.info("[FINAL_RENDER_OK] branch=template_compose output=%s", temp_path)
        logger.info("[IMG_PROCESS_OK] stage=template_compose output=%s", temp_path)
        return temp_path, None
    except Exception as exc:
        logger.warning("[IMG_PROCESS_FAIL] stage=template_compose reason=%s", exc)
        return None, "compose_failed"


def _compose_rss_image(
    template_path: Path,
    rss_image_url: str,
    watermark_path: Path | None = None,
    cfg: dict | None = None,
) -> Path | None:
    composed_path, _ = _compose_rss_image_with_status(template_path, rss_image_url, watermark_path, cfg=cfg)
    return composed_path


def _compose_vertical_rss_image_with_optional_watermark(
    rss_image_url: str,
    watermark_path: Path | None = None,
    cfg: dict | None = None,
) -> tuple[Path | None, bool, str | None]:
    logger.info("[IMG_BRANCH] branch=vertical_compose")
    logger.info("[IMG_PROCESS_START] stage=vertical_compose url=%s", rss_image_url)
    downloaded_path, _ = _download_image_to_tempfile(rss_image_url, marker="compose_vertical")
    if not downloaded_path:
        logger.warning("[IMG_PROCESS_FAIL] stage=vertical_compose reason=rss_image_unusable")
        return None, False, "rss_image_unusable"
    try:
        rss_img = Image.open(downloaded_path).convert("RGBA")
    except Exception:
        logger.warning("[IMG_PROCESS_FAIL] stage=vertical_compose reason=rss_image_unusable")
        return None, False, "rss_image_unusable"
    finally:
        try:
            downloaded_path.unlink(missing_ok=True)
        except Exception:
            pass

    source_ratio = rss_img.width / max(1, rss_img.height)
    logger.info("[SRC_ASPECT] branch=vertical_compose ratio=%.4f", source_ratio)
    if source_ratio >= 0.75:
        return None, False, None

    quality_issue = _rss_image_quality_issue(rss_img, rss_image_url)
    if quality_issue:
        logger.info("Vertical RSS image rejected (%s): %s", quality_issue, rss_image_url)
        return None, True, "rss_image_rejected"

    try:
        logger.info("[CANVAS_SIZE] branch=vertical_compose width=%s height=%s", rss_img.width, rss_img.height)
        logger.info("[SRC_IMAGE_SIZE] branch=vertical_compose width=%s height=%s", rss_img.width, rss_img.height)
        logger.info("[COMPOSE_MODE] branch=vertical_compose mode=use_original")
        logger.info("[COMPOSE_USE_ORIGINAL] branch=vertical_compose reason=portrait_original_strategy")
        logger.info("[FIT_MODE] branch=vertical_compose mode=source_original")
        if watermark_path and not _apply_watermark_to_canvas(rss_img, watermark_path, cfg or {}, mode="rss", branch="vertical_compose"):
            logger.warning("[WM_APPLY_FAIL] branch=vertical_compose reason=watermark_apply_failed_fallback_to_unwatermarked")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            temp_path = Path(tmp.name)
        rss_img.convert("RGB").save(temp_path, format="JPEG", quality=92, optimize=True)
        logger.info("[FINAL_RENDER_OK] branch=vertical_compose output=%s", temp_path)
        logger.info("[IMG_PROCESS_OK] stage=vertical_compose output=%s", temp_path)
        return temp_path, True, None
    except Exception as exc:
        logger.warning("[IMG_PROCESS_FAIL] stage=vertical_compose reason=%s", exc)
        return None, True, "compose_failed"


async def prepare_rss_image_for_sending(bot, cfg: dict, user_id: int, image_url: str | None) -> tuple[str | None, Path | None]:
    if not image_url:
        logger.info("[IMG_PIPELINE_RESULT] stage=prepare result=no_source_image")
        return None, None
    if not bool(cfg.get("use_rss_feed_image", True)):
        return image_url, None
    if str(cfg.get("mode") or "").strip().lower() not in ("rss", "both"):
        return image_url, None

    watermark_enabled = bool(cfg.get("rss_watermark_file_id"))
    logger.info("[WM_ENABLED] branch=prepare_send enabled=%s", watermark_enabled)
    watermark_rel = await _ensure_asset_path(bot, cfg, user_id, "rss", "watermark")
    watermark_path = (BASE_DIR / watermark_rel) if watermark_rel else None
    if watermark_enabled and not watermark_path:
        logger.warning("[WM_APPLY_FAIL] branch=prepare_send reason=watermark_enabled_but_asset_unavailable")
    logger.info("[WM_BRANCH] branch=vertical_compose")
    vertical_path, is_vertical, vertical_error = _compose_vertical_rss_image_with_optional_watermark(image_url, watermark_path, cfg=cfg)
    if is_vertical:
        if not vertical_path:
            if watermark_enabled:
                fallback_wm_path, fallback_err = _watermark_original_image_with_status(
                    cfg, image_url, watermark_path, mode="rss", branch="vertical_fallback_original"
                )
                if fallback_wm_path:
                    return str(fallback_wm_path), fallback_wm_path
                logger.warning("[WM_APPLY_FAIL] branch=vertical_fallback_original reason=%s", fallback_err)
            logger.info("[IMG_FALLBACK_ORIGINAL] reason=%s url=%s", vertical_error or "vertical_transform_failed", image_url)
            return image_url, None
        return str(vertical_path), vertical_path
    if watermark_enabled:
        fallback_wm_path, fallback_err = _watermark_original_image_with_status(
            cfg, image_url, watermark_path, mode="rss", branch="rss_original_only"
        )
        if fallback_wm_path:
            return str(fallback_wm_path), fallback_wm_path
        logger.warning("[WM_APPLY_FAIL] branch=rss_original_only reason=%s", fallback_err)
    return image_url, None


async def prepare_rss_preview_image_for_sending(bot, cfg: dict, user_id: int, image_url: str | None) -> tuple[str | None, Path | None, str | None]:
    if not image_url:
        logger.info("RSS preview image missing for user %s", user_id)
        return None, None, "preview_status_no_rss_image_text_only"
    if not bool(cfg.get("use_rss_feed_image", True)):
        return image_url, None, None
    if str(cfg.get("mode") or "").strip().lower() not in ("rss", "both"):
        return image_url, None, None

    watermark_enabled = bool(cfg.get("rss_watermark_file_id"))
    logger.info("[WM_ENABLED] branch=prepare_preview enabled=%s", watermark_enabled)
    watermark_rel = await _ensure_asset_path(bot, cfg, user_id, "rss", "watermark")
    watermark_path = (BASE_DIR / watermark_rel) if watermark_rel else None
    if watermark_enabled and not watermark_path:
        logger.warning("[WM_APPLY_FAIL] branch=prepare_preview reason=watermark_enabled_but_asset_unavailable")
    if cfg.get("rss_watermark_file_id") and not watermark_rel:
        logger.info("RSS preview watermark download failed for user %s", user_id)
        return image_url, None, "preview_status_asset_load_failed_normal"

    logger.info("[WM_BRANCH] branch=vertical_compose")
    vertical_path, is_vertical, vertical_error = _compose_vertical_rss_image_with_optional_watermark(image_url, watermark_path, cfg=cfg)
    if is_vertical:
        if not vertical_path:
            if watermark_enabled:
                fallback_wm_path, fallback_err = _watermark_original_image_with_status(
                    cfg, image_url, watermark_path, mode="rss", branch="preview_vertical_fallback_original"
                )
                if fallback_wm_path:
                    return str(fallback_wm_path), fallback_wm_path, None
                logger.warning("[WM_APPLY_FAIL] branch=preview_vertical_fallback_original reason=%s", fallback_err)
            logger.info("[IMG_FALLBACK_ORIGINAL] reason=%s url=%s", vertical_error or "vertical_transform_failed", image_url)
            return image_url, None, "preview_status_template_build_failed_normal"
        return str(vertical_path), vertical_path, None
    if watermark_enabled:
        fallback_wm_path, fallback_err = _watermark_original_image_with_status(
            cfg, image_url, watermark_path, mode="rss", branch="preview_rss_original_only"
        )
        if fallback_wm_path:
            return str(fallback_wm_path), fallback_wm_path, None
        logger.warning("[WM_APPLY_FAIL] branch=preview_rss_original_only reason=%s", fallback_err)
    return image_url, None, None

# ===================== LLM providers =====================
def ollama_generate_post(user_id: int, cfg: dict, title: str, summary: str, link: str, source_context: str = "", weak_context: bool = False, social_source: bool = False) -> str:
    style_prompt = get_mode_prompt(user_id, cfg, "rss")
    title = clean_text(title)
    summary = clean_text(summary)

    include_source_link = bool(cfg.get("include_rss_source_link", True))
    source_block = f"Source URL: {link}\n" if include_source_link else ""
    weak_context_rules = ""
    if weak_context:
        weak_context_rules = (
            "Context is weak or ambiguous. Use a cautious short summary style. "
            "State only what is explicitly present in title/summary/content. "
            "Do not infer hidden events or motives. Avoid confident specifics.\n"
        )
    if social_source:
        weak_context_rules += (
            "If this looks like a social update with thin context, keep it grounded and neutral. "
            "Do not pretend to understand media/story context that is not described in text.\n"
        )

    prompt = (
        style_prompt + "\n\n"
        "You are a Telegram editor. Rewrite naturally and clearly for Telegram; avoid robotic wording.\n"
        "Use only facts from the source content below. Do not invent details.\n"
        "Do not include source attribution, usernames, raw metadata, or links unless explicitly requested in the prompt/output settings.\n"
        "Return plain Telegram-ready text (no JSON, no code blocks). Preserve requested paragraph spacing and formatting.\n\n"
        f"Title: {title}\n"
        f"Summary: {summary}\n"
        f"Source content: {source_context[:1500]}\n"
        f"{source_block}"
        f"{weak_context_rules}"
        f"{emoji_style_note(cfg, 'rss')}"
    )

    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    txt = data.get("response", "")
    return sanitize_llm_post(txt, cfg, link)

def openai_compat_generate_post(user_id: int, cfg: dict, title: str, summary: str, link: str, source_context: str = "", weak_context: bool = False, social_source: bool = False) -> str:
    logger.info(
        "openai_compat_generate_post entered for user %s (api_key_present=%s, base_url=%s, model=%s)",
        user_id,
        "yes" if bool(OPENAI_API_KEY) else "no",
        OPENAI_BASE_URL,
        OPENAI_MODEL,
    )
    if not OPENAI_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY missing (set it in host variables)")

    style_prompt = get_mode_prompt(user_id, cfg, "rss")
    title = clean_text(title)
    summary = clean_text(summary)

    include_source_link = bool(cfg.get("include_rss_source_link", True))
    source_block = f"Source URL: {link}\n" if include_source_link else ""
    weak_context_rules = ""
    if weak_context:
        weak_context_rules = (
            "Context is weak/ambiguous. Write a shorter, cautious update and only use explicit source facts. "
            "No assumptions, no invented details, no fake certainty.\n"
        )
    if social_source:
        weak_context_rules += (
            "For social-style vague posts: stay neutral and grounded in available text only; "
            "do not infer unseen story/media details.\n"
        )

    user_content = (
        f"Title: {title}\n"
        f"Summary: {summary}\n"
        f"Source content: {source_context[:1500]}\n"
        f"{source_block}\n"
        "You are a Telegram editor. Rewrite naturally and clearly for Telegram; avoid robotic wording.\n"
        "Use only facts from the source content. Do not invent details.\n"
        "Do not include source attribution, usernames, raw metadata, or links unless explicitly requested in the prompt/output settings.\n"
        "Return plain Telegram-ready text (no JSON, no code blocks). Preserve requested paragraph spacing and formatting."
        f"\n{weak_context_rules}"
        f"\n{emoji_style_note(cfg, 'rss')}"
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

    try:
        logger.info("openai_compat_generate_post sending request to %s", url)
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        txt = data["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.exception(
            "openai_compat_generate_post failed for user %s (%s: %s)",
            user_id,
            exc.__class__.__name__,
            exc,
        )
        raise
    return sanitize_llm_post(txt, cfg, link)

def llm_generate_post(user_id: int, cfg: dict, title: str, summary: str, link: str, source_context: str = "", weak_context: bool = False, social_source: bool = False) -> str:
    logger.info("llm_generate_post provider=%s for user %s", LLM_PROVIDER, user_id)
    if LLM_PROVIDER == "openai_compat":
        return openai_compat_generate_post(user_id, cfg, title, summary, link, source_context, weak_context, social_source)
    return ollama_generate_post(user_id, cfg, title, summary, link, source_context, weak_context, social_source)


def detect_builder_requested_language(requested_language_raw: str) -> str:
    normalized = re.sub(r"\s+", " ", (requested_language_raw or "").strip().lower())
    ru_exact = {"ru", "russian", "рус", "русский", "на русском", "russian language"}
    en_exact = {"en", "english", "англ", "английский", "на английском", "english language"}

    if normalized in ru_exact or normalized.endswith(":ru"):
        return "Russian"
    if normalized in en_exact or normalized.endswith(":en"):
        return "English"

    tokens = set(re.findall(r"[a-zа-яё]+", normalized))
    ru_tokens = {"ru", "russian", "рус", "русский"}
    en_tokens = {"en", "english", "англ", "английский"}
    has_ru = bool(tokens & ru_tokens)
    has_en = bool(tokens & en_tokens)

    if has_ru and not has_en:
        return "Russian"
    if has_en and not has_ru:
        return "English"

    return "English"


def llm_generate_prompt_builder(mode: str, answers: dict[str, str]) -> str:
    requested_language = detect_builder_requested_language(answers.get("q7", ""))

    if mode == "creative":
        user_content = (
            "Create a clean, practical SYSTEM prompt for generating original Telegram posts.\n"
            f"Niche/topic: {answers.get('q1', '')}\n"
            f"Audience: {answers.get('q2', '')}\n"
            f"Tone/voice: {answers.get('q3', '')}\n"
            f"Preferred post types: {answers.get('q4', '')}\n"
            f"Typical length: {answers.get('q5', '')}\n"
            f"Avoid: {answers.get('q6', '')}\n"
            f"Output language: {requested_language}\n\n"
            "The generated prompt must: act as a Telegram content writer/editor; write naturally (not robotic); "
            "prioritize clarity/readability; follow tone, length, audience and language settings; avoid copying source-like phrasing too closely; "
            "avoid fake facts; avoid source mentions/usernames/links unless enabled by output settings; "
            "respect explicit formatting instructions (including empty lines).\n"
            "Keep it flexible and publication-ready, not a rigid one-size-fits-all template.\n"
            "Return only the final prompt text."
        )
    else:
        user_content = (
            "Create a clean, practical SYSTEM prompt for rewriting RSS/news into Telegram posts.\n"
            f"Feed/topic: {answers.get('q1', '')}\n"
            f"Audience: {answers.get('q2', '')}\n"
            f"Tone/voice: {answers.get('q3', '')}\n"
            f"Typical length: {answers.get('q4', '')}\n"
            f"Style preference (neutral vs stronger angle): {answers.get('q5', '')}\n"
            f"Avoid: {answers.get('q6', '')}\n"
            f"Output language: {requested_language}\n\n"
            "The generated prompt must: act as a Telegram content writer/editor; rewrite naturally for Telegram; preserve important facts while avoiding inventions; "
            "follow tone, length, audience and language settings; avoid copying source text too closely; avoid raw metadata/source mentions/usernames/links unless enabled; "
            "respect explicit formatting instructions (including empty lines).\n"
            "Keep it flexible and publication-ready, not a rigid one-size-fits-all template.\n"
            "Return only the final prompt text."
        )

    system_content = (
        "You are an expert prompt engineer for Telegram automation workflows. "
        "Write one strong, usable SYSTEM prompt tailored to the provided settings. "
        "Avoid generic fluff and rigid skeletons; optimize for natural, high-quality Telegram posts."
    )

    if LLM_PROVIDER == "openai_compat":
        url = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.8,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        generated = (data["choices"][0]["message"]["content"] or "").replace("\r", "").strip()
        generated = re.sub(r"(?is)^```[a-z0-9_\-]*\s*", "", generated).strip()
        generated = re.sub(r"(?is)\s*```$", "", generated).strip()
        generated = re.sub(r"\n{3,}", "\n\n", generated)[:2000]
        return f"Output language: {requested_language}.\n{generated}"[:2000]

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": system_content + "\n\n" + user_content,
        "stream": False,
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    generated = (data.get("response", "") or "").replace("\r", "").strip()
    generated = re.sub(r"(?is)^```[a-z0-9_\-]*\s*", "", generated).strip()
    generated = re.sub(r"(?is)\s*```$", "", generated).strip()
    generated = re.sub(r"\n{3,}", "\n\n", generated)[:2000]
    return f"Output language: {requested_language}.\n{generated}"[:2000]


def llm_generate_style_prompt_from_examples(mode: str, examples: list[str], requested_language: str) -> str:
    cleaned = [clean_text(x) for x in examples if clean_text(x)]
    snippets = "\n\n".join([f"Example {i + 1}:\n{txt}" for i, txt in enumerate(cleaned[:3])])
    mode_context = "rewriting RSS/news into Telegram posts" if mode == "rss" else "writing original Telegram posts"
    mode_output = "rewrite source content into the user's style" if mode == "rss" else "write original posts in the user's style"
    user_content = (
        f"Analyze the writing style from these 3 example Telegram posts and create one reusable SYSTEM prompt for {mode_context}.\n"
        "Capture tone, energy, sentence rhythm, structure, hooks/endings, and detail level.\n"
        "The final SYSTEM prompt must include practical control rules:\n"
        "- Write for Telegram and keep formatting clean/publication-ready.\n"
        "- Keep clarity/readability high.\n"
        f"- {mode_output}; rewrite naturally, not mechanically.\n"
        "- Use only provided source facts when source material exists; do not invent facts.\n"
        f"- Always produce the final post in {requested_language}, even if the source language is different.\n"
        "- Avoid source metadata, usernames, and links unless output settings require links.\n"
        "Do not copy or quote the examples directly.\n"
        "Create practical instructions the model can follow in future posts.\n"
        "Preserve clarity and factual accuracy; do not invent facts.\n"
        f"Output language: {requested_language}.\n\n"
        f"{snippets}\n\n"
        "Return only the final prompt text."
    )
    system_content = (
        "You are an expert prompt engineer for Telegram content automation. "
        "Build one concise, practical style prompt based on the user's examples."
    )

    if LLM_PROVIDER == "openai_compat":
        url = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.7,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        generated = (data["choices"][0]["message"]["content"] or "").replace("\r", "").strip()
        generated = re.sub(r"(?is)^```[a-z0-9_\-]*\s*", "", generated).strip()
        generated = re.sub(r"(?is)\s*```$", "", generated).strip()
        generated = re.sub(r"\n{3,}", "\n\n", generated)[:2000]
        return f"Output language: {requested_language}.\n{generated}"[:2000]

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": system_content + "\n\n" + user_content,
        "stream": False,
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    generated = (data.get("response", "") or "").replace("\r", "").strip()
    generated = re.sub(r"(?is)^```[a-z0-9_\-]*\s*", "", generated).strip()
    generated = re.sub(r"(?is)\s*```$", "", generated).strip()
    generated = re.sub(r"\n{3,}", "\n\n", generated)[:2000]
    return f"Output language: {requested_language}.\n{generated}"[:2000]


def prompt_builder_questions(cfg: dict, mode: str) -> list[str]:
    prefix = "prompt_builder_q_creative_" if mode == "creative" else "prompt_builder_q_rss_"
    return [ui_text(cfg, prefix + str(i)) for i in range(1, 8)]


def build_prompt_builder_review(cfg: dict, mode: str) -> InlineKeyboardMarkup:
    return build_prompt_builder_review_menu(ui_pack(cfg), mode)


def build_copy_style_review(cfg: dict, mode: str) -> InlineKeyboardMarkup:
    return build_copy_style_review_menu(ui_pack(cfg), mode)


def clear_prompt_interaction_state(
    context: ContextTypes.DEFAULT_TYPE,
    *,
    clear_manual: bool = True,
    clear_builder: bool = True,
) -> None:
    if clear_manual:
        context.user_data.pop("awaiting_prompt_mode", None)
        context.user_data.pop("awaiting_prompt_channel", None)
    if clear_builder:
        context.user_data.pop("prompt_builder", None)
    context.user_data.pop("copy_style", None)
    context.user_data.pop("copy_style_review", None)


# ===================== Creator mode (text-only) =====================
def creative_variation_level(cfg: dict) -> str:
    level = (cfg.get("creative_variation_level") or "balanced").strip().lower()
    return level if level in CREATIVE_VARIATION_LEVELS else "balanced"


def creative_post_types(cfg: dict) -> list[str]:
    selected = cfg.get("creative_post_types")
    if not isinstance(selected, list):
        return list(CREATIVE_POST_TYPES)
    valid = [p for p in selected if p in CREATIVE_POST_TYPES]
    return valid or list(CREATIVE_POST_TYPES)


def creative_next_post_type(cfg: dict) -> str:
    selected = creative_post_types(cfg)
    if len(selected) == 1:
        return selected[0]
    last_idx = int(cfg.get("creative_last_post_type_idx", -1) or -1)
    next_idx = (last_idx + 1) % len(selected)
    cfg["creative_last_post_type_idx"] = next_idx
    return selected[next_idx]


def creative_content_plan(cfg: dict) -> list[dict]:
    raw = cfg.get("creative_content_plan")
    if not isinstance(raw, list):
        return []
    normalized: list[dict] = []
    for idx, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "id": int(item.get("id") or idx),
                "day_label": str(item.get("day_label") or f"Day {idx}"),
                "topic": str(item.get("topic") or "").strip(),
                "angle": str(item.get("angle") or "").strip(),
                "post_type": str(item.get("post_type") or "").strip() or "opinion",
                "goal": str(item.get("goal") or "").strip() or "engagement",
                "status": str(item.get("status") or "planned").strip().lower() or "planned",
            }
        )
    return normalized


def creative_source_items(cfg: dict, key: str) -> list[str]:
    raw = cfg.get(key)
    if not isinstance(raw, list):
        return []
    normalized: list[str] = []
    for value in raw:
        item = str(value or "").strip()
        if item:
            normalized.append(item)
    return normalized


def creative_source_context_block(cfg: dict, *, for_plan: bool) -> str:
    pillars = creative_source_items(cfg, "creative_topic_pillars")
    ideas = creative_source_items(cfg, "creative_idea_bank")
    links = creative_source_items(cfg, "creative_inspiration_links")
    snippets = creative_source_items(cfg, "creative_source_snippets")
    lines: list[str] = []
    if pillars:
        lines.append("Topic pillars: " + "; ".join(pillars[:8]))
    if ideas:
        lines.append("Idea bank: " + "; ".join(ideas[:8]))
    if links:
        take = 3 if for_plan else 2
        lines.append("Inspiration links (lightly reference themes only): " + "; ".join(links[:take]))
    if snippets:
        take = 4 if for_plan else 2
        lines.append("Source snippets/notes (light supporting context): " + "; ".join(snippets[:take]))
    if not lines:
        return ""
    guidance = (
        "Use this source context as supporting material. Keep the user's creative prompt primary."
        if not for_plan
        else "Use available source context to enrich variety and reduce repetition. Do not force every item into every day."
    )
    return guidance + "\n" + "\n".join(f"- {line}" for line in lines) + "\n"


def creative_current_topic_item(cfg: dict) -> dict | None:
    items = creative_content_plan(cfg)
    for item in items:
        if (item.get("topic") or "").strip():
            return item
    return None


def creative_visual_context(cfg: dict, selected_channel: str) -> dict:
    item = creative_current_topic_item(cfg)
    return {
        "channel": selected_channel or str(cfg.get("channel") or "").strip(),
        "creative_prompt": get_mode_prompt(0, cfg, "creative"),
        "topic": str((item or {}).get("topic") or "").strip(),
        "angle": str((item or {}).get("angle") or "").strip(),
        "post_type": str((item or {}).get("post_type") or "").strip(),
        "goal": str((item or {}).get("goal") or "").strip(),
        "topic_pillars": creative_source_items(cfg, "creative_topic_pillars"),
        "idea_bank": creative_source_items(cfg, "creative_idea_bank"),
        "source_snippets": creative_source_items(cfg, "creative_source_snippets"),
    }


def llm_generate_visual_support(cfg: dict, selected_channel: str, action: str) -> str:
    context_data = creative_visual_context(cfg, selected_channel)
    action_instructions = {
        "idea": "Return a short practical visual concept in 4 bullets: scene/mood, image type, composition idea, emotional tone.",
        "search": "Return one concise web/image search query only. No bullets, no quotes, no explanations.",
        "aiprompt": "Return one polished AI image prompt for social media/influencer style. Visually descriptive and practical.",
    }
    user_content = (
        "Generate visual support for a Telegram creator post.\n"
        f"Channel: {context_data['channel'] or 'N/A'}\n"
        f"Creative prompt: {context_data['creative_prompt']}\n"
        f"Current topic: {context_data['topic'] or 'N/A'}\n"
        f"Angle: {context_data['angle'] or 'N/A'}\n"
        f"Post type: {context_data['post_type'] or 'N/A'}\n"
        f"Goal: {context_data['goal'] or 'N/A'}\n"
        f"Topic pillars: {'; '.join(context_data['topic_pillars'][:6]) or 'N/A'}\n"
        f"Idea bank: {'; '.join(context_data['idea_bank'][:6]) or 'N/A'}\n"
        f"Source snippets: {'; '.join(context_data['source_snippets'][:4]) or 'N/A'}\n"
        "Do not mention scraping/downloading images. The user will search/create visuals manually.\n"
        f"{action_instructions[action]}"
    )

    if LLM_PROVIDER == "openai_compat":
        url = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": "You generate concise visual guidance for creator content."},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.8,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        out = (r.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
    else:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": "You generate concise visual guidance for creator content.\n\n" + user_content,
            "stream": False,
        }
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        r.raise_for_status()
        out = r.json().get("response", "")

    cleaned = clean_text(out).strip()
    cleaned = re.sub(r"(?is)^```[a-z0-9_\\-]*\\s*", "", cleaned).strip()
    cleaned = re.sub(r"(?is)\\s*```$", "", cleaned).strip()
    return cleaned[:1200]


CREATIVE_SOURCE_META = {
    "topic_pillars": {
        "key": "creative_topic_pillars",
        "title_key": "source_topic_pillars_title",
        "empty_key": "source_topic_pillars_empty",
        "add_prompt_key": "source_topic_pillars_add_prompt",
        "saved_key": "source_topic_pillars_saved",
    },
    "idea_bank": {
        "key": "creative_idea_bank",
        "title_key": "source_idea_bank_title",
        "empty_key": "source_idea_bank_empty",
        "add_prompt_key": "source_idea_bank_add_prompt",
        "saved_key": "source_idea_bank_saved",
    },
    "inspiration_links": {
        "key": "creative_inspiration_links",
        "title_key": "source_inspiration_links_title",
        "empty_key": "source_inspiration_links_empty",
        "add_prompt_key": "source_inspiration_links_add_prompt",
        "saved_key": "source_inspiration_links_saved",
    },
    "source_snippets": {
        "key": "creative_source_snippets",
        "title_key": "source_source_snippets_title",
        "empty_key": "source_source_snippets_empty",
        "add_prompt_key": "source_source_snippets_add_prompt",
        "saved_key": "source_source_snippets_saved",
    },
}


def llm_generate_content_plan(
    user_id: int,
    cfg: dict,
    *,
    days: int = 7,
    regenerate_item: dict | None = None,
) -> list[dict]:
    style_prompt = get_mode_prompt(user_id, cfg, "creative")
    profile = (cfg.get("creator_profile") or "").strip()
    variation = creative_variation_level(cfg)
    post_types = ", ".join(creative_post_types(cfg))
    avoid_repetition = bool(cfg.get("creative_avoid_repetition", True))
    channel_name = str(cfg.get("channel") or "").strip()
    base_instruction = (
        "Create a practical Telegram creator content plan.\n"
        f"Days count: {days}.\n"
        f"Channel: {channel_name or 'N/A'}.\n"
        f"Creator profile/context: {profile or 'No profile provided.'}\n"
        f"Variation level: {variation}.\n"
        f"Allowed post types: {post_types}.\n"
        f"Avoid repetition: {'yes' if avoid_repetition else 'no'}.\n"
        "Return ONLY valid JSON array. No markdown.\n"
        "Each item object keys: id, day_label, topic, angle, post_type, goal, status.\n"
        "Set status to planned.\n"
    )
    sources_block = creative_source_context_block(cfg, for_plan=True)
    if sources_block:
        base_instruction += sources_block
    if regenerate_item:
        base_instruction += (
            "Generate exactly one replacement item and keep it fresh compared with this existing item:\n"
            + json.dumps(regenerate_item, ensure_ascii=False)
            + "\nReturn JSON array with one item."
        )

    if LLM_PROVIDER == "openai_compat":
        url = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": style_prompt},
                {"role": "user", "content": base_instruction},
            ],
            "temperature": 0.85,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        txt = (r.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
    else:
        payload = {"model": OLLAMA_MODEL, "prompt": style_prompt + "\n\n" + base_instruction, "stream": False}
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        r.raise_for_status()
        txt = r.json().get("response", "")

    cleaned = txt.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, list):
        raise ValueError("Content plan response is not a list")
    normalized = creative_content_plan({"creative_content_plan": parsed})
    return normalized[:days] if not regenerate_item else normalized[:1]


def llm_generate_campaign_arc(cfg: dict, campaign: dict) -> list[dict]:
    intake = cfg.get("creative_channel_intake") if isinstance(cfg.get("creative_channel_intake"), dict) else {}
    days = int(campaign.get("duration_days") or 7)
    base_prompt = (
        "Create a practical creator campaign arc.\n"
        f"Days: {days}.\n"
        f"Goal: {campaign.get('goal') or 'N/A'}.\n"
        f"Offer/product: {campaign.get('offer') or 'N/A'}.\n"
        f"Target action: {campaign.get('target_action') or 'N/A'}.\n"
        f"Audience awareness/situation: {campaign.get('awareness') or 'N/A'}.\n"
        f"Key objections: {campaign.get('objections') or 'N/A'}.\n"
        f"Key benefits: {campaign.get('benefits') or 'N/A'}.\n"
        f"Urgency/event context: {campaign.get('urgency_context') or 'N/A'}.\n"
        "Return ONLY JSON array with one item per day.\n"
        "Each item keys: day, stage, direction, hook, proof, cta.\n"
        "Stages should naturally move: warm -> educate -> desire -> objections -> proof -> conversion.\n"
    )
    if intake:
        base_prompt += (
            "Channel context:\n"
            f"- Topic: {intake.get('channel_about') or 'N/A'}\n"
            f"- Audience: {intake.get('audience') or 'N/A'}\n"
            f"- Tone: {intake.get('tone_style') or 'N/A'}\n"
        )

    if LLM_PROVIDER == "openai_compat":
        url = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": OPENAI_MODEL,
            "messages": [{"role": "system", "content": "You build strategic creator campaigns."}, {"role": "user", "content": base_prompt}],
            "temperature": 0.75,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        txt = (r.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
    else:
        payload = {"model": OLLAMA_MODEL, "prompt": "You build strategic creator campaigns.\n\n" + base_prompt, "stream": False}
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        r.raise_for_status()
        txt = r.json().get("response", "")
    cleaned = txt.strip().strip("`")
    cleaned = cleaned.replace("json", "", 1).strip() if cleaned.lower().startswith("json") else cleaned
    parsed = json.loads(cleaned)
    if not isinstance(parsed, list):
        raise ValueError("campaign arc response is not a list")
    return [item for item in parsed if isinstance(item, dict)][:days]


def creator_make_post(user_id: int, cfg: dict) -> str:
    style_prompt = get_mode_prompt(user_id, cfg, "creative")
    profile = (cfg.get("creator_profile") or "").strip()

    if not profile:
        # minimal fallback
        profile = "Эксперт/блогер. Пишет полезные короткие посты для своей аудитории."

    variation = creative_variation_level(cfg)
    post_type = creative_next_post_type(cfg)
    avoid_repetition = bool(cfg.get("creative_avoid_repetition", True))

    variation_guidance = {
        "low": "Variation level: low. Keep style stable and structure mostly consistent for brand continuity.",
        "balanced": "Variation level: balanced. Add moderate variety in hook and angle while keeping output predictable.",
        "high": "Variation level: high. Use broader variation in hook, structure, and angle while staying Telegram-appropriate and on-brand.",
    }

    prompt = (
        "Write one Telegram-ready post following the system prompt. Return plain text only (no JSON, no code blocks).\n\n"
        f"Creator profile:\n{profile}\n\n"
        f"Post type for this generation: {post_type}.\n"
        f"{variation_guidance[variation]}\n"
        f"{emoji_style_note(cfg, 'creative')}"
    )
    intake = cfg.get("creative_channel_intake") if isinstance(cfg.get("creative_channel_intake"), dict) else {}
    if intake:
        prompt += (
            "\nUse this channel context as primary strategy:\n"
            f"- Channel about: {str(intake.get('channel_about') or 'N/A')}\n"
            f"- Audience: {str(intake.get('audience') or 'N/A')}\n"
            f"- Audience wants: {str(intake.get('audience_wants') or 'N/A')}\n"
            f"- Pains: {str(intake.get('audience_pains') or 'N/A')}\n"
            f"- Tone/style: {str(intake.get('tone_style') or 'N/A')}\n"
            f"- Offer/services: {str(intake.get('offers') or 'N/A')}\n"
            f"- Creator goals: {str(intake.get('creator_goals') or 'N/A')}\n"
            f"- Good examples: {str(intake.get('good_posts') or 'N/A')}\n"
            f"- Avoid examples: {str(intake.get('bad_posts') or 'N/A')}\n"
            f"- Never sound like: {str(intake.get('never_sound_like') or 'N/A')}\n"
        )
    active_campaign_id = cfg.get("creative_active_campaign_id")
    for campaign in creative_campaigns(cfg):
        if campaign.get("id") == active_campaign_id:
            prompt += (
                "\nActive campaign context (prioritize this):\n"
                f"- Goal: {campaign.get('goal') or 'N/A'}\n"
                f"- Offer: {campaign.get('offer') or 'N/A'}\n"
                f"- Target action: {campaign.get('target_action') or 'N/A'}\n"
                f"- Awareness level/situation: {campaign.get('awareness') or 'N/A'}\n"
                f"- Key objections: {campaign.get('objections') or 'N/A'}\n"
                f"- Key benefits: {campaign.get('benefits') or 'N/A'}\n"
                f"- Urgency/event context: {campaign.get('urgency_context') or 'N/A'}\n"
            )
            arc = campaign.get("arc") or []
            if arc:
                first = arc[0]
                if isinstance(first, dict):
                    prompt += (
                        "Use the current campaign arc direction as guidance:\n"
                        f"- Stage: {first.get('stage') or 'N/A'}\n"
                        f"- Direction: {first.get('direction') or 'N/A'}\n"
                        f"- CTA focus: {first.get('cta') or 'N/A'}\n"
                    )
            break
    sources_block = creative_source_context_block(cfg, for_plan=False)
    if sources_block:
        prompt += "\n" + sources_block

    if avoid_repetition:
        prompt += "Avoid repeating the same hook, structure, CTA, and sentence rhythm too often. Keep it light and natural.\n"

    temperature = 0.75 if variation == "low" else 0.85 if variation == "balanced" else 0.95

    if LLM_PROVIDER == "openai_compat":
        url = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": style_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        txt = data["choices"][0]["message"]["content"]
        return clean_text(txt)[:900]

    # ollama creator
    payload = {"model": OLLAMA_MODEL, "prompt": style_prompt + "\n\n" + prompt, "stream": False}
    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return clean_text(data.get("response", ""))[:900]

def ui_text(cfg: dict | None, key: str) -> str:
    lang = ((cfg or {}).get("language") or "en").lower()
    if lang not in UI_TEXTS:
        lang = "en"
    return UI_TEXTS[lang].get(key, UI_TEXTS["en"].get(key, key))


def ui_pack(cfg: dict) -> dict:
    lang = (cfg.get("language") or "en").lower()
    return UI_TEXTS.get(lang, UI_TEXTS["en"])


def build_main_menu_clean(cfg: dict) -> InlineKeyboardMarkup:
    return build_main_menu_minimal(ui_pack(cfg))


def build_help_text(cfg: dict) -> str:
    return (
        f"{ui_text(cfg, 'help_open_link')}\n"
        f"{ui_text(cfg, 'help_link')}\n\n"
        f"{ui_text(cfg, 'help_contact')}"
    )


def build_setup_menu(cfg: dict) -> InlineKeyboardMarkup:
    current_mode = (cfg.get("mode") or "rss").strip().lower()
    autopost_on = mode_autopost_enabled(cfg, "creative" if current_mode == "creator" else "rss")
    return build_setup_submenu(ui_pack(cfg), autopost_on)


def build_channel_menu(cfg: dict) -> InlineKeyboardMarkup:
    return build_channel_management_menu(ui_pack(cfg))


def build_modes_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_modes_menu(ui_pack(cfg))


def build_creative_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_creative_menu(ui_pack(cfg))


def build_creative_publish_settings_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_creative_publish_settings_menu(ui_pack(cfg))


def build_creative_intake_submenu(cfg: dict, show_resume: bool = False) -> InlineKeyboardMarkup:
    return build_creative_intake_menu(ui_pack(cfg), show_resume)


def build_creative_campaigns_submenu(cfg: dict, show_resume: bool = False) -> InlineKeyboardMarkup:
    return build_creative_campaigns_menu(ui_pack(cfg), show_resume)


def build_creative_advanced_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_creative_advanced_menu(ui_pack(cfg))


def build_creative_variety_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_creative_variety_menu(
        ui_pack(cfg),
        creative_variation_level(cfg),
        bool(cfg.get("creative_avoid_repetition", True)),
    )


def build_creative_variation_level_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_creative_variation_level_menu(ui_pack(cfg), creative_variation_level(cfg))


def build_creative_post_types_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_creative_post_types_menu(ui_pack(cfg), creative_post_types(cfg))


def build_rss_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_rss_ai_menu(ui_pack(cfg), rss_posting_paused(cfg))


def build_style_setup_submenu(cfg: dict, mode: str) -> InlineKeyboardMarkup:
    back_callback = "ui:mode:creative:menu" if mode == "creative" else "ui:mode:rss:menu"
    return build_style_setup_menu(ui_pack(cfg), mode, back_callback)


def build_rss_output_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_rss_output_menu(
        ui_pack(cfg),
        bool(cfg.get("include_rss_source_link", True)),
        bool(cfg.get("use_rss_feed_image", True)),
        bool(cfg.get("rss_cta_enabled", False)),
        bool(cfg.get("rss_bold_title", False)),
    )


def build_creative_output_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_creative_output_menu(ui_pack(cfg), bool(cfg.get("creative_bold_title", False)))


def build_creative_content_plan_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_creative_content_plan_menu(ui_pack(cfg))


def build_creative_content_plan_item_picker(cfg: dict, action: str) -> InlineKeyboardMarkup:
    return build_creative_content_plan_item_picker_menu(ui_pack(cfg), creative_content_plan(cfg), action)


def build_creative_source_center_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_creative_source_center_menu(ui_pack(cfg))


def build_creative_source_list_submenu(cfg: dict, source_type: str) -> InlineKeyboardMarkup:
    return build_creative_source_list_menu(ui_pack(cfg), source_type)


def build_creative_source_delete_submenu(cfg: dict, source_type: str, items: list[str]) -> InlineKeyboardMarkup:
    return build_creative_source_delete_menu(ui_pack(cfg), source_type, items)


def build_creative_visual_support_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_creative_visual_support_menu(ui_pack(cfg))


def creative_source_list_text(cfg: dict, source_type: str, selected_channel: str) -> str:
    meta = CREATIVE_SOURCE_META[source_type]
    items = creative_source_items(cfg, meta["key"])
    lines = [ui_text(cfg, meta["title_key"]), "", selected_channel_text(cfg, selected_channel), ""]
    if source_type == "idea_bank":
        lines.extend([ui_text(cfg, "source_idea_bank_intro"), ""])
    if not items:
        lines.append(ui_text(cfg, meta["empty_key"]))
        return "\n".join(lines)
    for idx, item in enumerate(items, start=1):
        lines.append(f"{idx}) {item}")
    return "\n".join(lines)


def creative_visual_support_menu_text(cfg: dict, selected_channel: str) -> str:
    return (
        ui_text(cfg, "creative_visual_support_title")
        + "\n\n"
        + selected_channel_text(cfg, selected_channel)
        + "\n\n"
        + ui_text(cfg, "creative_visual_support_intro")
    )


def creative_content_plan_menu_text(cfg: dict, selected_channel: str) -> str:
    return (
        ui_text(cfg, "content_plan_title")
        + "\n\n"
        + selected_channel_text(cfg, selected_channel)
        + "\n\n"
        + ui_text(cfg, "content_plan_intro")
    )


def creative_channel_intake_questions(cfg: dict) -> list[tuple[str, str]]:
    return [
        ("channel_about", ui_text(cfg, "channel_intake_q_channel_about")),
        ("audience", ui_text(cfg, "channel_intake_q_audience")),
        ("audience_wants", ui_text(cfg, "channel_intake_q_audience_wants")),
        ("audience_pains", ui_text(cfg, "channel_intake_q_audience_pains")),
        ("tone_style", ui_text(cfg, "channel_intake_q_tone_style")),
        ("offers", ui_text(cfg, "channel_intake_q_offers")),
        ("creator_goals", ui_text(cfg, "channel_intake_q_creator_goals")),
        ("good_posts", ui_text(cfg, "channel_intake_q_good_posts")),
        ("bad_posts", ui_text(cfg, "channel_intake_q_bad_posts")),
        ("never_sound_like", ui_text(cfg, "channel_intake_q_never_sound_like")),
    ]


def creative_campaign_questions(cfg: dict) -> list[tuple[str, str]]:
    return [
        ("goal", ui_text(cfg, "campaign_q_goal")),
        ("offer", ui_text(cfg, "campaign_q_offer")),
        ("duration_days", ui_text(cfg, "campaign_q_duration")),
        ("target_action", ui_text(cfg, "campaign_q_target_action")),
        ("awareness", ui_text(cfg, "campaign_q_awareness")),
        ("objections", ui_text(cfg, "campaign_q_objections")),
        ("benefits", ui_text(cfg, "campaign_q_benefits")),
        ("urgency_context", ui_text(cfg, "campaign_q_urgency")),
    ]


def creative_fast_start_questions(cfg: dict) -> list[tuple[str, str]]:
    return [
        ("channel_about", ui_text(cfg, "quickstart_q_channel_about")),
        ("audience", ui_text(cfg, "quickstart_q_audience")),
        ("offers", ui_text(cfg, "quickstart_q_offer")),
        ("creator_goals", ui_text(cfg, "quickstart_q_goal")),
    ]


def creative_campaign_arc_readable_text(cfg: dict, campaign: dict) -> str:
    arc = campaign.get("arc") if isinstance(campaign.get("arc"), list) else []
    if not arc:
        return ui_text(cfg, "campaign_arc_empty")
    lines = [ui_text(cfg, "campaign_arc_title")]
    for idx, item in enumerate(arc, start=1):
        if not isinstance(item, dict):
            continue
        day_label = item.get("day") or idx
        stage = str(item.get("stage") or ui_text(cfg, "campaign_arc_default_stage")).strip()
        direction = str(item.get("direction") or ui_text(cfg, "campaign_arc_default_direction")).strip()
        hook = str(item.get("hook") or ui_text(cfg, "campaign_arc_default_hook")).strip()
        cta = str(item.get("cta") or "").strip()
        lines.append(
            ui_text(cfg, "campaign_arc_day_block").format(
                day=day_label,
                stage=stage[:140],
                direction=direction[:220],
                hook=hook[:180],
                cta=(cta[:160] if cta else ui_text(cfg, "campaign_arc_cta_optional")),
            )
        )
    return "\n\n".join(lines)


def creative_intake_summary_text(cfg: dict, selected_channel: str) -> str:
    data = cfg.get("creative_channel_intake") if isinstance(cfg.get("creative_channel_intake"), dict) else {}
    lines = [ui_text(cfg, "channel_intake_title"), "", selected_channel_text(cfg, selected_channel), ""]
    if not data:
        lines.append(ui_text(cfg, "channel_intake_empty"))
        return "\n".join(lines)
    label_keys = {
        "channel_about": "channel_intake_label_channel_about",
        "audience": "channel_intake_label_audience",
        "audience_wants": "channel_intake_label_audience_wants",
        "audience_pains": "channel_intake_label_audience_pains",
        "tone_style": "channel_intake_label_tone_style",
        "offers": "channel_intake_label_offers",
        "creator_goals": "channel_intake_label_creator_goals",
        "good_posts": "channel_intake_label_good_posts",
        "bad_posts": "channel_intake_label_bad_posts",
        "never_sound_like": "channel_intake_label_never_sound_like",
    }
    for key, label_key in label_keys.items():
        val = str(data.get(key) or "").strip()
        if val:
            lines.append(f"• {ui_text(cfg, label_key)}: {val[:280]}")
    active_campaign_id = cfg.get("creative_active_campaign_id")
    campaigns = cfg.get("creative_campaigns") if isinstance(cfg.get("creative_campaigns"), list) else []
    active = None
    for item in campaigns:
        if isinstance(item, dict) and item.get("id") == active_campaign_id:
            active = item
            break
    if active:
        lines.extend(["", ui_text(cfg, "campaign_active_label").format(name=str(active.get("goal") or "Campaign"))])
    return "\n".join(lines)


def _looks_vague_context_text(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return True
    lowered = text.lower()
    generic_markers = {
        "everyone",
        "all",
        "anyone",
        "people",
        "business",
        "general",
        "все",
        "для всех",
        "люди",
        "любой",
        "бизнес",
        "общее",
    }
    if lowered in generic_markers:
        return True
    words = [w for w in re.split(r"[^a-zA-Zа-яА-Я0-9]+", text) if w]
    return len(words) < 4


def creative_preview_diagnostics_text(cfg: dict) -> str:
    intake = cfg.get("creative_channel_intake") if isinstance(cfg.get("creative_channel_intake"), dict) else {}
    if not intake:
        return ""
    hints: list[str] = []
    if _looks_vague_context_text(str(intake.get("audience") or "")):
        hints.append(ui_text(cfg, "preview_diag_audience"))
    if _looks_vague_context_text(str(intake.get("offers") or "")):
        hints.append(ui_text(cfg, "preview_diag_offer"))
    if _looks_vague_context_text(str(intake.get("audience_pains") or "")):
        hints.append(ui_text(cfg, "preview_diag_objections"))
    if _looks_vague_context_text(str(intake.get("good_posts") or "")):
        hints.append(ui_text(cfg, "preview_diag_examples"))
    if len(hints) < 2:
        return ""
    return ui_text(cfg, "preview_diag_intro") + "\n• " + "\n• ".join(hints[:2])


def creative_campaigns(cfg: dict) -> list[dict]:
    raw = cfg.get("creative_campaigns")
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for idx, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "id": int(item.get("id") or idx),
                "goal": str(item.get("goal") or "").strip(),
                "offer": str(item.get("offer") or "").strip(),
                "duration_days": int(item.get("duration_days") or 0) or 7,
                "target_action": str(item.get("target_action") or "").strip(),
                "awareness": str(item.get("awareness") or "").strip(),
                "objections": str(item.get("objections") or "").strip(),
                "benefits": str(item.get("benefits") or "").strip(),
                "urgency_context": str(item.get("urgency_context") or "").strip(),
                "arc": item.get("arc") if isinstance(item.get("arc"), list) else [],
            }
        )
    return out


def creative_content_plan_view_text(cfg: dict, selected_channel: str) -> str:
    items = creative_content_plan(cfg)
    if not items:
        return (
            ui_text(cfg, "content_plan_title")
            + "\n\n"
            + selected_channel_text(cfg, selected_channel)
            + "\n\n"
            + ui_text(cfg, "content_plan_empty")
        )
    lines = [ui_text(cfg, "content_plan_current_title"), selected_channel_text(cfg, selected_channel), ""]
    for idx, item in enumerate(items, start=1):
        lines.append(
            ui_text(cfg, "content_plan_item_line").format(
                idx=idx,
                day_label=item.get("day_label") or f"Day {idx}",
                topic=item.get("topic") or "—",
                angle=item.get("angle") or "—",
                post_type=item.get("post_type") or "—",
                goal=item.get("goal") or "—",
                status=item.get("status") or "planned",
            )
        )
    return "\n\n".join(lines)


def build_emoji_management_submenu(cfg: dict, mode: str) -> InlineKeyboardMarkup:
    return build_emoji_management_menu(ui_pack(cfg), mode)


def build_asset_management_submenu(cfg: dict, mode: str, asset_type: str) -> InlineKeyboardMarkup:
    has_asset = bool(cfg.get(f"{mode}_{asset_type}_file_id"))
    return build_asset_management_menu(ui_pack(cfg), mode, asset_type, has_asset)


def post_format_assets_text(cfg: dict, mode: str) -> str:
    template_key = f"{mode}_template_file_id"
    watermark_key = f"{mode}_watermark_file_id"
    template_status = ui_text(cfg, "status_added") if cfg.get(template_key) else ui_text(cfg, "status_not_added")
    watermark_status = ui_text(cfg, "status_added") if cfg.get(watermark_key) else ui_text(cfg, "status_not_added")
    bold_status = ui_text(cfg, "label_on") if bool(cfg.get(f"{mode}_bold_title", False)) else ui_text(cfg, "label_off")
    emoji_status = ui_text(cfg, "status_added") if (cfg.get(f"{mode}_custom_emojis_text") or "").strip() else ui_text(cfg, "status_not_added")
    return ui_text(cfg, "post_format_assets_info").format(
        template=template_status,
        watermark=watermark_status,
        bold_title=bold_status,
        emoji=emoji_status,
    )


def output_settings_text(cfg: dict, mode: str) -> str:
    if mode == "rss":
        return ui_text(cfg, "rss_output_settings_title") + "\n\n" + post_format_assets_text(cfg, mode)
    return ui_text(cfg, "creative_output_settings_title") + "\n\n" + post_format_assets_text(cfg, mode)


def emoji_management_text(cfg: dict, mode: str) -> str:
    has_emoji = bool((cfg.get(f"{mode}_custom_emojis_text") or "").strip())
    has_link = bool((cfg.get(f"{mode}_custom_emojis_link") or "").strip())
    return (
        ui_text(cfg, "emoji_management_title")
        + "\n\n"
        + ui_text(cfg, "emoji_management_status").format(
            emoji=ui_text(cfg, "status_yes") if has_emoji else ui_text(cfg, "status_no"),
            link=ui_text(cfg, "status_yes") if has_link else ui_text(cfg, "status_no"),
        )
        + "\n\n"
        + ui_text(cfg, "emoji_prompt_send")
    )


def _extract_channel_from_forward(msg) -> tuple[str | None, dict]:
    origin = getattr(msg, "forward_origin", None)
    if origin and getattr(origin, "type", "") == "channel":
        chat = getattr(origin, "chat", None)
        if chat and getattr(chat, "id", None):
            username_raw = (getattr(chat, "username", None) or "").strip().lstrip("@")
            username = f"@{username_raw}" if username_raw else ""
            channel_key = username or str(chat.id)
            title = (getattr(chat, "title", None) or "").strip()
            return channel_key, {"username": username, "title": title}

    sender_chat = getattr(msg, "sender_chat", None)
    if sender_chat and getattr(sender_chat, "id", None):
        username_raw = (getattr(sender_chat, "username", None) or "").strip().lstrip("@")
        username = f"@{username_raw}" if username_raw else ""
        channel_key = username or str(sender_chat.id)
        title = (getattr(sender_chat, "title", None) or "").strip()
        return channel_key, {"username": username, "title": title}
    return None, {}


def _looks_like_link(value: str) -> bool:
    raw = value.strip().lower()
    return raw.startswith("http://") or raw.startswith("https://") or raw.startswith("t.me/")


def asset_management_text(cfg: dict, mode: str, asset_type: str) -> str:
    title_key = "asset_manage_watermark_title" if asset_type == "watermark" else "asset_manage_template_title"
    help_key = "asset_manage_watermark_help" if asset_type == "watermark" else "asset_manage_template_help"
    status_key = f"{mode}_{asset_type}_file_id"
    status_value = ui_text(cfg, "status_added") if cfg.get(status_key) else ui_text(cfg, "status_not_added")
    return (
        ui_text(cfg, title_key)
        + "\n\n"
        + ui_text(cfg, help_key)
        + "\n"
        + ui_text(cfg, "asset_manage_status").format(status=status_value)
    )


def asset_paths(user_id: int, mode: str, asset_type: str, ext: str) -> tuple[Path, str]:
    safe_ext = ext if ext in ("jpg", "jpeg", "png", "webp") else "jpg"
    rel = Path("client_assets") / str(user_id) / f"{mode}_{asset_type}.{safe_ext}"
    return BASE_DIR / rel, rel.as_posix()


def clear_asset_file(path_value: str) -> None:
    if not path_value:
        return
    try:
        path = BASE_DIR / path_value
        if path.exists() and path.is_file():
            path.unlink()
    except Exception:
        pass


def build_feed_menu(cfg: dict) -> InlineKeyboardMarkup:
    return build_feed_management_menu(ui_pack(cfg))


def build_lang_menu() -> InlineKeyboardMarkup:
    return build_lang_keyboard()


def build_scheduling_submenu(cfg: dict) -> InlineKeyboardMarkup:
    return build_scheduling_menu(ui_pack(cfg))


def mode_schedule_state(cfg: dict, mode: str) -> tuple[bool, list[str], str, str]:
    mode_times_key = "creative_schedule_times" if mode == "creative" else "rss_schedule_times"
    mode_times_raw = cfg.get(mode_times_key)
    mode_has_own_times = False
    if isinstance(mode_times_raw, list):
        mode_has_own_times = any(str(x).strip() for x in mode_times_raw)

    if mode == "creative":
        enabled = bool(cfg.get("creative_schedule_enabled"))
        times = cfg.get("creative_schedule_times", []) or []
        last_date = cfg.get("creative_last_schedule_date")
        last_time = cfg.get("creative_last_schedule_time")
    else:
        enabled = bool(cfg.get("rss_schedule_enabled"))
        times = cfg.get("rss_schedule_times", []) or []
        last_date = cfg.get("rss_last_schedule_date")
        last_time = cfg.get("rss_last_schedule_time")

    channels = cfg.get("channels") if isinstance(cfg.get("channels"), list) else []
    use_legacy_global_schedule = len(channels) <= 1
    if use_legacy_global_schedule and not mode_has_own_times and not times and cfg.get("schedule_times"):
        enabled = bool(cfg.get("schedule_enabled"))
        times = cfg.get("schedule_times", []) or []
        last_date = cfg.get("last_schedule_date")
        last_time = cfg.get("last_schedule_time")
    return enabled, times, last_date, last_time


def mode_activation_state(cfg: dict, mode: str) -> bool:
    return mode_autopost_enabled(cfg, mode)


def _quiet_window_duration_minutes(start: str, end: str) -> int:
    start_hm = _parse_hhmm(start)
    end_hm = _parse_hhmm(end)
    if not start_hm or not end_hm:
        return 0
    start_total = start_hm[0] * 60 + start_hm[1]
    end_total = end_hm[0] * 60 + end_hm[1]
    if start_total == end_total:
        return 0
    if end_total > start_total:
        return end_total - start_total
    return (24 * 60 - start_total) + end_total


def blocked_minutes_per_day(cfg: dict, mode: str) -> int:
    total = sum(_quiet_window_duration_minutes(start, end) for start, end in quiet_windows_for_mode(cfg, mode))
    return min(24 * 60, max(0, total))


def activation_readiness_issues(cfg: dict, mode: str) -> list[str]:
    effective_mode = "rss" if mode == "both" else mode
    issues: list[str] = []
    if not cfg.get("channel"):
        issues.append(ui_text(cfg, "activation_issue_channel"))
    if mode in {"rss", "both"} and not cfg.get("feeds"):
        issues.append(ui_text(cfg, "activation_issue_feeds"))
    if not channel_timezone_is_set(cfg):
        issues.append(ui_text(cfg, "activation_issue_timezone"))

    mode_flag_key = f"{effective_mode}_use_interval"
    _, times, _, _ = mode_schedule_state(cfg, effective_mode)
    has_mode_flag = mode_flag_key in cfg
    has_slots = bool(times)
    if not has_mode_flag and not has_slots:
        issues.append(ui_text(cfg, "activation_issue_posting_mode"))
    use_interval = mode_uses_interval(cfg, effective_mode)
    if not use_interval and not has_slots:
        issues.append(ui_text(cfg, "activation_issue_slots"))
    return issues


def activation_risk_warnings(cfg: dict, mode: str) -> list[str]:
    effective_mode = "rss" if mode == "both" else mode
    warnings: list[str] = []
    blocked_min = blocked_minutes_per_day(cfg, effective_mode)
    if blocked_min >= 16 * 60:
        warnings.append(ui_text(cfg, "activation_warn_blocked_hours").format(hours=round(blocked_min / 60, 1)))

    freshness = rss_freshness_minutes(cfg)
    if mode in {"rss", "both"} and freshness <= 60:
        warnings.append(ui_text(cfg, "activation_warn_freshness").format(minutes=freshness))

    use_interval = mode_uses_interval(cfg, effective_mode)
    interval_min = max(1, int(cfg.get("interval_minutes", 30) or 30))
    if use_interval and interval_min >= 360:
        warnings.append(ui_text(cfg, "activation_warn_interval").format(interval=interval_min))

    if not use_interval:
        _, times, _, _ = mode_schedule_state(cfg, effective_mode)
        if len(times) <= 1:
            warnings.append(ui_text(cfg, "activation_warn_slots_count"))
        parsed_slots = sorted([_parse_hhmm(t) for t in times if _parse_hhmm(t)])
        if len(parsed_slots) >= 2:
            max_gap = 0
            expanded = [h * 60 + m for h, m in parsed_slots]
            for i in range(len(expanded)):
                a = expanded[i]
                b = expanded[(i + 1) % len(expanded)]
                gap = (b - a) if i + 1 < len(expanded) else (24 * 60 - a + b)
                max_gap = max(max_gap, gap)
            if max_gap >= 10 * 60:
                warnings.append(ui_text(cfg, "activation_warn_slots_gap").format(hours=round(max_gap / 60, 1)))

    available_min = max(0, 24 * 60 - blocked_min)
    if use_interval:
        est_posts = available_min // interval_min
        if est_posts <= 1:
            warnings.append(ui_text(cfg, "activation_warn_low_volume_interval").format(count=int(est_posts)))
    return warnings


def _next_scheduled_run(cfg: dict, mode: str, now: datetime) -> datetime | None:
    _, times, _, _ = mode_schedule_state(cfg, mode)
    parsed_times: list[tuple[int, int]] = []
    for slot in times:
        hm = _parse_hhmm(slot)
        if hm:
            parsed_times.append(hm)
    if not parsed_times:
        return None
    for day_offset in range(0, 8):
        base = (now + timedelta(days=day_offset)).replace(second=0, microsecond=0)
        for hh, mm in sorted(parsed_times):
            candidate = base.replace(hour=hh, minute=mm)
            if candidate < now:
                continue
            shifted = _apply_quiet_hours(cfg, mode, candidate)
            if shifted >= now:
                return shifted
    return None


def mode_next_run_text(cfg: dict, mode: str, now: datetime | None = None) -> str:
    reference_now = now or user_now(cfg)
    if mode_uses_interval(cfg, mode):
        next_run = _parse_local_iso_datetime(cfg.get(_interval_next_run_key(mode)) or "")
        if not next_run:
            next_run = _schedule_next_interval_run(cfg, mode, reference_now)
        return next_run.strftime("%Y-%m-%d %H:%M")
    next_run = _next_scheduled_run(cfg, mode, reference_now)
    if not next_run:
        return ui_text(cfg, "schedule_not_set")
    return next_run.strftime("%Y-%m-%d %H:%M")


def activate_posting(cfg: dict, mode: str, *, turn_on: bool) -> tuple[bool, str]:
    if turn_on:
        issues = activation_readiness_issues(cfg, mode)
        if issues:
            text = ui_text(cfg, "activation_blocked_intro") + "\n" + "\n".join(f"- {item}" for item in issues)
            return False, text
        set_mode_autopost_enabled(cfg, mode, True)
        if mode in {"rss", "creative"}:
            cfg[f"{mode}_schedule_enabled"] = True
            if mode_uses_interval(cfg, mode):
                _schedule_next_interval_run(cfg, mode, user_now(cfg))
        else:
            cfg["rss_schedule_enabled"] = True
            cfg["creative_schedule_enabled"] = True
            for _m in ("rss", "creative"):
                if mode_uses_interval(cfg, _m):
                    _schedule_next_interval_run(cfg, _m, user_now(cfg))
        warnings = activation_risk_warnings(cfg, mode)
        warning_text = ""
        if warnings:
            warning_text = ui_text(cfg, "activation_warning_intro") + "\n" + "\n".join(f"- {item}" for item in warnings) + "\n\n"
        return True, warning_text + live_confirmation_text(cfg, mode)

    set_mode_autopost_enabled(cfg, mode, False)
    if mode in {"rss", "creative"}:
        cfg[f"{mode}_schedule_enabled"] = False
    else:
        cfg["rss_schedule_enabled"] = False
        cfg["creative_schedule_enabled"] = False
    return True, ui_text(cfg, "activation_off_confirmed")


def live_confirmation_text(cfg: dict, mode: str) -> str:
    effective_mode = "rss" if mode == "both" else mode
    mode_label = ui_text(cfg, "posting_mode_interval") if mode_uses_interval(cfg, effective_mode) else ui_text(cfg, "posting_mode_scheduled")
    _, times, _, _ = mode_schedule_state(cfg, effective_mode)
    schedule_info = ui_text(cfg, "schedule_empty_slots")
    if mode_uses_interval(cfg, effective_mode):
        schedule_info = ui_text(cfg, "live_line_interval").format(interval=int(cfg.get("interval_minutes", 30) or 30))
    elif times:
        schedule_info = ", ".join(times)
    blocked = quiet_windows_for_mode(cfg, effective_mode)
    blocked_text = ", ".join(f"{start}–{end}" for start, end in blocked) if blocked else ui_text(cfg, "schedule_blocked_hours_off")
    channel = channel_display_name(cfg, cfg.get("channel") or "—")
    return (
        ui_text(cfg, "live_title")
        + "\n\n"
        + ui_text(cfg, "live_line_channel").format(channel=channel)
        + "\n"
        + ui_text(cfg, "live_line_mode").format(mode=mode_label)
        + "\n"
        + ui_text(cfg, "live_line_schedule").format(schedule=schedule_info)
        + "\n"
        + ui_text(cfg, "live_line_timezone").format(timezone=user_timezone_label(cfg))
        + "\n"
        + ui_text(cfg, "live_line_freshness").format(minutes=rss_freshness_minutes(cfg))
        + "\n"
        + ui_text(cfg, "live_line_blocked").format(blocked=blocked_text)
        + "\n\n"
        + ui_text(cfg, "live_line_next_check").format(next_run=mode_next_run_text(cfg, effective_mode))
        + "\n"
        + ui_text(cfg, "live_line_next_post_hint")
    )


def schedule_summary_for_mode(cfg: dict, mode: str) -> str:
    _, times, _, _ = mode_schedule_state(cfg, mode)
    posting_status = "ON" if mode_autopost_enabled(cfg, mode) else "OFF"
    posting_mode = ui_text(cfg, "posting_mode_interval") if mode_uses_interval(cfg, mode) else ui_text(cfg, "posting_mode_scheduled")
    if mode_uses_interval(cfg, mode):
        times_text = ui_text(cfg, "live_line_interval").format(interval=int(cfg.get("interval_minutes", 30) or 30))
    else:
        times_text = ", ".join(times) if times else ui_text(cfg, "schedule_empty_slots")
    quiet_windows = quiet_windows_for_mode(cfg, mode)
    quiet_text = ", ".join([f"{start}–{end}" for start, end in quiet_windows]) if quiet_windows else ui_text(cfg, "schedule_blocked_hours_off")
    next_text = mode_next_run_text(cfg, mode)
    return (
        ui_text(cfg, "schedule_summary_title")
        + "\n"
        + ui_text(cfg, "schedule_summary_channel").format(channel=channel_display_name(cfg, cfg.get("channel") or "—"))
        + "\n"
        + ui_text(cfg, "schedule_summary_mode").format(mode=posting_mode)
        + "\n"
        + ui_text(cfg, "schedule_summary_slots").format(slots=times_text)
        + "\n"
        + ui_text(cfg, "schedule_summary_timezone").format(timezone=user_timezone_label(cfg))
        + "\n"
        + ui_text(cfg, "schedule_summary_blocked").format(blocked=quiet_text)
        + "\n"
        + ui_text(cfg, "schedule_summary_freshness").format(minutes=rss_freshness_minutes(cfg))
        + "\n"
        + ui_text(cfg, "schedule_summary_status").format(status=posting_status)
        + "\n"
        + ui_text(cfg, "schedule_summary_next_run").format(next_run=next_text)
    )


def creative_quota_summary_text(cfg: dict) -> str:
    cfg = ensure_creative_monthly_counter(cfg)
    monthly_pool = creative_monthly_limit(cfg)
    used = int(cfg.get("creative_monthly_count", 0) or 0)
    remaining = max(monthly_pool - used, 0)
    period = cfg.get("creative_monthly_period") or _current_month_key()
    return (
        ui_text(cfg, "creative_quota_title")
        + "\n"
        + ui_text(cfg, "creative_quota_pool").format(pool=monthly_pool)
        + "\n"
        + ui_text(cfg, "creative_quota_used").format(used=used)
        + "\n"
        + ui_text(cfg, "creative_quota_remaining").format(remaining=remaining)
        + "\n"
        + ui_text(cfg, "creative_quota_period").format(period=period)
    )


def mode_uses_interval(cfg: dict, mode: str) -> bool:
    key = f"{mode}_use_interval"
    if key in cfg:
        return bool(cfg.get(key))
    enabled, times, _, _ = mode_schedule_state(cfg, mode)
    return not bool(enabled and times)


def _parse_local_iso_datetime(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _interval_next_run_key(mode: str) -> str:
    return "creative_interval_next_run_at" if mode == "creative" else "rss_interval_next_run_at"


def _interval_last_run_key(mode: str) -> str:
    return "creative_last_interval_run_at" if mode == "creative" else "rss_last_interval_run_at"


def _scheduled_next_allowed_key(mode: str) -> str:
    return "creative_scheduled_next_allowed_at" if mode == "creative" else "rss_scheduled_next_allowed_at"


def _quiet_hours_keys(mode: str) -> tuple[str, str]:
    if mode == "creative":
        return "creative_quiet_hours_start", "creative_quiet_hours_end"
    return "rss_quiet_hours_start", "rss_quiet_hours_end"


def _quiet_hours_windows_key(mode: str) -> str:
    return "creative_quiet_hours_windows" if mode == "creative" else "rss_quiet_hours_windows"


def quiet_windows_for_mode(cfg: dict, mode: str) -> list[tuple[str, str]]:
    windows: list[tuple[str, str]] = []
    raw_windows = cfg.get(_quiet_hours_windows_key(mode))
    if isinstance(raw_windows, list):
        for item in raw_windows:
            start = ""
            end = ""
            if isinstance(item, str):
                parts = item.split("-", 1)
                if len(parts) == 2:
                    start, end = parts[0].strip(), parts[1].strip()
            elif isinstance(item, dict):
                start = str(item.get("start") or "").strip()
                end = str(item.get("end") or "").strip()
            if _parse_hhmm(start) and _parse_hhmm(end) and start != end:
                windows.append((start, end))
    if windows:
        return windows
    start_key, end_key = _quiet_hours_keys(mode)
    start = str(cfg.get(start_key) or "").strip()
    end = str(cfg.get(end_key) or "").strip()
    if _parse_hhmm(start) and _parse_hhmm(end) and start != end:
        return [(start, end)]
    return []


def set_quiet_windows_for_mode(cfg: dict, mode: str, windows: list[tuple[str, str]]) -> None:
    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for start, end in windows:
        if not _parse_hhmm(start) or not _parse_hhmm(end) or start == end:
            continue
        token = f"{start}-{end}"
        if token in seen:
            continue
        seen.add(token)
        normalized.append((start, end))
    cfg[_quiet_hours_windows_key(mode)] = [f"{start}-{end}" for start, end in normalized]
    start_key, end_key = _quiet_hours_keys(mode)
    if normalized:
        cfg[start_key] = normalized[0][0]
        cfg[end_key] = normalized[0][1]
    else:
        cfg[start_key] = ""
        cfg[end_key] = ""


def user_timezone_offset_hours(cfg: dict) -> int:
    raw = cfg.get("channel_timezone_offset_hours", None)
    if raw is None:
        raw = cfg.get("timezone_offset_hours", 0)
    try:
        offset = int(raw)
    except (TypeError, ValueError):
        offset = 0
    return max(-12, min(14, offset))


def user_now(cfg: dict) -> datetime:
    return (datetime.now(timezone.utc) + timedelta(hours=user_timezone_offset_hours(cfg))).replace(tzinfo=None)


def user_timezone_label(cfg: dict) -> str:
    offset = user_timezone_offset_hours(cfg)
    sign = "+" if offset >= 0 else ""
    return f"UTC{sign}{offset}"


def channel_timezone_is_set(cfg: dict) -> bool:
    return cfg.get("channel_timezone_offset_hours", None) is not None


def ensure_channel_timezone(cfg: dict, channel: str | None = None) -> tuple[int, str]:
    current = cfg.get("channel")
    if channel and current != channel:
        switch_active_channel(cfg, channel)
    if channel_timezone_is_set(cfg):
        if channel and current != channel:
            switch_active_channel(cfg, current)
        return user_timezone_offset_hours(cfg), "existing"

    raw_legacy = cfg.get("timezone_offset_hours", 0)
    try:
        inferred = int(raw_legacy)
        parsed_ok = True
    except (TypeError, ValueError):
        inferred = 0
        parsed_ok = False
    inferred = max(-12, min(14, inferred))
    cfg["channel_timezone_offset_hours"] = inferred
    if channel and current != channel:
        switch_active_channel(cfg, current)
    reason = "legacy_global" if parsed_ok else "fallback_utc"
    logger.info("[CHANNEL_TIMEZONE] action=autodetect reason=%s value=%s channel=%s", reason, inferred, channel or cfg.get("channel"))
    return inferred, reason


def parse_timezone_offset_hours(value: str) -> int | None:
    raw = (value or "").strip().upper().replace(" ", "")
    if raw.startswith("UTC"):
        raw = raw[3:]
    if raw in {"", "+", "-"}:
        return None
    if raw == "0":
        return 0
    match = re.fullmatch(r"([+-]?)(\d{1,2})", raw)
    if not match:
        return None
    sign, hh = match.groups()
    offset = int(hh)
    if sign == "-":
        offset = -offset
    if offset < -12 or offset > 14:
        return None
    return offset


def _parse_hhmm(value: str) -> tuple[int, int] | None:
    raw = (value or "").strip()
    if not re.fullmatch(r"\d{2}:\d{2}", raw):
        return None
    hh, mm = raw.split(":", 1)
    h = int(hh)
    m = int(mm)
    if h > 23 or m > 59:
        return None
    return h, m


def _quiet_window_for_day(start_hm: tuple[int, int], end_hm: tuple[int, int], now: datetime) -> tuple[datetime, datetime]:
    start_dt = now.replace(hour=start_hm[0], minute=start_hm[1], second=0, microsecond=0)
    end_dt = now.replace(hour=end_hm[0], minute=end_hm[1], second=0, microsecond=0)
    if start_dt <= end_dt:
        return start_dt, end_dt
    if now >= start_dt:
        return start_dt, end_dt + timedelta(days=1)
    return start_dt - timedelta(days=1), end_dt


def is_blocked_now(cfg: dict, mode: str, now: datetime) -> bool:
    windows = quiet_windows_for_mode(cfg, mode)
    if not windows:
        logger.info("[BLOCKED_HOURS_CHECK] mode=%s blocked=false reason=no_windows", mode)
        return False
    for start, end in windows:
        start_hm = _parse_hhmm(start)
        end_hm = _parse_hhmm(end)
        if not start_hm or not end_hm or start_hm == end_hm:
            continue
        start_dt, end_dt = _quiet_window_for_day(start_hm, end_hm, now)
        if start_dt <= now < end_dt:
            logger.info("[BLOCKED_HOURS_CHECK] mode=%s blocked=true now=%s window=%s-%s", mode, now.isoformat(timespec="minutes"), start, end)
            logger.info("[BLOCKED_HOURS_ACTIVE] mode=%s window=%s-%s", mode, start, end)
            return True
    logger.info("[BLOCKED_HOURS_CHECK] mode=%s blocked=false now=%s", mode, now.isoformat(timespec="minutes"))
    return False


def rss_freshness_minutes(cfg: dict) -> int:
    raw = cfg.get("rss_freshness_minutes", 180)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = 180
    return max(15, min(1440, value))


IMPORTANT_KEYWORDS_DEFAULT = [
    "injury", "official", "confirmed", "transfer", "signed", "contract", "surgery",
    "suspended", "lineup", "starting xi", "breaking",
    "травм", "официал", "подтвержд", "трансфер", "подписал", "контракт", "операц", "дисквалиф",
    "состав", "стартов", "срочно",
    "lesión", "oficial", "confirmado", "fichaje", "firmó", "contrato", "cirugía",
    "suspendido", "alineación", "once inicial", "última hora",
]


def rss_important_freshness_minutes(cfg: dict) -> int:
    raw = cfg.get("rss_important_freshness_minutes", 480)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = 480
    normal = rss_freshness_minutes(cfg)
    return max(normal, min(2880, value))


def important_keywords(cfg: dict) -> list[str]:
    configured = cfg.get("rss_important_keywords")
    if isinstance(configured, list):
        values = [str(x).strip().lower() for x in configured if str(x).strip()]
        if values:
            return values
    return IMPORTANT_KEYWORDS_DEFAULT


def classify_candidate_importance(cfg: dict, title: str, summary: str) -> tuple[bool, list[str]]:
    haystack = f"{clean_text(title).lower()} {clean_text(summary).lower()}"
    hits: list[str] = []
    for keyword in important_keywords(cfg):
        if keyword and keyword in haystack:
            hits.append(keyword)
    is_important = bool(hits)
    logger.info(
        "[CANDIDATE_IMPORTANCE] important=%s hits=%s title=%s",
        is_important,
        ",".join(hits[:8]) if hits else "-",
        clean_text(title)[:140],
    )
    return is_important, hits


def allowed_freshness_threshold(cfg: dict, is_important: bool) -> int:
    return rss_important_freshness_minutes(cfg) if is_important else rss_freshness_minutes(cfg)


def candidate_age_minutes_from_published(published_struct, now_utc: datetime) -> float | None:
    if not published_struct:
        return None
    try:
        published_dt = datetime.fromtimestamp(time.mktime(published_struct), tz=timezone.utc)
    except Exception:
        return None
    age = now_utc - published_dt
    return max(0.0, age.total_seconds() / 60.0)


def candidate_is_fresh(cfg: dict, published_struct, now_utc: datetime, source: str, *, is_important: bool = False) -> bool:
    age_min = candidate_age_minutes_from_published(published_struct, now_utc)
    threshold = allowed_freshness_threshold(cfg, is_important)
    logger.info(
        "[CANDIDATE_AGE] source=%s age_min=%s threshold_min=%s important=%s",
        source,
        f"{age_min:.1f}" if age_min is not None else "unknown",
        threshold,
        is_important,
    )
    if age_min is None:
        return True
    if age_min > threshold:
        logger.info("[CANDIDATE_SKIPPED_STALE] source=%s age_min=%.1f threshold_min=%s important=%s", source, age_min, threshold, is_important)
        return False
    return True


def _apply_quiet_hours(cfg: dict, mode: str, candidate: datetime) -> datetime:
    windows = quiet_windows_for_mode(cfg, mode)
    if not windows:
        return candidate
    adjusted = candidate
    for _ in range(24):
        next_allowed = adjusted
        for start, end in windows:
            start_hm = _parse_hhmm(start)
            end_hm = _parse_hhmm(end)
            if not start_hm or not end_hm or start_hm == end_hm:
                continue
            start_dt, end_dt = _quiet_window_for_day(start_hm, end_hm, adjusted)
            if start_dt <= adjusted < end_dt and end_dt > next_allowed:
                next_allowed = end_dt
        if next_allowed == adjusted:
            return adjusted
        adjusted = next_allowed
    return adjusted


def _schedule_next_interval_run(cfg: dict, mode: str, from_time: datetime) -> datetime:
    interval_min = int(cfg.get("interval_minutes", 30) or 30)
    if interval_min <= 0:
        interval_min = 30
    next_run = from_time + timedelta(minutes=interval_min)
    next_run = _apply_quiet_hours(cfg, mode, next_run)
    cfg[_interval_next_run_key(mode)] = next_run.isoformat(timespec="seconds")
    return next_run


def should_run_mode_now(
    cfg: dict,
    mode: str,
    now: datetime,
    last_post_at: dict[tuple[int, str, str], datetime],
    user_id: int,
    channel: str,
) -> bool:
    enabled, times, last_date, last_time = mode_schedule_state(cfg, mode)
    use_schedule = not mode_uses_interval(cfg, mode)
    logger.info("[SCHEDULE_MODE] mode=%s strategy=%s enabled=%s times=%s", mode, "scheduled" if use_schedule else "interval", enabled, len(times))
    if use_schedule:
        if not enabled or not times:
            cfg.pop(_scheduled_next_allowed_key(mode), None)
            return False

        pending_key = _scheduled_next_allowed_key(mode)
        pending_run = _parse_local_iso_datetime(cfg.get(pending_key) or "")
        if pending_run:
            adjusted_pending = _apply_quiet_hours(cfg, mode, pending_run)
            if adjusted_pending != pending_run:
                cfg[pending_key] = adjusted_pending.isoformat(timespec="seconds")
                save_client(user_id, cfg)
                return False
            if now < adjusted_pending:
                return False
            due_slot = str(cfg.get(f"{mode}_scheduled_due_slot") or "").strip()
            cfg.pop(pending_key, None)
            if due_slot:
                cfg[f"{mode}_scheduled_due_slot"] = due_slot
            return True

        now_slot = now.strftime("%H:%M")
        times_set = set(times)
        if now_slot not in times_set:
            return False

        today = str(now.date())
        if last_date == today and last_time == now_slot:
            return False

        candidate = now.replace(second=0, microsecond=0)
        next_allowed = _apply_quiet_hours(cfg, mode, candidate)
        cfg[f"{mode}_scheduled_due_slot"] = now_slot
        if next_allowed > candidate:
            cfg[pending_key] = next_allowed.isoformat(timespec="seconds")
            save_client(user_id, cfg)
            return False
        cfg.pop(pending_key, None)
        return True

    interval_min = int(cfg.get("interval_minutes", 30))
    if interval_min <= 0:
        interval_min = 30
    cfg.pop(_scheduled_next_allowed_key(mode), None)

    next_key = _interval_next_run_key(mode)
    next_run = _parse_local_iso_datetime(cfg.get(next_key) or "")
    if not next_run:
        prev_key = _interval_last_run_key(mode)
        prev_stored = _parse_local_iso_datetime(cfg.get(prev_key) or "")
        if prev_stored:
            next_run = prev_stored + timedelta(minutes=interval_min)
            next_run = _apply_quiet_hours(cfg, mode, next_run)
            cfg[next_key] = next_run.isoformat(timespec="seconds")
        else:
            _schedule_next_interval_run(cfg, mode, now)
            save_client(user_id, cfg)
            return False

    if next_run:
        adjusted_next_run = _apply_quiet_hours(cfg, mode, next_run)
        if adjusted_next_run != next_run:
            cfg[next_key] = adjusted_next_run.isoformat(timespec="seconds")
            save_client(user_id, cfg)
            return False
        if now < next_run:
            return False

    prev = last_post_at.get((user_id, channel, mode))
    if not prev:
        stored_key = _interval_last_run_key(mode)
        prev = _parse_local_iso_datetime(cfg.get(stored_key) or "")
        if not prev:
            cfg[stored_key] = now.isoformat(timespec="seconds")
            save_client(user_id, cfg)
            return False
    if prev and (now - prev).total_seconds() < interval_min * 60:
        return False
    return True

def mark_mode_scheduled(cfg: dict, mode: str, now: datetime) -> None:
    interval_key = _interval_last_run_key(mode)
    cfg[interval_key] = now.isoformat(timespec="seconds")
    _schedule_next_interval_run(cfg, mode, now)
    cfg.pop(_scheduled_next_allowed_key(mode), None)
    enabled, times, _, _ = mode_schedule_state(cfg, mode)
    if not (enabled and times):
        return
    due_slot = str(cfg.pop(f"{mode}_scheduled_due_slot", "") or "").strip()
    if not due_slot:
        due_slot = now.strftime("%H:%M")
    if mode == "creative":
        cfg["creative_last_schedule_date"] = str(now.date())
        cfg["creative_last_schedule_time"] = due_slot
    else:
        cfg["rss_last_schedule_date"] = str(now.date())
        cfg["rss_last_schedule_time"] = due_slot

def build_mode_schedule_submenu(cfg: dict, mode: str) -> InlineKeyboardMarkup:
    return build_mode_schedule_menu(ui_pack(cfg), mode, mode_activation_state(cfg, mode), mode_uses_interval(cfg, mode))


def schedule_mode_title_key(mode: str) -> str:
    return "schedule_mode_title_creative" if mode == "creative" else "schedule_mode_title_rss"


def schedule_mode_menu_text(cfg: dict, mode: str) -> str:
    interval_min = int(cfg.get("interval_minutes", 30))
    return (
        ui_text(cfg, schedule_mode_title_key(mode))
        + "\n\n"
        + ui_text(cfg, "schedule_guided_intro")
        + "\n\n"
        + ui_text(cfg, "schedule_interval_current").format(interval=interval_min)
        + "\n"
        + ui_text(cfg, "schedule_timezone").format(timezone=user_timezone_label(cfg))
        + "\n"
        + "\n"
        + ui_text(cfg, "schedule_current").format(schedule=schedule_summary_for_mode(cfg, mode))
    )


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



async def send_prompt_parent_menu(update: Update, cfg: dict, mode: str, notice: str) -> None:
    if not update.message:
        return
    if mode == "creative":
        await update.message.reply_text(
            text=notice + "\n\n" + ui_text(cfg, "creative_menu_title"),
            reply_markup=build_creative_submenu(cfg),
        )
        return

    await update.message.reply_text(
        text=notice + "\n\n" + ui_text(cfg, "rss_menu_title"),
        reply_markup=build_rss_submenu(cfg),
    )


def validate_hhmm(value: str) -> bool:
    if not re.fullmatch(r"\d{2}:\d{2}", value or ""):
        return False
    hh, mm = value.split(":", 1)
    return 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59


def schedule_summary(cfg: dict) -> str:
    enabled = ui_text(cfg, "schedule_status_on") if cfg.get("schedule_enabled") else ui_text(cfg, "schedule_status_off")
    times = cfg.get("schedule_times", [])
    times_text = ", ".join(times) if times else ui_text(cfg, "schedule_times_empty")
    return f"{ui_text(cfg, 'schedule_summary_status').replace('• ', '')}: {enabled}\n{ui_text(cfg, 'schedule_summary_slots').replace('• ', '').split(':', 1)[0]}: {times_text}"


def parse_schedule_input(text: str) -> list[str] | None:
    chunks = [x.strip() for x in text.split(",") if x.strip()]
    if not chunks:
        return None
    if any(not validate_hhmm(x) for x in chunks):
        return None
    return sorted(set(chunks))


async def rss_preview_text(bot, user_id: int, cfg: dict) -> tuple[str, str | None, list[MessageEntity], Path | None]:
    feeds = cfg.get("feeds", [])
    if not feeds:
        return ui_text(cfg, "preview_empty_no_feed"), None, [], None
    best = pick_newest_unseen(cfg)
    if not best:
        return preview_empty_state_text(cfg), None, [], None
    _, title, link, src = best
    summary, source_context, weak_context, social_source = build_rss_generation_input(src, link, title)
    msg = llm_generate_post(user_id, cfg, title, summary, link, source_context, weak_context, social_source)
    image_url = extract_image_url_for_link(src, link)
    text, entities = build_rss_message_payload(cfg, msg, link)
    preview_prefix = "🧪 Preview:\n\n"
    preview_entities = _load_message_entities([_message_entity_to_dict(e) for e in entities], offset_shift=len(preview_prefix))
    send_image_url, temp_file = await prepare_rss_image_for_sending(bot, cfg, user_id, image_url)
    return preview_prefix + text, send_image_url, preview_entities, temp_file

def feeds_overview(cfg: dict) -> str:
    feeds = cfg.get("feeds", [])
    if not feeds:
        return ui_text(cfg, "feeds_empty")
    lines = []
    for i, item in enumerate(feeds, start=1):
        url = _feed_url(item)
        name = _feed_name(item)
        lines.append(f"{i}) {name} — {url}" if name else f"{i}) {url}")
    return "🧾 Feeds:\n" + "\n".join(lines)


def feed_management_text(cfg: dict, selected_channel: str) -> str:
    limit = feed_limit_per_channel(cfg)
    return (
        selected_channel_text(cfg, selected_channel)
        + "\n\n"
        + ui_text(cfg, "feed_management_title")
        + "\n"
        + ui_text(cfg, "feed_management_help")
        + "\n"
        + ui_text(cfg, "feed_limit_status").format(count=len(cfg.get("feeds", [])), limit=limit)
        + "\n\n"
        + feeds_overview(cfg)
    )


def build_feeds_delete_menu(cfg: dict) -> InlineKeyboardMarkup:
    return build_feed_delete_menu(ui_pack(cfg), cfg.get("feeds", []))


def quiet_hours_overview(cfg: dict, mode: str) -> str:
    windows = quiet_windows_for_mode(cfg, mode)
    if not windows:
        return ui_text(cfg, "quiet_hours_empty")
    lines = [f"{idx}) {start}-{end}" for idx, (start, end) in enumerate(windows, start=1)]
    return ui_text(cfg, "quiet_hours_list_title") + "\n" + "\n".join(lines)


def quiet_hours_management_text(cfg: dict, mode: str, selected_channel: str) -> str:
    return (
        selected_channel_text(cfg, selected_channel)
        + "\n\n"
        + ui_text(cfg, "quiet_hours_management_title")
        + "\n"
        + ui_text(cfg, "schedule_timezone").format(timezone=user_timezone_label(cfg))
        + "\n\n"
        + quiet_hours_overview(cfg, mode)
    )


def build_mode_quiet_hours_menu(cfg: dict, mode: str) -> InlineKeyboardMarkup:
    return build_quiet_hours_menu(ui_pack(cfg), mode)


def build_mode_quiet_hours_delete_menu(cfg: dict, mode: str) -> InlineKeyboardMarkup:
    windows = [f"{start}-{end}" for start, end in quiet_windows_for_mode(cfg, mode)]
    return build_quiet_hours_delete_menu(ui_pack(cfg), mode, windows)


def channels_overview(cfg: dict) -> str:
    channels = get_saved_channels(cfg)
    slots = int(cfg.get("channel_slots", 0) or 0)
    if not channels:
        return ui_text(cfg, "channels_empty_state").format(slots=slots)
    return ui_text(cfg, "channels_list_title").format(count=len(channels), slots=slots) + "\n" + "\n".join(
        [f"{i+1}) {channel_display_name(cfg, ch)}" for i, ch in enumerate(channels)]
    )


def build_channel_delete_selection_menu(cfg: dict) -> InlineKeyboardMarkup:
    channels = get_saved_channels(cfg)
    return build_channel_delete_menu(ui_pack(cfg), [channel_display_name(cfg, ch) for ch in channels])


def get_saved_channels(cfg: dict) -> list[str]:
    return normalize_channels(cfg)


def channel_display_name(cfg: dict, channel: str) -> str:
    meta = cfg.get("channel_meta")
    if isinstance(meta, dict):
        item = meta.get(channel)
        if isinstance(item, dict):
            title = (item.get("title") or "").strip()
            if title:
                return title
            username = (item.get("username") or "").strip()
            if username:
                return username if username.startswith("@") else f"@{username}"

    labels = cfg.get("channel_labels")
    if isinstance(labels, dict):
        label = (labels.get(channel) or "").strip()
        if label:
            return label
    return channel


def selected_channel_text(cfg: dict, channel: str) -> str:
    return ui_text(cfg, "channel_selected_now").format(channel=channel_display_name(cfg, channel))


def rss_setup_guidance_text(user_id: int, cfg: dict) -> str:
    if not cfg.get("feeds"):
        return ui_text(cfg, "rss_primary_next_feed")
    if not (get_mode_prompt(user_id, cfg, "rss") or "").strip():
        return ui_text(cfg, "rss_primary_next_prompt")
    issues = activation_readiness_issues(cfg, "rss")
    if any(issue in issues for issue in (ui_text(cfg, "activation_issue_timezone"), ui_text(cfg, "activation_issue_posting_mode"), ui_text(cfg, "activation_issue_slots"))):
        return ui_text(cfg, "rss_primary_next_schedule")
    if not mode_activation_state(cfg, "rss"):
        return ui_text(cfg, "rss_primary_next_enable")
    return ui_text(cfg, "rss_primary_next_preview")


def rss_menu_text(user_id: int, cfg: dict, selected_channel: str) -> str:
    return (
        ui_text(cfg, "rss_menu_title")
        + "\n\n"
        + selected_channel_text(cfg, selected_channel)
        + "\n\n"
        + rss_setup_guidance_text(user_id, cfg)
    )


def creative_menu_text(cfg: dict, selected_channel: str) -> str:
    return (
        ui_text(cfg, "creative_menu_title")
        + "\n\n"
        + selected_channel_text(cfg, selected_channel)
        + "\n\n"
        + creative_quota_summary_text(cfg)
    )


def _flow_control_hint(cfg: dict) -> str:
    return ui_text(cfg, "flow_controls_hint")


def _flow_question_prompt(cfg: dict, questions: list[tuple[str, str]], step: int) -> str:
    return f"{step + 1}/{len(questions)}. {questions[step][1]}\n\n{_flow_control_hint(cfg)}"


def _rss_quickstart_steps_status(user_id: int, cfg: dict) -> list[tuple[str, bool]]:
    has_feed = bool(cfg.get("feeds"))
    has_prompt = bool((get_mode_prompt(user_id, cfg, "rss") or "").strip())
    has_posting_mode = ("rss_use_interval" in cfg) or bool(mode_schedule_state(cfg, "rss")[1])
    return [
        (ui_text(cfg, "quickstart_step_channel"), bool(cfg.get("channel"))),
        (ui_text(cfg, "quickstart_step_feed"), has_feed),
        (ui_text(cfg, "quickstart_step_prompt"), has_prompt),
        (ui_text(cfg, "quickstart_step_mode"), has_posting_mode),
        (ui_text(cfg, "quickstart_step_timezone"), channel_timezone_is_set(cfg)),
        (ui_text(cfg, "quickstart_step_enable"), mode_activation_state(cfg, "rss")),
        (ui_text(cfg, "quickstart_step_preview"), mode_activation_state(cfg, "rss") and has_feed),
    ]


def rss_quickstart_text(user_id: int, cfg: dict, selected_channel: str) -> str:
    lines = [
        ui_text(cfg, "rss_quickstart_title"),
        "",
        selected_channel_text(cfg, selected_channel),
        "",
        ui_text(cfg, "rss_quickstart_intro"),
        "",
    ]
    for label, done in _rss_quickstart_steps_status(user_id, cfg):
        marker = "✅" if done else "➡️"
        lines.append(f"{marker} {label}")
    lines.append("")
    lines.append(ui_text(cfg, "rss_quickstart_next_hint"))
    return "\n".join(lines)


def build_rss_quickstart_menu(cfg: dict) -> InlineKeyboardMarkup:
    labels = ui_pack(cfg)
    rows = [
        [InlineKeyboardButton(labels["btn_quickstart_add_feed"], callback_data="ui:addfeed")],
        [InlineKeyboardButton(labels["btn_quickstart_set_prompt"], callback_data="ui:rss:stylemenu")],
        [InlineKeyboardButton(labels["btn_quickstart_simple_mode"], callback_data="ui:rss:quickstart:simple_mode")],
        [InlineKeyboardButton(labels["btn_quickstart_timezone"], callback_data="ui:schedule:timezone")],
        [InlineKeyboardButton(labels["btn_quickstart_enable"], callback_data="ui:schedule:rss:toggle")],
        [InlineKeyboardButton(labels["btn_quickstart_preview"], callback_data="ui:rss:preview")],
        [InlineKeyboardButton(labels["btn_back"], callback_data="ui:mode:rss:menu")],
    ]
    return InlineKeyboardMarkup(rows)


def _preview_feed_stats(cfg: dict) -> tuple[int, int]:
    total_entries = 0
    processed_entries = 0
    posted = set(cfg.get("posted_urls", []))
    for feed_entry in cfg.get("feeds", []):
        feed_url = _feed_url(feed_entry)
        if not feed_url:
            continue
        try:
            parsed = feedparser.parse(feed_url)
        except Exception:
            continue
        entries = getattr(parsed, "entries", []) or []
        total_entries += len(entries)
        for entry in entries:
            link = _entry_primary_link(entry)
            if link and normalize_url(link) in posted:
                processed_entries += 1
    return total_entries, processed_entries


def preview_empty_state_text(cfg: dict) -> str:
    if not cfg.get("feeds"):
        return ui_text(cfg, "preview_empty_no_feed")
    total_entries, processed_entries = _preview_feed_stats(cfg)
    if total_entries == 0:
        return ui_text(cfg, "preview_empty_feed_no_items")
    if processed_entries >= total_entries and total_entries > 0:
        return ui_text(cfg, "preview_empty_all_processed")
    return ui_text(cfg, "preview_empty_filtered")


def clear_mode_channel_selection(context: ContextTypes.DEFAULT_TYPE) -> None:
    prev = context.user_data.get("mode_selected_channel")
    if prev:
        logger.info("[CHANNEL_CONTEXT] action=clear previous=%s", prev)
    context.user_data.pop("mode_selected_channel", None)
    # cleanup legacy state key
    context.user_data.pop("mode_selected_channel_idx", None)


def set_mode_channel_selection(context: ContextTypes.DEFAULT_TYPE, channel: str) -> None:
    logger.info("[CHANNEL_CONTEXT] action=set channel=%s", channel)
    context.user_data["mode_selected_channel"] = channel
    # cleanup legacy state key
    context.user_data.pop("mode_selected_channel_idx", None)


def mark_channel_selection_origin(context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    context.user_data["mode_selected_for_action"] = action


def consume_channel_selection_origin(context: ContextTypes.DEFAULT_TYPE, action: str) -> bool:
    return context.user_data.pop("mode_selected_for_action", None) == action


def require_channel_context(cfg: dict, context: ContextTypes.DEFAULT_TYPE, action: str) -> tuple[str | None, str | None]:
    channels = get_saved_channels(cfg)
    if not channels:
        clear_mode_channel_selection(context)
        context.user_data.pop("active_channel_idx", None)
        logger.info("[CHANNEL_CONTEXT] action=require result=empty action=%s", action)
        return None, "empty"

    if action in {"creative_menu", "rss_menu"}:
        selected_channel = context.user_data.get("mode_selected_channel")
        if isinstance(selected_channel, str) and selected_channel in channels:
            logger.info("[NAV_PARENT] action=%s resolved=selected_channel channel=%s", action, selected_channel)
            context.user_data["active_channel_idx"] = channels.index(selected_channel)
            switch_active_channel(cfg, selected_channel)
            return selected_channel, None
        idx = context.user_data.get("active_channel_idx")
        if isinstance(idx, int) and 0 <= idx < len(channels):
            selected_channel = channels[idx]
            logger.info("[NAV_PARENT] action=%s resolved=active_channel_idx channel=%s", action, selected_channel)
            set_mode_channel_selection(context, selected_channel)
            switch_active_channel(cfg, selected_channel)
            return selected_channel, None
        current_channel = cfg.get("channel")
        if isinstance(current_channel, str) and current_channel in channels:
            logger.info("[NAV_PARENT] action=%s resolved=current_channel channel=%s", action, current_channel)
            set_mode_channel_selection(context, current_channel)
            context.user_data["active_channel_idx"] = channels.index(current_channel)
            switch_active_channel(cfg, current_channel)
            return current_channel, None
        logger.info("[NAV_PARENT] action=%s resolved=pick_required", action)
        logger.info("[CHANNEL_CONTEXT] action=require result=pick action=%s", action)
        return None, "pick"

    explicit_selection_actions = {
        "creative_editprompt",
        "creative_buildprompt",
        "creative_copystyle",
        "creative_variety",
        "creative_visual",
        "creative_content_plan",
        "creative_content_plan_regenerate",
        "creative_content_plan_edit",
        "creative_sources",
        "creative_sources_topic_pillars",
        "creative_sources_idea_bank",
        "creative_sources_inspiration_links",
        "creative_sources_source_snippets",
        "creative_preview",
        "rss_editprompt",
        "rss_buildprompt",
        "rss_copystyle",
        "rss_feeds",
        "rss_output",
        "creative_output",
        "rss_preview",
        "schedule_rss_menu",
        "schedule_creative_menu",
        "schedule_rss_edit",
        "schedule_creative_edit",
        "schedule_rss_toggle",
        "schedule_creative_toggle",
        "schedule_rss_switch",
        "schedule_creative_switch",
        "schedule_rss_interval",
        "schedule_creative_interval",
        "schedule_creative_quiet",
        "schedule_rss_quiet",
        "schedule_rss_freshness",
        "schedule_creative_freshness",
        "schedule_rss_timezone",
        "schedule_creative_timezone",
    }

    if action in explicit_selection_actions:
        selected_channel = context.user_data.get("mode_selected_channel")
        if isinstance(selected_channel, str) and selected_channel in channels:
            context.user_data["active_channel_idx"] = channels.index(selected_channel)
            switch_active_channel(cfg, selected_channel)
            return selected_channel, None
        idx = context.user_data.get("active_channel_idx")
        if isinstance(idx, int) and 0 <= idx < len(channels):
            selected_channel = channels[idx]
            set_mode_channel_selection(context, selected_channel)
            switch_active_channel(cfg, selected_channel)
            return selected_channel, None
        current_channel = cfg.get("channel")
        if isinstance(current_channel, str) and current_channel in channels:
            set_mode_channel_selection(context, current_channel)
            context.user_data["active_channel_idx"] = channels.index(current_channel)
            switch_active_channel(cfg, current_channel)
            return current_channel, None
        clear_mode_channel_selection(context)
        logger.info("[CHANNEL_CONTEXT] action=require result=pick action=%s", action)
        return None, "pick"

    idx = context.user_data.get("active_channel_idx")
    if isinstance(idx, int) and 0 <= idx < len(channels):
        switch_active_channel(cfg, channels[idx])
        return channels[idx], None

    logger.info("[CHANNEL_CONTEXT] action=require result=pick action=%s", action)
    return None, "pick"


def build_channel_picker(cfg: dict, action: str, back_callback: str) -> InlineKeyboardMarkup:
    channels = get_saved_channels(cfg)
    channel_labels = [channel_display_name(cfg, ch) for ch in channels]
    button_callbacks = [f"ui:pickchannel:{action}:{idx}" for idx in range(1, len(channel_labels) + 1)]
    logger.info(
        "[CHANNEL_PICKER_OPEN] action=%s back=%s channels=%s",
        action,
        back_callback,
        channel_labels,
    )
    logger.info("[CHANNEL_PICKER_BUTTON] action=%s callbacks=%s", action, button_callbacks)
    return build_channel_picker_menu(ui_pack(cfg), channel_labels, action, back_callback)


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
    first_name = (getattr(update.effective_user, "first_name", None) or "").strip()
    welcome_key = "start_welcome_named" if first_name else "start_welcome"
    welcome_text = UI_TEXTS[lang].get(welcome_key, UI_TEXTS[lang]["start_welcome"])
    if first_name and "{name}" in welcome_text:
        welcome_text = welcome_text.format(name=first_name)
    await send_menu(update, cfg, welcome_text)

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = ensure_creative_monthly_counter(ensure_daily_counter(load_client(user_id)))
    sub = cfg.get("subscription_until") or ui_text(cfg, "status_inactive")
    channels = get_saved_channels(cfg)
    channels_text = "\n".join([f"• {channel_display_name(cfg, ch)}" for ch in channels]) if channels else ui_text(cfg, "status_not_set")
    rss_daily = int(cfg.get("rss_daily_limit", 0) or 0)
    creative_monthly = creative_monthly_limit(cfg)
    creative_used = int(cfg.get("creative_monthly_count", 0) or 0)
    creative_remaining = max(creative_monthly - creative_used, 0)
    creative_period = cfg.get("creative_monthly_period") or _current_month_key()

    id_label = f"🆔 {ui_text(cfg, 'status_id')}:"
    id_value = str(user_id)
    text = (
        f"{ui_text(cfg, 'status_title')}\n\n"
        f"{id_label}\n<code>{id_value}</code>\n\n"
        f"📺 {ui_text(cfg, 'status_channels')}:\n{channels_text}\n\n"
        f"📰 {ui_text(cfg, 'status_rss_daily')}: {rss_daily}\n"
        f"✨ {ui_text(cfg, 'status_creative_monthly_pool')}: {creative_monthly}\n"
        f"✨ {ui_text(cfg, 'status_creative_monthly_used')}: {creative_used}\n"
        f"✨ {ui_text(cfg, 'status_creative_monthly_remaining')}: {creative_remaining}\n"
        f"✨ {ui_text(cfg, 'status_creative_monthly_period')}: {creative_period}\n"
        f"📅 {ui_text(cfg, 'status_valid_until')}: {sub}"
    )
    raw_mode = (cfg.get("mode") or "rss").strip().lower()
    active_mode = "creative" if raw_mode == "creator" else ("rss" if raw_mode == "rss" else "both")
    if active_mode == "both":
        live_summary = (
            ui_text(cfg, "status_live_title")
            + "\n"
            + ui_text(cfg, "status_live_mode_section").format(mode="RSS")
            + "\n"
            + schedule_summary_for_mode(cfg, "rss")
            + "\n\n"
            + ui_text(cfg, "status_live_mode_section").format(mode="Creative")
            + "\n"
            + schedule_summary_for_mode(cfg, "creative")
        )
    else:
        display_mode = "Creative" if active_mode == "creative" else "RSS"
        live_summary = (
            ui_text(cfg, "status_live_title")
            + "\n"
            + ui_text(cfg, "status_live_mode_section").format(mode=display_mode)
            + "\n"
            + schedule_summary_for_mode(cfg, active_mode)
        )
    text += "\n\n" + live_summary
    markup = build_main_menu_clean(cfg)

    if update.callback_query:
        q = update.callback_query
        await q.answer()
        try:
            await q.edit_message_text(text=text, parse_mode=ParseMode.HTML, reply_markup=markup)
        except BadRequest:
            await q.message.reply_text(text=text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return

    if update.message:
        await update.message.reply_text(text=text, parse_mode=ParseMode.HTML, reply_markup=markup)

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

    await send_menu(update, cfg, build_help_text(cfg))

from telegram.error import BadRequest
from telegram import Update
from telegram.ext import ContextTypes

async def ui_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    user_id = q.from_user.id
    cfg = load_client(user_id)
    data = q.data or ""
    if data in {"ui:setup", "ui:modes", "ui:mode:rss:menu", "ui:mode:creative:menu"}:
        logger.info("[CHANNEL_PICKER_BACK] callback=%s", data)
    if data in {
        "ui:setup",
        "ui:modes",
        "ui:backmain",
        "ui:mode:rss:menu",
        "ui:mode:creative:menu",
        "ui:creative:intake",
        "ui:creative:ideas",
        "ui:creative:campaigns",
        "ui:creative:publish_settings",
        "ui:creative:advanced",
        "ui:creative:contentplan",
        "ui:creative:sources",
        "ui:creative:variety",
        "ui:creative:visual",
        "ui:rss:feeds",
        "ui:rss:output",
        "ui:creative:output",
        "ui:schedule:rss:menu",
        "ui:schedule:creative:menu",
        "ui:schedule:rss:quiet",
        "ui:schedule:creative:quiet",
    }:
        logger.info("[NAV_BACK] callback=%s selected_channel=%s", data, context.user_data.get("mode_selected_channel"))

    if data == "ui:lang":
        await q.answer()
        await q.message.reply_text(ui_text(cfg, "choose_lang"), reply_markup=build_lang_menu())
        return

    if data.startswith("ui:setlang:"):
        choice = data.split(":", 2)[2].strip().lower()
        if choice in ("en", "ru"):
            cfg["language"] = choice
            save_client(user_id, cfg)
            await reply_ui(update, tr(cfg, "lang_set") + "\n\n" + tr(cfg, "menu_title") + "\n\n" + pay_line(update, cfg), cfg)
            return
        await q.answer()
        return

    if data.startswith("ui:pickchannel:"):
        logger.info("[CHANNEL_PICKER_CALLBACK] data=%s", data)
        parts = data.split(":", 3)
        if len(parts) != 4:
            logger.warning("[CHANNEL_PICKER_ERROR] reason=bad_parts data=%s parts=%s", data, parts)
            await q.answer()
            return
        action = parts[2]
        try:
            idx = int(parts[3]) - 1
        except ValueError:
            logger.warning("[CHANNEL_PICKER_ERROR] reason=bad_index data=%s", data)
            await q.answer()
            return

        channels = get_saved_channels(cfg)
        if idx < 0 or idx >= len(channels):
            logger.warning("[CHANNEL_PICKER_ERROR] reason=index_out_of_range data=%s channels=%s", data, len(channels))
            await q.answer()
            return

        context.user_data["active_channel_idx"] = idx
        selected = channels[idx]
        set_mode_channel_selection(context, selected)
        mark_channel_selection_origin(context, action)
        switch_active_channel(cfg, selected)
        save_client(user_id, cfg)
        logger.info("[CHANNEL_SELECTED] action=%s channel=%s idx=%s", action, selected, idx + 1)
        await q.answer()

        route_data = data
        if action == "creative_menu":
            text = creative_menu_text(cfg, selected)
            await q.message.reply_text(text, reply_markup=build_creative_submenu(cfg))
            return
        if action == "rss_menu":
            text = rss_menu_text(user_id, cfg, selected)
            await q.message.reply_text(text, reply_markup=build_rss_submenu(cfg))
            return
        if action in ("creative_editprompt", "rss_editprompt"):
            mapped = "ui:creative:stylemenu" if action == "creative_editprompt" else "ui:rss:stylemenu"
            route_data = mapped
        elif action in ("creative_buildprompt", "rss_buildprompt"):
            mapped = "ui:creative:buildprompt" if action == "creative_buildprompt" else "ui:rss:buildprompt"
            route_data = mapped
        elif action in ("creative_copystyle", "rss_copystyle"):
            mapped = "ui:creative:copystyle" if action == "creative_copystyle" else "ui:rss:copystyle"
            route_data = mapped
        elif action == "creative_variety":
            route_data = "ui:creative:variety"
        elif action == "creative_intake":
            route_data = "ui:creative:intake"
        elif action == "creative_ideas":
            route_data = "ui:creative:ideas"
        elif action == "creative_campaigns":
            route_data = "ui:creative:campaigns"
        elif action == "creative_publish_settings":
            route_data = "ui:creative:publish_settings"
        elif action == "creative_visual":
            route_data = "ui:creative:visual"
        elif action == "creative_content_plan":
            route_data = "ui:creative:contentplan"
        elif action == "creative_content_plan_regenerate":
            route_data = "ui:creative:contentplan:regenerate"
        elif action == "creative_content_plan_edit":
            route_data = "ui:creative:contentplan:edit"
        elif action == "creative_sources":
            route_data = "ui:creative:sources"
        elif action.startswith("creative_sources_"):
            source_type = action.replace("creative_sources_", "", 1)
            if source_type in CREATIVE_SOURCE_META:
                route_data = f"ui:creative:sources:{source_type}"
        elif action in ("creative_preview", "rss_preview"):
            mapped = "ui:creative:preview" if action == "creative_preview" else "ui:rss:preview"
            route_data = mapped
        elif action in ("rss_feeds",):
            route_data = "ui:rss:feeds"
        elif action == "rss_output":
            route_data = "ui:rss:output"
        elif action == "creative_output":
            route_data = "ui:creative:output"
        elif action in ("schedule_rss_menu", "schedule_creative_menu"):
            mapped = "ui:schedule:rss:menu" if action == "schedule_rss_menu" else "ui:schedule:creative:menu"
            route_data = mapped
        elif action in ("schedule_rss_edit", "schedule_creative_edit"):
            mapped = "ui:schedule:rss:edit" if action == "schedule_rss_edit" else "ui:schedule:creative:edit"
            route_data = mapped
        elif action in ("schedule_rss_toggle", "schedule_creative_toggle"):
            mapped = "ui:schedule:rss:toggle" if action == "schedule_rss_toggle" else "ui:schedule:creative:toggle"
            route_data = mapped
        elif action in ("schedule_rss_switch", "schedule_creative_switch"):
            mapped = "ui:schedule:rss:switch_mode" if action == "schedule_rss_switch" else "ui:schedule:creative:switch_mode"
            route_data = mapped
        elif action in ("schedule_rss_interval", "schedule_creative_interval"):
            mapped = "ui:schedule:rss:interval" if action == "schedule_rss_interval" else "ui:schedule:creative:interval"
            route_data = mapped
        elif action in ("schedule_rss_quiet", "schedule_creative_quiet"):
            mapped = "ui:schedule:rss:quiet" if action == "schedule_rss_quiet" else "ui:schedule:creative:quiet"
            route_data = mapped
        elif action in ("schedule_rss_freshness", "schedule_creative_freshness"):
            mapped = "ui:schedule:rss:freshness" if action == "schedule_rss_freshness" else "ui:schedule:creative:freshness"
            route_data = mapped
        elif action in ("schedule_rss_timezone", "schedule_creative_timezone"):
            mode = "creative" if action == "schedule_creative_timezone" else "rss"
            context.user_data["awaiting_timezone_mode"] = mode
            route_data = "ui:schedule:timezone"
        elif action == "setup_modes":
            route_data = "ui:modes"
        else:
            logger.warning("[CHANNEL_PICKER_ERROR] reason=unknown_action action=%s", action)
            await q.message.reply_text(selected_channel_text(cfg, selected))
            return
        logger.info("[CHANNEL_PICKER_CALLBACK] action=%s routed_to=%s", action, route_data)
        data = route_data

    if data == "ui:setup":
        logger.info("[NAV_ENTER] screen=setup")
        clear_mode_channel_selection(context)
        await q.answer()
        try:
            await q.edit_message_text(text=ui_text(cfg, "setup_menu_title"), reply_markup=build_setup_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=ui_text(cfg, "setup_menu_title"), reply_markup=build_setup_menu(cfg))
        return

    if data == "ui:setup:channels":
        text = ui_text(cfg, "channel_management_title") + "\n\n" + channels_overview(cfg)
        await q.answer()
        try:
            await q.edit_message_text(text=text, reply_markup=build_channel_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_channel_menu(cfg))
        return

    if data == "ui:setup:scheduling":
        clear_mode_channel_selection(context)
        await q.answer()
        try:
            await q.edit_message_text(text=ui_text(cfg, "modes_menu_title"), reply_markup=build_modes_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=ui_text(cfg, "modes_menu_title"), reply_markup=build_modes_submenu(cfg))
        return

    if data == "ui:modes":
        channels = get_saved_channels(cfg)
        selected = context.user_data.get("mode_selected_channel")
        if not channels:
            clear_mode_channel_selection(context)
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if not isinstance(selected, str) or selected not in channels:
            clear_mode_channel_selection(context)
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "setup_modes", "ui:setup"),
            )
            return
        logger.info("[NAV_ENTER] screen=modes channel=%s", selected)
        await q.answer()
        try:
            await q.edit_message_text(
                text=ui_text(cfg, "modes_menu_title") + "\n\n" + selected_channel_text(cfg, selected),
                reply_markup=build_modes_submenu(cfg),
            )
        except BadRequest:
            await q.message.reply_text(
                text=ui_text(cfg, "modes_menu_title") + "\n\n" + selected_channel_text(cfg, selected),
                reply_markup=build_modes_submenu(cfg),
            )
        return

    if data == "ui:mode:creative:menu":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_menu")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_menu", "ui:modes"),
            )
            return
        logger.info("[NAV_ENTER] screen=creative_menu channel=%s", selected)
        await q.answer()
        text = creative_menu_text(cfg, selected)
        try:
            await q.edit_message_text(text=text, reply_markup=build_creative_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_creative_submenu(cfg))
        return

    if data == "ui:creative:publish_settings":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_publish_settings")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_publish_settings", "ui:mode:creative:menu"),
            )
            return
        await q.answer()
        text = ui_text(cfg, "creative_publish_settings_title") + "\n\n" + selected_channel_text(cfg, selected)
        try:
            await q.edit_message_text(text=text, reply_markup=build_creative_publish_settings_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_creative_publish_settings_submenu(cfg))
        return

    if data == "ui:creative:intake":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_intake")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_intake", "ui:mode:creative:menu"),
            )
            return
        await q.answer()
        text = ui_text(cfg, "channel_intake_intro") + "\n\n" + selected_channel_text(cfg, selected)
        pending_intake = context.user_data.get("awaiting_creative_intake")
        if isinstance(pending_intake, dict):
            step = int(pending_intake.get("step", 0))
            total = len(creative_channel_intake_questions(cfg))
            text += "\n\n" + ui_text(cfg, "flow_resume_hint").format(
                step=min(step + 1, total),
                total=total,
                flow=ui_text(cfg, "flow_name_channel_intake"),
            )
        has_pending_intake = isinstance(context.user_data.get("awaiting_creative_intake"), dict)
        try:
            await q.edit_message_text(text=text, reply_markup=build_creative_intake_submenu(cfg, has_pending_intake))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_creative_intake_submenu(cfg, has_pending_intake))
        return

    if data == "ui:creative:intake:view":
        selected = str(cfg.get("channel") or "").strip()
        await q.answer()
        await q.message.reply_text(
            creative_intake_summary_text(cfg, selected),
            reply_markup=build_creative_intake_submenu(cfg),
        )
        return

    if data == "ui:creative:intake:start":
        selected, state = require_channel_context(cfg, context, "creative_intake")
        if state in {"empty", "pick"}:
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        questions = creative_channel_intake_questions(cfg)
        context.user_data["awaiting_creative_intake"] = {"channel": selected, "step": 0, "answers": {}}
        await q.answer()
        await q.message.reply_text(
            ui_text(cfg, "channel_intake_start")
            + "\n\n"
            + _flow_question_prompt(cfg, questions, 0)
        )
        return

    if data == "ui:creative:intake:resume":
        awaiting = context.user_data.get("awaiting_creative_intake")
        questions = creative_channel_intake_questions(cfg)
        if not isinstance(awaiting, dict):
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "flow_nothing_to_resume"), reply_markup=build_creative_intake_submenu(cfg))
            return
        step = max(0, min(int(awaiting.get("step", 0)), len(questions) - 1))
        await q.answer()
        await q.message.reply_text(
            ui_text(cfg, "flow_resuming").format(flow=ui_text(cfg, "flow_name_channel_intake"), step=step + 1, total=len(questions))
            + "\n\n"
            + _flow_question_prompt(cfg, questions, step)
        )
        return

    if data == "ui:creative:intake:fast_start":
        selected, state = require_channel_context(cfg, context, "creative_intake")
        if state in {"empty", "pick"}:
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        questions = creative_fast_start_questions(cfg)
        context.user_data["awaiting_creative_fast_start"] = {"channel": selected, "step": 0, "answers": {}}
        await q.answer()
        await q.message.reply_text(
            ui_text(cfg, "quickstart_start")
            + "\n\n"
            + _flow_question_prompt(cfg, questions, 0)
        )
        return

    if data == "ui:creative:ideas":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_sources_idea_bank")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_sources_idea_bank", "ui:mode:creative:menu"),
            )
            return
        await q.answer()
        text = creative_source_list_text(cfg, "idea_bank", selected)
        await q.message.reply_text(text, reply_markup=build_creative_source_list_submenu(cfg, "idea_bank"))
        return

    if data == "ui:creative:campaigns":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_campaigns")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_campaigns", "ui:mode:creative:menu"),
            )
            return
        await q.answer()
        intro = ui_text(cfg, "campaigns_intro") + "\n\n" + selected_channel_text(cfg, selected)
        pending_campaign = context.user_data.get("awaiting_campaign_create")
        if isinstance(pending_campaign, dict):
            step = int(pending_campaign.get("step", 0))
            total = len(creative_campaign_questions(cfg))
            intro += "\n\n" + ui_text(cfg, "flow_resume_hint").format(
                step=min(step + 1, total),
                total=total,
                flow=ui_text(cfg, "flow_name_campaign"),
            )
        has_pending_campaign = isinstance(context.user_data.get("awaiting_campaign_create"), dict)
        await q.message.reply_text(intro, reply_markup=build_creative_campaigns_submenu(cfg, has_pending_campaign))
        return

    if data == "ui:creative:campaigns:create":
        selected = str(cfg.get("channel") or "").strip()
        context.user_data["awaiting_campaign_create"] = {"channel": selected, "step": 0, "answers": {}}
        questions = creative_campaign_questions(cfg)
        await q.answer()
        await q.message.reply_text(
            ui_text(cfg, "campaign_create_start")
            + "\n\n"
            + _flow_question_prompt(cfg, questions, 0)
        )
        return

    if data == "ui:creative:campaigns:create:resume":
        awaiting = context.user_data.get("awaiting_campaign_create")
        questions = creative_campaign_questions(cfg)
        if not isinstance(awaiting, dict):
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "flow_nothing_to_resume"), reply_markup=build_creative_campaigns_submenu(cfg))
            return
        step = max(0, min(int(awaiting.get("step", 0)), len(questions) - 1))
        await q.answer()
        await q.message.reply_text(
            ui_text(cfg, "flow_resuming").format(flow=ui_text(cfg, "flow_name_campaign"), step=step + 1, total=len(questions))
            + "\n\n"
            + _flow_question_prompt(cfg, questions, step)
        )
        return

    if data == "ui:creative:advanced":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_advanced")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_advanced", "ui:mode:creative:menu"),
            )
            return
        await q.answer()
        text = ui_text(cfg, "creative_advanced_title") + "\n\n" + selected_channel_text(cfg, selected) + "\n\n" + ui_text(cfg, "creative_advanced_intro")
        try:
            await q.edit_message_text(text=text, reply_markup=build_creative_advanced_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_creative_advanced_submenu(cfg))
        return

    if data == "ui:creative:campaigns:view":
        await q.answer()
        campaigns = creative_campaigns(cfg)
        if not campaigns:
            await q.message.reply_text(ui_text(cfg, "campaign_empty"), reply_markup=build_creative_campaigns_submenu(cfg))
            return
        lines = [ui_text(cfg, "campaign_list_title")]
        active_id = cfg.get("creative_active_campaign_id")
        for item in campaigns:
            marker = "✅ " if item.get("id") == active_id else ""
            lines.append(
                f"{marker}{item.get('id')}) {item.get('goal') or 'Campaign'} · {item.get('duration_days')}d · {item.get('target_action') or '-'}"
            )
        await q.message.reply_text("\n".join(lines), reply_markup=build_creative_campaigns_submenu(cfg))
        return

    if data == "ui:creative:campaigns:activate":
        campaigns = creative_campaigns(cfg)
        if not campaigns:
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "campaign_empty"), reply_markup=build_creative_campaigns_submenu(cfg))
            return
        context.user_data["awaiting_campaign_activate"] = True
        lines = [ui_text(cfg, "campaign_activate_prompt")]
        for item in campaigns:
            lines.append(f"{item.get('id')}) {item.get('goal') or 'Campaign'}")
        await q.answer()
        await q.message.reply_text("\n".join(lines), reply_markup=build_creative_campaigns_submenu(cfg))
        return
    if data == "ui:creative:contentplan":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_content_plan")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_content_plan", "ui:mode:creative:menu"),
            )
            return
        await q.answer()
        text = creative_content_plan_menu_text(cfg, selected)
        try:
            await q.edit_message_text(text=text, reply_markup=build_creative_content_plan_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_creative_content_plan_submenu(cfg))
        return

    if data == "ui:creative:visual":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_visual")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_visual", "ui:mode:creative:menu"),
            )
            return
        await q.answer()
        text = creative_visual_support_menu_text(cfg, selected)
        try:
            await q.edit_message_text(text=text, reply_markup=build_creative_visual_support_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_creative_visual_support_submenu(cfg))
        return

    if data in ("ui:creative:visual:idea", "ui:creative:visual:search", "ui:creative:visual:aiprompt"):
        selected, state = require_channel_context(cfg, context, "creative_visual")
        if state in {"empty", "pick"}:
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        key_map = {
            "ui:creative:visual:idea": ("idea", "creative_visual_generating_idea", "creative_visual_label_idea", "last_visual_idea"),
            "ui:creative:visual:search": ("search", "creative_visual_generating_search_query", "creative_visual_label_search_query", "last_visual_search_query"),
            "ui:creative:visual:aiprompt": ("aiprompt", "creative_visual_generating_ai_prompt", "creative_visual_label_ai_prompt", "last_visual_ai_prompt"),
        }
        action, progress_key, label_key, save_key = key_map[data]
        await q.answer()
        await q.message.reply_text(ui_text(cfg, progress_key))
        try:
            result = llm_generate_visual_support(cfg, selected, action)
            if not result:
                raise ValueError("empty visual support output")
            cfg[save_key] = result
            save_client(user_id, cfg)
            prefix = ""
            if not creative_current_topic_item(cfg):
                prefix = ui_text(cfg, "creative_visual_topic_fallback") + "\n\n"
            await q.message.reply_text(
                prefix + f"{ui_text(cfg, label_key)}:\n{result}",
                reply_markup=build_creative_visual_support_submenu(cfg),
            )
        except Exception:
            logger.exception("Creative visual support failed for user %s", user_id)
            await q.message.reply_text(
                ui_text(cfg, "creative_visual_error"),
                reply_markup=build_creative_visual_support_submenu(cfg),
            )
        return

    if data == "ui:creative:contentplan:generate":
        selected, state = require_channel_context(cfg, context, "creative_content_plan")
        if state in {"empty", "pick"}:
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "content_plan_no_plan"))
            return
        await q.answer()
        await q.message.reply_text(ui_text(cfg, "content_plan_generating"))
        try:
            plan = llm_generate_content_plan(user_id, cfg, days=7)
            cfg["creative_content_plan"] = plan
            save_client(user_id, cfg)
            await q.message.reply_text(
                ui_text(cfg, "content_plan_generated"),
                reply_markup=build_creative_content_plan_submenu(cfg),
            )
            await q.message.reply_text(
                creative_content_plan_view_text(cfg, selected),
                reply_markup=build_creative_content_plan_submenu(cfg),
            )
        except Exception:
            logger.exception("Content plan generate failed for user %s", user_id)
            await q.message.reply_text(
                ui_text(cfg, "prompt_builder_error"),
                reply_markup=build_creative_content_plan_submenu(cfg),
            )
        return

    if data == "ui:creative:contentplan:view":
        selected, state = require_channel_context(cfg, context, "creative_content_plan")
        if state in {"empty", "pick"}:
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "content_plan_no_plan"))
            return
        await q.answer()
        await q.message.reply_text(
            creative_content_plan_view_text(cfg, selected),
            reply_markup=build_creative_content_plan_submenu(cfg),
        )
        return

    if data == "ui:creative:contentplan:regenerate":
        selected, state = require_channel_context(cfg, context, "creative_content_plan_regenerate")
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_content_plan_regenerate", "ui:creative:contentplan"),
            )
            return
        items = creative_content_plan(cfg)
        if not items:
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "content_plan_no_plan"), reply_markup=build_creative_content_plan_submenu(cfg))
            return
        await q.answer()
        await q.message.reply_text(
            ui_text(cfg, "content_plan_choose_regenerate"),
            reply_markup=build_creative_content_plan_item_picker(cfg, "regenerate"),
        )
        return

    if data == "ui:creative:contentplan:edit":
        selected, state = require_channel_context(cfg, context, "creative_content_plan_edit")
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_content_plan_edit", "ui:creative:contentplan"),
            )
            return
        items = creative_content_plan(cfg)
        if not items:
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "content_plan_no_plan"), reply_markup=build_creative_content_plan_submenu(cfg))
            return
        await q.answer()
        await q.message.reply_text(
            ui_text(cfg, "content_plan_choose_edit"),
            reply_markup=build_creative_content_plan_item_picker(cfg, "edit"),
        )
        return

    if data.startswith("ui:creative:contentplan:regenerate:"):
        try:
            item_idx = int(data.rsplit(":", 1)[1]) - 1
        except ValueError:
            await q.answer()
            return
        items = creative_content_plan(cfg)
        if item_idx < 0 or item_idx >= len(items):
            await q.answer()
            return
        await q.answer()
        await q.message.reply_text(ui_text(cfg, "content_plan_regenerating_item"))
        try:
            replacement = llm_generate_content_plan(user_id, cfg, days=1, regenerate_item=items[item_idx])
            if not replacement:
                raise ValueError("empty replacement")
            new_item = replacement[0]
            new_item["id"] = items[item_idx].get("id") or (item_idx + 1)
            new_item["day_label"] = items[item_idx].get("day_label") or f"Day {item_idx + 1}"
            items[item_idx] = new_item
            cfg["creative_content_plan"] = items
            save_client(user_id, cfg)
            await q.message.reply_text(
                ui_text(cfg, "content_plan_item_regenerated"),
                reply_markup=build_creative_content_plan_submenu(cfg),
            )
        except Exception:
            logger.exception("Content plan item regenerate failed for user %s", user_id)
            await q.message.reply_text(
                ui_text(cfg, "prompt_builder_error"),
                reply_markup=build_creative_content_plan_submenu(cfg),
            )
        return

    if data.startswith("ui:creative:contentplan:edit:"):
        try:
            item_idx = int(data.rsplit(":", 1)[1]) - 1
        except ValueError:
            await q.answer()
            return
        items = creative_content_plan(cfg)
        if item_idx < 0 or item_idx >= len(items):
            await q.answer()
            return
        await q.answer()
        item = items[item_idx]
        context.user_data["awaiting_content_plan_edit"] = {"channel": cfg.get("channel"), "idx": item_idx}
        await q.message.reply_text(
            ui_text(cfg, "content_plan_edit_prompt").format(
                day_label=item.get("day_label") or f"Day {item_idx + 1}",
                topic=item.get("topic") or "—",
                angle=item.get("angle") or "—",
            )
        )
        return

    if data == "ui:creative:sources":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_sources")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_sources", "ui:mode:creative:menu"),
            )
            return
        await q.answer()
        text = (
            ui_text(cfg, "source_center_title")
            + "\n\n"
            + selected_channel_text(cfg, selected)
            + "\n\n"
            + ui_text(cfg, "source_center_intro")
        )
        try:
            await q.edit_message_text(text=text, reply_markup=build_creative_source_center_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_creative_source_center_submenu(cfg))
        return

    if data.startswith("ui:creative:sources:"):
        parts = data.split(":")
        if len(parts) >= 4:
            source_type = parts[3]
            meta = CREATIVE_SOURCE_META.get(source_type)
            if not meta:
                await q.answer()
                return
            selected, state = require_channel_context(cfg, context, f"creative_sources_{source_type}")
            if state == "pick":
                await q.answer()
                await q.message.reply_text(
                    ui_text(cfg, "channel_picker_title"),
                    reply_markup=build_channel_picker(cfg, f"creative_sources_{source_type}", "ui:creative:sources"),
                )
                return
            selected_channel = selected or (cfg.get("channel") or "")

            if len(parts) == 4:
                await q.answer()
                text = creative_source_list_text(cfg, source_type, selected_channel)
                submenu = build_creative_source_list_submenu(cfg, source_type)
                try:
                    await q.edit_message_text(text=text, reply_markup=submenu)
                except BadRequest:
                    await q.message.reply_text(text=text, reply_markup=submenu)
                return

            action = parts[4]
            if action == "view":
                await q.answer()
                await q.message.reply_text(
                    creative_source_list_text(cfg, source_type, selected_channel),
                    reply_markup=build_creative_source_list_submenu(cfg, source_type),
                )
                return
            if action == "add":
                await q.answer()
                context.user_data["awaiting_creative_source_add"] = {
                    "channel": cfg.get("channel"),
                    "source_type": source_type,
                }
                await q.message.reply_text(ui_text(cfg, meta["add_prompt_key"]))
                return
            if action == "generate" and source_type == "idea_bank":
                await q.answer()
                await q.message.reply_text(ui_text(cfg, "idea_bank_generating"))
                intake = cfg.get("creative_channel_intake") if isinstance(cfg.get("creative_channel_intake"), dict) else {}
                prompt = (
                    "Generate 10 concise creator idea bank entries as plain lines.\n"
                    "Each line should start with one strategic bucket tag and colon.\n"
                    "Allowed buckets: pain, objection, proof, story, benefit, cta, educational angle.\n"
                    "Mix different buckets across the list.\n"
                    f"Channel topic: {intake.get('channel_about') if intake else 'N/A'}\n"
                    f"Audience: {intake.get('audience') if intake else 'N/A'}\n"
                    f"Offer: {intake.get('offers') if intake else 'N/A'}\n"
                    "No numbering, one idea per line."
                )
                try:
                    if LLM_PROVIDER == "openai_compat":
                        url = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
                        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
                        payload = {
                            "model": OPENAI_MODEL,
                            "messages": [{"role": "system", "content": "You generate strategic creator ideas."}, {"role": "user", "content": prompt}],
                            "temperature": 0.9,
                        }
                        r = requests.post(url, headers=headers, json=payload, timeout=60)
                        r.raise_for_status()
                        raw = (r.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
                    else:
                        r = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=60)
                        r.raise_for_status()
                        raw = r.json().get("response", "")
                    generated = [re.sub(r"^[\\-\\d\\.)\\s]+", "", line).strip() for line in (raw or "").splitlines()]
                    generated = [line[:220] for line in generated if line]
                    items = creative_source_items(cfg, meta["key"])
                    items.extend(generated[:10])
                    cfg[meta["key"]] = items[-150:]
                    save_client(user_id, cfg)
                    await q.message.reply_text(
                        ui_text(cfg, "idea_bank_generated").format(count=min(len(generated), 10)),
                        reply_markup=build_creative_source_list_submenu(cfg, source_type),
                    )
                except Exception:
                    logger.exception("Idea bank generation failed for user %s", user_id)
                    await q.message.reply_text(
                        ui_text(cfg, "prompt_builder_error"),
                        reply_markup=build_creative_source_list_submenu(cfg, source_type),
                    )
                return
            if action == "delete":
                await q.answer()
                items = creative_source_items(cfg, meta["key"])
                if not items:
                    await q.message.reply_text(
                        ui_text(cfg, "source_delete_empty"),
                        reply_markup=build_creative_source_list_submenu(cfg, source_type),
                    )
                    return
                await q.message.reply_text(
                    ui_text(cfg, "source_delete_choose"),
                    reply_markup=build_creative_source_delete_submenu(cfg, source_type, items),
                )
                return
            if action == "del" and len(parts) >= 6:
                try:
                    item_idx = int(parts[5]) - 1
                except ValueError:
                    await q.answer()
                    return
                items = creative_source_items(cfg, meta["key"])
                if item_idx < 0 or item_idx >= len(items):
                    await q.answer()
                    return
                removed = items.pop(item_idx)
                cfg[meta["key"]] = items
                save_client(user_id, cfg)
                await q.answer()
                await q.message.reply_text(
                    ui_text(cfg, "source_item_deleted").format(item=removed[:80]),
                    reply_markup=build_creative_source_list_submenu(cfg, source_type),
                )
                return

    if data == "ui:creative:variety":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_variety")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_variety", "ui:mode:creative:menu"),
            )
            return
        await q.answer()
        text = (
            ui_text(cfg, "creative_variety_title")
            + "\n\n"
            + selected_channel_text(cfg, selected)
            + "\n\n"
            + ui_text(cfg, "creative_variety_intro")
            + "\n\n"
            + ui_text(cfg, "creative_variety_summary").format(
                level=ui_text(cfg, "variation_level_value_" + creative_variation_level(cfg)),
                post_types=", ".join(ui_text(cfg, "post_type_" + t) for t in creative_post_types(cfg)),
                avoid=ui_text(cfg, "label_on") if bool(cfg.get("creative_avoid_repetition", True)) else ui_text(cfg, "label_off"),
            )
        )
        try:
            await q.edit_message_text(text=text, reply_markup=build_creative_variety_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_creative_variety_submenu(cfg))
        return

    if data == "ui:creative:variety:level":
        await q.answer()
        try:
            await q.edit_message_text(text=ui_text(cfg, "variation_level_title"), reply_markup=build_creative_variation_level_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=ui_text(cfg, "variation_level_title"), reply_markup=build_creative_variation_level_submenu(cfg))
        return

    if data.startswith("ui:creative:variety:level:"):
        level = data.rsplit(":", 1)[1].strip().lower()
        if level in CREATIVE_VARIATION_LEVELS:
            cfg["creative_variation_level"] = level
            save_client(user_id, cfg)
        await q.answer()
        try:
            await q.edit_message_text(text=ui_text(cfg, "variation_level_title"), reply_markup=build_creative_variation_level_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=ui_text(cfg, "variation_level_title"), reply_markup=build_creative_variation_level_submenu(cfg))
        return

    if data == "ui:creative:variety:types":
        await q.answer()
        try:
            await q.edit_message_text(text=ui_text(cfg, "post_types_title"), reply_markup=build_creative_post_types_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=ui_text(cfg, "post_types_title"), reply_markup=build_creative_post_types_submenu(cfg))
        return

    if data.startswith("ui:creative:variety:type:"):
        post_type = data.rsplit(":", 1)[1].strip().lower()
        selected_types = creative_post_types(cfg)
        if post_type in CREATIVE_POST_TYPES:
            if post_type in selected_types:
                selected_types = [x for x in selected_types if x != post_type]
            else:
                selected_types.append(post_type)
            cfg["creative_post_types"] = selected_types or list(CREATIVE_POST_TYPES)
            cfg["creative_last_post_type_idx"] = -1
            save_client(user_id, cfg)
        await q.answer()
        try:
            await q.edit_message_text(text=ui_text(cfg, "post_types_title"), reply_markup=build_creative_post_types_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=ui_text(cfg, "post_types_title"), reply_markup=build_creative_post_types_submenu(cfg))
        return

    if data == "ui:creative:variety:avoid":
        cfg["creative_avoid_repetition"] = not bool(cfg.get("creative_avoid_repetition", True))
        save_client(user_id, cfg)
        await q.answer()
        text = ui_text(cfg, "creative_variety_title") + "\n\n" + ui_text(cfg, "creative_variety_note")
        try:
            await q.edit_message_text(text=text, reply_markup=build_creative_variety_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_creative_variety_submenu(cfg))
        return

    if data == "ui:creative:preview":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        try:
            selected, state = require_channel_context(cfg, context, "creative_preview")
        except Exception:
            logger.exception("preview config stage failed for user %s", user_id)
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "preview_stage_config_failed"),
                reply_markup=build_creative_submenu(cfg),
            )
            return
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_preview", "ui:mode:creative:menu"),
            )
            return
        await q.answer()
        try:
            await q.message.reply_text(ui_text(cfg, "preview_loading"))
            if not selected:
                logger.warning("preview config stage failed for user %s: no selected channel", user_id)
                await q.message.reply_text(
                    ui_text(cfg, "preview_stage_config_failed"),
                    reply_markup=build_creative_submenu(cfg),
                )
                return

            try:
                msg = creator_make_post(user_id, cfg)
                save_client(user_id, cfg)
            except Exception:
                logger.exception("preview ai stage failed for user %s", user_id)
                await q.message.reply_text(
                    ui_text(cfg, "preview_stage_ai_failed"),
                    reply_markup=build_creative_submenu(cfg),
                )
                return

            try:
                preview_prefix = selected_channel_text(cfg, selected) + "\n\n" + "🧪 Preview:\n\n"
                creator_entities = apply_bold_title(msg, []) if bool(cfg.get("creative_bold_title", False)) else []
                await q.message.reply_text(
                    preview_prefix + msg,
                    entities=_load_message_entities([_message_entity_to_dict(e) for e in creator_entities], offset_shift=len(preview_prefix)) or None,
                    reply_markup=build_creative_submenu(cfg),
                )
                await q.message.reply_text(ui_text(cfg, "preview_ready_guidance"), reply_markup=build_creative_submenu(cfg))
                diagnostics = creative_preview_diagnostics_text(cfg)
                if diagnostics:
                    await q.message.reply_text(diagnostics, reply_markup=build_creative_submenu(cfg))
            except Exception:
                logger.exception("preview send stage failed for user %s", user_id)
                await q.message.reply_text(
                    ui_text(cfg, "preview_stage_send_failed"),
                    reply_markup=build_creative_submenu(cfg),
                )
                return
        except Exception:
            logger.exception("Creative preview failed for user %s", user_id)
            await q.message.reply_text(
                ui_text(cfg, "preview_temporarily_unavailable"),
                reply_markup=build_creative_submenu(cfg),
            )
        return

    if data == "ui:mode:rss:menu":
        if not await enforce_mode_paywall(update, cfg, "rss"):
            return
        selected, state = require_channel_context(cfg, context, "rss_menu")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_menu", "ui:modes"),
            )
            return
        logger.info("[NAV_ENTER] screen=rss_menu channel=%s", selected)
        await q.answer()
        text = rss_menu_text(user_id, cfg, selected)
        try:
            await q.edit_message_text(text=text, reply_markup=build_rss_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_rss_submenu(cfg))
        return

    if data == "ui:rss:quickstart":
        if not await enforce_mode_paywall(update, cfg, "rss"):
            return
        selected, state = require_channel_context(cfg, context, "rss_menu")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_menu", "ui:modes"),
            )
            return
        await q.answer()
        text = rss_quickstart_text(user_id, cfg, selected)
        try:
            await q.edit_message_text(text=text, reply_markup=build_rss_quickstart_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_rss_quickstart_menu(cfg))
        return

    if data == "ui:rss:quickstart:simple_mode":
        if not await enforce_mode_paywall(update, cfg, "rss"):
            return
        selected, state = require_channel_context(cfg, context, "rss_menu")
        if state in {"empty", "pick"}:
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_empty") if state == "empty" else ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_menu", "ui:modes") if state == "pick" else None,
            )
            return
        cfg["rss_use_interval"] = True
        if int(cfg.get("interval_minutes", 0) or 0) <= 0:
            cfg["interval_minutes"] = 60
        if not _parse_local_iso_datetime(cfg.get(_interval_next_run_key("rss")) or ""):
            _schedule_next_interval_run(cfg, "rss", user_now(cfg))
        save_client(user_id, cfg)
        await q.answer()
        text = (
            rss_quickstart_text(user_id, cfg, selected)
            + "\n\n"
            + ui_text(cfg, "quickstart_simple_mode_set")
        )
        try:
            await q.edit_message_text(text=text, reply_markup=build_rss_quickstart_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_rss_quickstart_menu(cfg))
        return

    if data in ("ui:rss:pause_posting", "ui:rss:resume_posting"):
        if not await enforce_mode_paywall(update, cfg, "rss"):
            return
        selected, state = require_channel_context(cfg, context, "rss_menu")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_menu", "ui:modes"),
            )
            return
        pause_requested = data == "ui:rss:pause_posting"
        set_rss_posting_paused(cfg, pause_requested)
        save_client(user_id, cfg)
        await q.answer(ui_text(cfg, "rss_posting_paused_short") if pause_requested else ui_text(cfg, "rss_posting_resumed_short"))
        notice_key = "rss_posting_paused_notice" if pause_requested else "rss_posting_resumed_notice"
        text = rss_menu_text(user_id, cfg, selected) + "\n\n" + ui_text(cfg, notice_key)
        try:
            await q.edit_message_text(text=text, reply_markup=build_rss_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_rss_submenu(cfg))
        return

    if data == "ui:rss:preview":
        if not await enforce_mode_paywall(update, cfg, "rss"):
            return
        try:
            selected, state = require_channel_context(cfg, context, "rss_preview")
        except Exception:
            logger.exception("preview config stage failed for user %s", user_id)
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "preview_stage_config_failed"),
                reply_markup=build_rss_submenu(cfg),
            )
            return
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_preview", "ui:mode:rss:menu"),
            )
            return
        await q.answer()
        await q.message.reply_text(ui_text(cfg, "preview_loading"))
        temp_file = None
        try:
            if not selected:
                logger.warning("preview config stage failed for user %s: no selected channel", user_id)
                await q.message.reply_text(
                    ui_text(cfg, "preview_stage_config_failed"),
                    reply_markup=build_rss_submenu(cfg),
                )
                return

            try:
                feeds = cfg.get("feeds", [])
                if not feeds:
                    await q.message.reply_text(
                        selected_channel_text(cfg, selected) + "\n\n" + ui_text(cfg, "preview_empty_no_feed"),
                        reply_markup=build_rss_submenu(cfg),
                    )
                    return
                best = pick_newest_unseen(cfg)
                if not best:
                    await q.message.reply_text(
                        selected_channel_text(cfg, selected) + "\n\n" + preview_empty_state_text(cfg),
                        reply_markup=build_rss_submenu(cfg),
                    )
                    return
                _, title, link, src = best
                summary, source_context, weak_context, social_source = build_rss_generation_input(src, link, title)
                image_url = extract_image_url_for_link(src, link)
            except Exception:
                logger.exception("preview rss stage failed for user %s", user_id)
                await q.message.reply_text(
                    ui_text(cfg, "preview_stage_rss_failed"),
                    reply_markup=build_rss_submenu(cfg),
                )
                return

            try:
                msg = llm_generate_post(user_id, cfg, title, summary, link, source_context, weak_context, social_source)
            except Exception:
                logger.exception("preview ai stage failed for user %s", user_id)
                await q.message.reply_text(
                    ui_text(cfg, "preview_stage_ai_failed"),
                    reply_markup=build_rss_submenu(cfg),
                )
                return

            text, entities = build_rss_message_payload(cfg, msg, link)
            preview_prefix = "🧪 Preview:\n\n"
            preview = preview_prefix + text
            preview_entities = _load_message_entities(
                [_message_entity_to_dict(e) for e in entities], offset_shift=len(preview_prefix)
            )

            try:
                send_image_url, temp_file, preview_notice_key = await prepare_rss_preview_image_for_sending(
                    context.bot, cfg, user_id, image_url
                )
            except Exception:
                logger.exception("preview image stage failed for user %s", user_id)
                await q.message.reply_text(
                    ui_text(cfg, "preview_stage_image_failed"),
                    reply_markup=build_rss_submenu(cfg),
                )
                return

            await q.message.reply_text(selected_channel_text(cfg, selected))
            if preview_notice_key:
                await q.message.reply_text(ui_text(cfg, preview_notice_key))
            if send_image_url:
                try:
                    caption_entities = _load_message_entities([_message_entity_to_dict(e) for e in preview_entities], max_offset=1024)
                    photo_input = temp_file if temp_file else send_image_url
                    await q.message.reply_photo(photo=photo_input, caption=preview[:1024], caption_entities=caption_entities or None, reply_markup=build_rss_submenu(cfg))
                    return
                except Exception:
                    logger.exception("preview send stage failed for user %s", user_id)
                    await q.message.reply_text(
                        ui_text(cfg, "preview_stage_send_failed"),
                        reply_markup=build_rss_submenu(cfg),
                    )
                    return

            try:
                await q.message.reply_text(preview, entities=preview_entities or None, reply_markup=build_rss_submenu(cfg))
            except Exception:
                logger.exception("preview send stage failed for user %s", user_id)
                await q.message.reply_text(
                    ui_text(cfg, "preview_stage_send_failed"),
                    reply_markup=build_rss_submenu(cfg),
                )
        except Exception:
            logger.exception("RSS preview failed for user %s", user_id)
            await q.message.reply_text(
                ui_text(cfg, "preview_temporarily_unavailable"),
                reply_markup=build_rss_submenu(cfg),
            )
        finally:
            if temp_file:
                try:
                    temp_file.unlink(missing_ok=True)
                except Exception:
                    pass
        return

    if data in ("ui:schedule:rss:menu", "ui:schedule:creative:menu"):

        mode = "creative" if data.endswith("creative:menu") else "rss"
        context.user_data["active_schedule_mode"] = mode
        action = "schedule_creative_menu" if mode == "creative" else "schedule_rss_menu"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:mode:{mode}:menu"),
            )
            return
        logger.info("[NAV_ENTER] screen=schedule_menu mode=%s channel=%s", mode, selected)
        _, tz_reason = ensure_channel_timezone(cfg, selected)
        if tz_reason != "existing":
            save_client(user_id, cfg)
        await q.answer()
        timezone_notice = ""
        if tz_reason == "legacy_global":
            timezone_notice = ui_text(cfg, "timezone_autodetected_notice").format(timezone=user_timezone_label(cfg)) + "\n\n"
        elif tz_reason == "fallback_utc":
            timezone_notice = ui_text(cfg, "timezone_fallback_notice").format(timezone=user_timezone_label(cfg)) + "\n\n"
        text = selected_channel_text(cfg, selected) + "\n\n" + timezone_notice + schedule_mode_menu_text(cfg, mode)
        try:
            await q.edit_message_text(text=text, reply_markup=build_mode_schedule_submenu(cfg, mode))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_mode_schedule_submenu(cfg, mode))
        return

    if data in ("ui:schedule:rss:edit", "ui:schedule:creative:edit"):
        mode = "creative" if data.endswith("creative:edit") else "rss"
        context.user_data["active_schedule_mode"] = mode
        action = "schedule_creative_edit" if mode == "creative" else "schedule_rss_edit"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:schedule:{mode}:menu"),
            )
            return
        context.user_data["awaiting_schedule_mode"] = mode
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + ui_text(cfg, "schedule_input_instructions")
            + "\n\n"
            + ui_text(cfg, "schedule_current").format(schedule=schedule_summary_for_mode(cfg, mode)),
            reply_markup=build_mode_schedule_submenu(cfg, mode),
        )
        return

    if data in ("ui:schedule:rss:toggle", "ui:schedule:creative:toggle"):
        mode = "creative" if data.endswith("creative:toggle") else "rss"
        context.user_data["active_schedule_mode"] = mode
        action = "schedule_creative_toggle" if mode == "creative" else "schedule_rss_toggle"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:schedule:{mode}:menu"),
            )
            return
        enabled = mode_activation_state(cfg, mode)
        ok, notice = activate_posting(cfg, mode, turn_on=not enabled)
        if not ok:
            await q.answer()
            await q.message.reply_text(notice, reply_markup=build_mode_schedule_submenu(cfg, mode))
            return
        save_client(user_id, cfg)
        await q.answer()
        text = selected_channel_text(cfg, selected) + "\n\n" + notice + "\n\n" + schedule_mode_menu_text(cfg, mode)
        try:
            await q.edit_message_text(text=text, reply_markup=build_mode_schedule_submenu(cfg, mode))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_mode_schedule_submenu(cfg, mode))
        return

    if data in ("ui:schedule:rss:switch_mode", "ui:schedule:creative:switch_mode"):
        mode = "creative" if data.endswith("creative:switch_mode") else "rss"
        context.user_data["active_schedule_mode"] = mode
        action = "schedule_creative_switch" if mode == "creative" else "schedule_rss_switch"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:schedule:{mode}:menu"),
            )
            return
        key = f"{mode}_use_interval"
        cfg[key] = not mode_uses_interval(cfg, mode)
        if cfg[key]:
            next_key = _interval_next_run_key(mode)
            if not _parse_local_iso_datetime(cfg.get(next_key) or ""):
                _schedule_next_interval_run(cfg, mode, user_now(cfg))
        logger.info("[SCHEDULE_MODE] action=switch mode=%s strategy=%s", mode, "interval" if cfg[key] else "scheduled")
        save_client(user_id, cfg)
        notice = ui_text(cfg, "posting_mode_interval_set") if cfg[key] else ui_text(cfg, "posting_mode_scheduled_set")
        await q.answer()
        text = selected_channel_text(cfg, selected) + "\n\n" + notice + "\n\n" + schedule_mode_menu_text(cfg, mode)
        try:
            await q.edit_message_text(text=text, reply_markup=build_mode_schedule_submenu(cfg, mode))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_mode_schedule_submenu(cfg, mode))
        return

    if data in ("ui:schedule:rss:interval", "ui:schedule:creative:interval"):
        mode = "creative" if data.endswith("creative:interval") else "rss"
        context.user_data["active_schedule_mode"] = mode
        action = "schedule_creative_interval" if mode == "creative" else "schedule_rss_interval"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:schedule:{mode}:menu"),
            )
            return
        context.user_data["awaiting_interval_mode"] = mode
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + ui_text(cfg, "interval_input_instructions"),
            reply_markup=build_mode_schedule_submenu(cfg, mode),
        )
        return

    if data in ("ui:schedule:rss:quiet", "ui:schedule:creative:quiet"):
        mode = "creative" if data.endswith("creative:quiet") else "rss"
        context.user_data["active_schedule_mode"] = mode
        action = "schedule_creative_quiet" if mode == "creative" else "schedule_rss_quiet"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:schedule:{mode}:menu"),
            )
            return
        await q.answer()
        text = quiet_hours_management_text(cfg, mode, selected)
        try:
            await q.edit_message_text(text=text, reply_markup=build_mode_quiet_hours_menu(cfg, mode))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_mode_quiet_hours_menu(cfg, mode))
        return

    if data in ("ui:schedule:rss:quiet:add", "ui:schedule:creative:quiet:add"):
        mode = "creative" if data.endswith("creative:quiet:add") else "rss"
        context.user_data["active_schedule_mode"] = mode
        action = "schedule_creative_quiet" if mode == "creative" else "schedule_rss_quiet"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:schedule:{mode}:menu"),
            )
            return
        context.user_data["awaiting_quiet_mode"] = mode
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + ui_text(cfg, "schedule_timezone").format(timezone=user_timezone_label(cfg))
            + "\n\n"
            + ui_text(cfg, "quiet_hours_input_instructions"),
            reply_markup=build_mode_quiet_hours_menu(cfg, mode),
        )
        return

    if data in ("ui:schedule:rss:freshness", "ui:schedule:creative:freshness"):
        mode = "creative" if data.endswith("creative:freshness") else "rss"
        context.user_data["active_schedule_mode"] = mode
        action = "schedule_creative_freshness" if mode == "creative" else "schedule_rss_freshness"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:schedule:{mode}:menu"),
            )
            return
        context.user_data["awaiting_freshness_mode"] = mode
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + ui_text(cfg, "freshness_input_instructions")
            + "\n\n"
            + ui_text(cfg, "schedule_freshness_current").format(minutes=rss_freshness_minutes(cfg)),
            reply_markup=build_mode_schedule_submenu(cfg, mode),
        )
        return

    if data in ("ui:schedule:rss:quiet:delete", "ui:schedule:creative:quiet:delete"):
        mode = "creative" if data.endswith("creative:quiet:delete") else "rss"
        context.user_data["active_schedule_mode"] = mode
        action = "schedule_creative_quiet" if mode == "creative" else "schedule_rss_quiet"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:schedule:{mode}:menu"),
            )
            return
        windows = quiet_windows_for_mode(cfg, mode)
        await q.answer()
        if not windows:
            await q.message.reply_text(ui_text(cfg, "quiet_hours_delete_empty"), reply_markup=build_mode_quiet_hours_menu(cfg, mode))
            return
        text = quiet_hours_management_text(cfg, mode, selected)
        try:
            await q.edit_message_text(text=text, reply_markup=build_mode_quiet_hours_delete_menu(cfg, mode))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_mode_quiet_hours_delete_menu(cfg, mode))
        return

    if data.startswith("ui:schedule:rss:quiet:del:") or data.startswith("ui:schedule:creative:quiet:del:"):
        mode = "creative" if data.startswith("ui:schedule:creative:quiet:del:") else "rss"
        context.user_data["active_schedule_mode"] = mode
        action = "schedule_creative_quiet" if mode == "creative" else "schedule_rss_quiet"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:schedule:{mode}:menu"),
            )
            return
        raw_idx = data.rsplit(":", 1)[-1]
        try:
            idx = int(raw_idx) - 1
        except ValueError:
            await q.answer()
            return
        windows = quiet_windows_for_mode(cfg, mode)
        if idx < 0 or idx >= len(windows):
            await q.answer()
            return
        removed = windows.pop(idx)
        set_quiet_windows_for_mode(cfg, mode, windows)
        save_client(user_id, cfg)
        await q.answer()
        text = (
            ui_text(cfg, "quiet_hours_deleted").format(window=f"{removed[0]}-{removed[1]}")
            + "\n\n"
            + quiet_hours_management_text(cfg, mode, selected)
        )
        try:
            await q.edit_message_text(text=text, reply_markup=build_mode_quiet_hours_menu(cfg, mode))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_mode_quiet_hours_menu(cfg, mode))
        return

    if data == "ui:schedule:timezone":
        mode = context.user_data.get("active_schedule_mode") or context.user_data.get("awaiting_timezone_mode") or "rss"
        action = "schedule_creative_timezone" if mode == "creative" else "schedule_rss_timezone"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:schedule:{mode}:menu"),
            )
            return
        context.user_data["awaiting_timezone"] = True
        context.user_data["awaiting_timezone_mode"] = mode
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + ui_text(cfg, "timezone_input_instructions")
            + "\n\n"
            + ui_text(cfg, "schedule_timezone").format(timezone=user_timezone_label(cfg))
        )
        return

    if data == "ui:rss:output":
        selected, state = require_channel_context(cfg, context, "rss_output")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_output", "ui:mode:rss:menu"),
            )
            return
        text = selected_channel_text(cfg, selected) + "\n\n" + output_settings_text(cfg, "rss")
        await q.answer()
        try:
            await q.edit_message_text(text=text, reply_markup=build_rss_output_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_rss_output_submenu(cfg))
        return

    if data == "ui:rss:toggle_source_link":
        cfg["include_rss_source_link"] = False
        save_client(user_id, cfg)
        await q.answer()
        text = output_settings_text(cfg, "rss")
        try:
            await q.edit_message_text(text=text, reply_markup=build_rss_output_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_rss_output_submenu(cfg))
        return

    if data == "ui:rss:toggle_feed_image":
        cfg["use_rss_feed_image"] = True
        save_client(user_id, cfg)
        await q.answer()
        text = output_settings_text(cfg, "rss")
        try:
            await q.edit_message_text(text=text, reply_markup=build_rss_output_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_rss_output_submenu(cfg))
        return

    if data == "ui:rss:toggle_cta":
        enabled = not bool(cfg.get("rss_cta_enabled", False))
        cfg["rss_cta_enabled"] = enabled
        if enabled:
            context.user_data["awaiting_rss_cta_text"] = True
            save_client(user_id, cfg)
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "rss_cta_prompt"))
            return
        context.user_data.pop("awaiting_rss_cta_text", None)
        save_client(user_id, cfg)
        await q.answer()
        text = output_settings_text(cfg, "rss")
        try:
            await q.edit_message_text(text=text, reply_markup=build_rss_output_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_rss_output_submenu(cfg))
        return

    if data in ("ui:rss:toggle_bold_title", "ui:creative:toggle_bold_title"):
        mode = "creative" if data.startswith("ui:creative") else "rss"
        key = f"{mode}_bold_title"
        cfg[key] = not bool(cfg.get(key, False))
        save_client(user_id, cfg)
        await q.answer()
        text = ui_text(cfg, "publish_setting_updated") + "\n\n" + output_settings_text(cfg, mode)
        submenu = build_creative_output_submenu(cfg) if mode == "creative" else build_rss_output_submenu(cfg)
        try:
            await q.edit_message_text(text=text, reply_markup=submenu)
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=submenu)
        return

    if data in ("ui:rss:emoji:menu", "ui:creative:emoji:menu"):
        mode = "creative" if data.startswith("ui:creative") else "rss"
        action = "creative_output" if mode == "creative" else "rss_output"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_title"), reply_markup=build_channel_picker(cfg, action, f"ui:mode:{mode}:menu"))
            return
        await q.answer()
        text = selected_channel_text(cfg, selected) + "\n\n" + emoji_management_text(cfg, mode)
        try:
            await q.edit_message_text(text=text, reply_markup=build_emoji_management_submenu(cfg, mode))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_emoji_management_submenu(cfg, mode))
        return

    if data in ("ui:rss:emoji:add", "ui:creative:emoji:add"):
        mode = "creative" if data.startswith("ui:creative") else "rss"
        action = "creative_output" if mode == "creative" else "rss_output"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_title"), reply_markup=build_channel_picker(cfg, action, f"ui:mode:{mode}:menu"))
            return
        context.user_data["awaiting_custom_emoji_mode"] = mode
        context.user_data["awaiting_custom_emoji_channel"] = selected
        await q.answer()
        await q.message.reply_text(ui_text(cfg, "emoji_prompt_send"))
        return

    if data in ("ui:rss:emoji:delete", "ui:creative:emoji:delete"):
        mode = "creative" if data.startswith("ui:creative") else "rss"
        action = "creative_output" if mode == "creative" else "rss_output"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_title"), reply_markup=build_channel_picker(cfg, action, f"ui:mode:{mode}:menu"))
            return
        cfg[f"{mode}_custom_emojis_text"] = ""
        cfg[f"{mode}_custom_emojis_entities"] = []
        cfg[f"{mode}_custom_emojis_link"] = ""
        save_client(user_id, cfg)
        await q.answer()
        text = ui_text(cfg, "emoji_deleted") + "\n\n" + emoji_management_text(cfg, mode)
        submenu = build_emoji_management_submenu(cfg, mode)
        try:
            await q.edit_message_text(text=text, reply_markup=submenu)
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=submenu)
        return

    if data == "ui:creative:output":
        selected, state = require_channel_context(cfg, context, "creative_output")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_output", "ui:mode:creative:menu"),
            )
            return
        text = selected_channel_text(cfg, selected) + "\n\n" + output_settings_text(cfg, "creative")
        await q.answer()
        try:
            await q.edit_message_text(text=text, reply_markup=build_creative_output_submenu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_creative_output_submenu(cfg))
        return

    if data in (
        "ui:rss:asset:template",
        "ui:rss:asset:watermark",
        "ui:creative:asset:template",
        "ui:creative:asset:watermark",
    ):
        mode = "creative" if data.startswith("ui:creative") else "rss"
        asset_type = "watermark" if data.endswith("watermark") else "template"
        action = "creative_output" if mode == "creative" else "rss_output"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:mode:{mode}:menu"),
            )
            return
        await q.answer()
        text = selected_channel_text(cfg, selected) + "\n\n" + asset_management_text(cfg, mode, asset_type)
        submenu = build_asset_management_submenu(cfg, mode, asset_type)
        try:
            await q.edit_message_text(text=text, reply_markup=submenu)
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=submenu)

        asset_file_id = str(cfg.get(f"{mode}_{asset_type}_file_id") or "").strip()
        asset_path = str(cfg.get(f"{mode}_{asset_type}_image_path") or "").strip()
        if asset_file_id:
            try:
                await q.message.reply_photo(photo=asset_file_id)
            except Exception:
                if asset_path:
                    asset_abs = BASE_DIR / asset_path
                    if asset_abs.exists() and asset_abs.is_file():
                        try:
                            with asset_abs.open("rb") as f:
                                await q.message.reply_photo(photo=f)
                        except Exception:
                            pass
        return

    if data in (
        "ui:rss:asset:template:add",
        "ui:rss:asset:watermark:add",
        "ui:creative:asset:template:add",
        "ui:creative:asset:watermark:add",
    ):
        mode = "creative" if data.startswith("ui:creative") else "rss"
        asset_type = "watermark" if ":watermark:" in data else "template"
        action = "creative_output" if mode == "creative" else "rss_output"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:mode:{mode}:menu"),
            )
            return
        context.user_data["awaiting_asset_upload"] = {"mode": mode, "asset": asset_type, "channel": selected}
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + (ui_text(cfg, "asset_prompt_send_watermark") if asset_type == "watermark" else ui_text(cfg, "asset_prompt_send_template"))
        )
        return

    if data in (
        "ui:rss:asset:template:delete",
        "ui:rss:asset:watermark:delete",
        "ui:creative:asset:template:delete",
        "ui:creative:asset:watermark:delete",
    ):
        mode = "creative" if data.startswith("ui:creative") else "rss"
        asset_type = "watermark" if ":watermark:" in data else "template"
        action = "creative_output" if mode == "creative" else "rss_output"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:mode:{mode}:menu"),
            )
            return
        path_key = f"{mode}_{asset_type}_image_path"
        file_key = f"{mode}_{asset_type}_file_id"
        clear_asset_file(str(cfg.get(path_key) or ""))
        cfg[path_key] = ""
        cfg[file_key] = ""
        save_client(user_id, cfg)
        await q.answer()
        notice = ui_text(cfg, "asset_deleted_watermark") if asset_type == "watermark" else ui_text(cfg, "asset_deleted_template")
        text = selected_channel_text(cfg, selected) + "\n\n" + notice + "\n\n" + asset_management_text(cfg, mode, asset_type)
        submenu = build_asset_management_submenu(cfg, mode, asset_type)
        try:
            await q.edit_message_text(text=text, reply_markup=submenu)
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=submenu)
        return

    if data in (
        "ui:rss:add_template_image",
        "ui:rss:add_watermark",
        "ui:creative:add_template_image",
        "ui:creative:add_watermark",
    ):
        mode = "creative" if data.startswith("ui:creative") else "rss"
        asset_type = "watermark" if data.endswith("watermark") else "template"
        action = "creative_output" if mode == "creative" else "rss_output"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:mode:{mode}:menu"),
            )
            return
        context.user_data["awaiting_asset_upload"] = {"mode": mode, "asset": asset_type, "channel": selected}
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + (ui_text(cfg, "asset_prompt_send_watermark") if asset_type == "watermark" else ui_text(cfg, "asset_prompt_send_template"))
        )
        return

    if data in (
        "ui:rss:delete_template_image",
        "ui:rss:delete_watermark",
        "ui:creative:delete_template_image",
        "ui:creative:delete_watermark",
    ):
        mode = "creative" if data.startswith("ui:creative") else "rss"
        asset_type = "watermark" if data.endswith("watermark") else "template"
        action = "creative_output" if mode == "creative" else "rss_output"
        selected, state = require_channel_context(cfg, context, action)
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, action, f"ui:mode:{mode}:menu"),
            )
            return
        path_key = f"{mode}_{asset_type}_image_path"
        file_key = f"{mode}_{asset_type}_file_id"
        clear_asset_file(str(cfg.get(path_key) or ""))
        cfg[path_key] = ""
        cfg[file_key] = ""
        save_client(user_id, cfg)
        await q.answer()
        notice = ui_text(cfg, "asset_deleted_watermark") if asset_type == "watermark" else ui_text(cfg, "asset_deleted_template")
        text = selected_channel_text(cfg, selected) + "\n\n" + notice + "\n\n" + output_settings_text(cfg, mode)
        submenu = build_creative_output_submenu(cfg) if mode == "creative" else build_rss_output_submenu(cfg)
        try:
            await q.edit_message_text(text=text, reply_markup=submenu)
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=submenu)
        return

    if data == "ui:rss:feeds":
        selected, state = require_channel_context(cfg, context, "rss_feeds")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_feeds", "ui:mode:rss:menu"),
            )
            return
        text = feed_management_text(cfg, selected)
        await q.answer()
        try:
            await q.edit_message_text(text=text, reply_markup=build_feed_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_feed_menu(cfg))
        return

    if data == "ui:feedsdelete":
        selected, state = require_channel_context(cfg, context, "rss_feeds")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_feeds", "ui:mode:rss:menu"),
            )
            return
        feeds = cfg.get("feeds", [])
        text = selected_channel_text(cfg, selected) + "\n\n" + feeds_overview(cfg)
        await q.answer()
        if not feeds:
            try:
                await q.edit_message_text(text=text, reply_markup=build_feed_menu(cfg))
            except BadRequest:
                await q.message.reply_text(text=text, reply_markup=build_feed_menu(cfg))
            return
        try:
            await q.edit_message_text(text=text, reply_markup=build_feeds_delete_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_feeds_delete_menu(cfg))
        return

    if data == "ui:creative:buildprompt":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_buildprompt")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_buildprompt", "ui:mode:creative:menu"),
            )
            return
        clear_prompt_interaction_state(context, clear_manual=True, clear_builder=False)
        context.user_data["prompt_builder"] = {"mode": "creative", "step": 0, "answers": {}, "selected_channel": selected}
        await q.answer()
        questions = prompt_builder_questions(cfg, "creative")
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + ui_text(cfg, "prompt_builder_intro_creative")
            + "\n\n"
            + questions[0]
        )
        return

    if data == "ui:rss:buildprompt":
        if not await enforce_mode_paywall(update, cfg, "rss"):
            return
        selected, state = require_channel_context(cfg, context, "rss_buildprompt")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_buildprompt", "ui:mode:rss:menu"),
            )
            return
        clear_prompt_interaction_state(context, clear_manual=True, clear_builder=False)
        context.user_data["prompt_builder"] = {"mode": "rss", "step": 0, "answers": {}, "selected_channel": selected}
        await q.answer()
        questions = prompt_builder_questions(cfg, "rss")
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + ui_text(cfg, "prompt_builder_intro_rss")
            + "\n\n"
            + questions[0]
        )
        return

    if data.startswith("ui:promptbuilder:"):
        parts = data.split(":")
        if len(parts) != 4:
            await q.answer()
            return
        mode = parts[2]
        action = parts[3]
        builder = context.user_data.get("prompt_builder") or {}
        if builder.get("mode") != mode:
            await q.answer()
            return
        if action == "cancel":
            context.user_data.pop("prompt_builder", None)
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "prompt_builder_cancelled"))
            selected_channel = (builder.get("selected_channel") or cfg.get("channel") or "").strip()
            menu_text = creative_menu_text(cfg, selected_channel) if mode == "creative" else ui_text(cfg, "rss_menu_title")
            if selected_channel and mode != "creative":
                menu_text = menu_text + "\n\n" + selected_channel_text(cfg, selected_channel)
            await q.message.reply_text(
                menu_text,
                reply_markup=build_creative_submenu(cfg) if mode == "creative" else build_rss_submenu(cfg),
            )
            return
        if action == "save":
            generated = (builder.get("generated_prompt") or "").strip()
            if not generated:
                await q.answer()
                return
            selected_channel = (builder.get("selected_channel") or "").strip()
            if selected_channel:
                switch_active_channel(cfg, selected_channel)
            set_mode_prompt(cfg, mode, generated)
            save_client(user_id, cfg)
            context.user_data.pop("prompt_builder", None)
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "prompt_builder_saved"))
            menu_text = creative_menu_text(cfg, selected_channel) if mode == "creative" else ui_text(cfg, "rss_menu_title")
            if selected_channel and mode != "creative":
                menu_text = menu_text + "\n\n" + selected_channel_text(cfg, selected_channel)
            await q.message.reply_text(
                menu_text,
                reply_markup=build_creative_submenu(cfg) if mode == "creative" else build_rss_submenu(cfg),
            )
            return
        if action == "regenerate":
            await q.answer()
            try:
                generated = llm_generate_prompt_builder(mode, builder.get("answers") or {})
            except Exception:
                await q.message.reply_text(ui_text(cfg, "prompt_builder_error"))
                return
            builder["generated_prompt"] = generated
            context.user_data["prompt_builder"] = builder
            await q.message.reply_text(
                ui_text(cfg, "prompt_builder_review").format(prompt=generated),
                reply_markup=build_prompt_builder_review(cfg, mode),
            )
            return

    if data.startswith("ui:copystyle:"):
        parts = data.split(":")
        if len(parts) != 4:
            await q.answer()
            return
        mode = parts[2]
        action = parts[3]
        copy_style_review = context.user_data.get("copy_style_review") or {}
        if copy_style_review.get("mode") != mode:
            await q.answer()
            return
        generated = (copy_style_review.get("generated_prompt") or "").strip()
        if not generated:
            await q.answer()
            return
        selected_channel = (copy_style_review.get("selected_channel") or "").strip()
        if selected_channel:
            switch_active_channel(cfg, selected_channel)

        if action == "save":
            set_mode_prompt(cfg, mode, generated)
            save_client(user_id, cfg)
            context.user_data.pop("copy_style_review", None)
            await q.answer()
            menu_text = creative_menu_text(cfg, selected_channel) if mode == "creative" else ui_text(cfg, "rss_menu_title")
            if selected_channel and mode != "creative":
                menu_text = menu_text + "\n\n" + selected_channel_text(cfg, selected_channel)
            await q.message.reply_text(
                ui_text(cfg, "copy_style_success")
                + "\n\n"
                + menu_text,
                reply_markup=build_creative_submenu(cfg) if mode == "creative" else build_rss_submenu(cfg),
            )
            return

        if action == "edit":
            context.user_data.pop("copy_style_review", None)
            clear_prompt_interaction_state(context, clear_manual=False, clear_builder=True)
            context.user_data["awaiting_prompt_mode"] = mode
            context.user_data["awaiting_prompt_channel"] = selected_channel
            await q.answer()
            await q.message.reply_text(
                selected_channel_text(cfg, selected_channel)
                + "\n\n"
                + ui_text(cfg, "copy_style_edit_ready").format(prompt=generated[:1500])
                + "\n\n"
                + ui_text(cfg, "prompt_edit_instructions")
                + "\n"
                + ui_text(cfg, "prompt_edit_cancel_hint")
            )
            return

    if data.startswith("ui:stylemenu:"):
        parts = data.split(":")
        if len(parts) != 4:
            await q.answer()
            return
        mode = parts[2]
        action = parts[3]
        if action != "save" or mode not in ("creative", "rss"):
            await q.answer()
            return
        selected_channel = (context.user_data.get("awaiting_prompt_channel") or "").strip()
        if selected_channel:
            switch_active_channel(cfg, selected_channel)
        current = get_mode_prompt(user_id, cfg, mode).strip()
        if current:
            set_mode_prompt(cfg, mode, current)
            save_client(user_id, cfg)
        await q.answer()
        await q.message.reply_text(
            ui_text(cfg, "style_setup_saved"),
            reply_markup=build_style_setup_submenu(cfg, mode),
        )
        return

    if data == "ui:creative:stylemenu":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_editprompt")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_editprompt", "ui:mode:creative:menu"),
            )
            return
        context.user_data["awaiting_prompt_channel"] = selected
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected) + "\n\n" + style_setup_text(user_id, cfg, "creative"),
            reply_markup=build_style_setup_submenu(cfg, "creative"),
        )
        return

    if data == "ui:rss:stylemenu":
        if not await enforce_mode_paywall(update, cfg, "rss"):
            return
        selected, state = require_channel_context(cfg, context, "rss_editprompt")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_editprompt", "ui:mode:rss:menu"),
            )
            return
        context.user_data["awaiting_prompt_channel"] = selected
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected) + "\n\n" + style_setup_text(user_id, cfg, "rss"),
            reply_markup=build_style_setup_submenu(cfg, "rss"),
        )
        return

    if data == "ui:creative:copystyle":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_copystyle")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_copystyle", "ui:mode:creative:menu"),
            )
            return
        clear_prompt_interaction_state(context, clear_manual=True, clear_builder=True)
        context.user_data["copy_style"] = {"mode": "creative", "selected_channel": selected, "examples": []}
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + ui_text(cfg, "copy_style_intro")
        )
        return

    if data == "ui:rss:copystyle":
        if not await enforce_mode_paywall(update, cfg, "rss"):
            return
        selected, state = require_channel_context(cfg, context, "rss_copystyle")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_copystyle", "ui:mode:rss:menu"),
            )
            return
        clear_prompt_interaction_state(context, clear_manual=True, clear_builder=True)
        context.user_data["copy_style"] = {"mode": "rss", "selected_channel": selected, "examples": []}
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + ui_text(cfg, "copy_style_intro")
        )
        return

    if data == "ui:creative:editprompt":
        if not await enforce_mode_paywall(update, cfg, "creator"):
            return
        selected, state = require_channel_context(cfg, context, "creative_editprompt")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "creative_editprompt", "ui:mode:creative:menu"),
            )
            return
        current = get_mode_prompt(user_id, cfg, "creative").strip()
        current_text = ui_text(cfg, "prompt_current_creative").format(prompt=current[:1500]) if current else ui_text(cfg, "prompt_empty")
        clear_prompt_interaction_state(context, clear_manual=False, clear_builder=True)
        context.user_data["awaiting_prompt_mode"] = "creative"
        context.user_data["awaiting_prompt_channel"] = selected
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + current_text
            + "\n\n"
            + ui_text(cfg, "prompt_edit_instructions")
            + "\n"
            + ui_text(cfg, "prompt_edit_cancel_hint")
        )
        return

    if data == "ui:rss:editprompt":
        if not await enforce_mode_paywall(update, cfg, "rss"):
            return
        selected, state = require_channel_context(cfg, context, "rss_editprompt")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_editprompt", "ui:mode:rss:menu"),
            )
            return
        current = get_mode_prompt(user_id, cfg, "rss").strip()
        current_text = ui_text(cfg, "prompt_current_rss").format(prompt=current[:1500]) if current else ui_text(cfg, "prompt_empty")
        clear_prompt_interaction_state(context, clear_manual=False, clear_builder=True)
        context.user_data["awaiting_prompt_mode"] = "rss"
        context.user_data["awaiting_prompt_channel"] = selected
        await q.answer()
        await q.message.reply_text(
            selected_channel_text(cfg, selected)
            + "\n\n"
            + current_text
            + "\n\n"
            + ui_text(cfg, "prompt_edit_instructions")
            + "\n"
            + ui_text(cfg, "prompt_edit_cancel_hint")
        )
        return

    if data == "ui:setchannel":
        channels = get_saved_channels(cfg)
        slots = int(cfg.get("channel_slots", 0) or 0)
        if len(channels) >= slots:
            text = ui_text(cfg, "channel_slots_limit").format(count=len(channels), slots=slots)
            await q.answer()
            await q.message.reply_text(text)
            return
        context.user_data["awaiting_channel_forward"] = True
        await q.answer()
        await q.message.reply_text(tr(cfg, "ui_setchannel"))
        return

    if data == "ui:addfeed":
        context.user_data["awaiting_feed_add"] = "url"
        context.user_data.pop("pending_feed_url", None)
        logger.info("[ADD_FEED_STATE] user_id=%s state=url", user_id)
        await q.answer()
        await q.message.reply_text(tr(cfg, "ui_addfeed") + "\n\n" + feeds_overview(cfg))
        return

    if data == "ui:unsetchannel":
        channels = get_saved_channels(cfg)
        if not channels:
            text = ui_text(cfg, "channel_management_title") + "\n\n" + channels_overview(cfg)
            await q.answer()
            try:
                await q.edit_message_text(text=text, reply_markup=build_channel_menu(cfg))
            except BadRequest:
                await q.message.reply_text(text=text, reply_markup=build_channel_menu(cfg))
            return

        text = ui_text(cfg, "channel_choose_delete") + "\n\n" + channels_overview(cfg)
        await q.answer()
        try:
            await q.edit_message_text(text=text, reply_markup=build_channel_delete_selection_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_channel_delete_selection_menu(cfg))
        return

    if data.startswith("ui:delchannel:"):
        raw_idx = data.split(":", 2)[2]
        try:
            idx = int(raw_idx) - 1
        except ValueError:
            await q.answer()
            return

        channels = get_saved_channels(cfg)
        if idx < 0 or idx >= len(channels):
            await q.answer()
            return

        removed = channels[idx]
        removed_label = channel_display_name(cfg, removed)
        channels.pop(idx)
        cfg["channels"] = channels
        labels = cfg.get("channel_labels")
        if isinstance(labels, dict):
            labels.pop(removed, None)
            cfg["channel_labels"] = labels
        meta = cfg.get("channel_meta")
        if isinstance(meta, dict):
            meta.pop(removed, None)
            cfg["channel_meta"] = meta
        active_idx = context.user_data.get("active_channel_idx")
        if not channels:
            context.user_data.pop("active_channel_idx", None)
            cfg["channel"] = None
        elif isinstance(active_idx, int) and active_idx >= len(channels):
            context.user_data["active_channel_idx"] = 0

        if channels:
            new_idx = context.user_data.get("active_channel_idx")
            if not isinstance(new_idx, int) or new_idx < 0 or new_idx >= len(channels):
                new_idx = 0
                context.user_data["active_channel_idx"] = 0
            switch_active_channel(cfg, channels[new_idx])
        save_client(user_id, cfg)
        text = (
            ui_text(cfg, "channel_deleted_named").format(channel=removed_label)
            + "\n\n"
            + ui_text(cfg, "channel_management_title")
            + "\n\n"
            + channels_overview(cfg)
        )
        await q.answer()
        try:
            await q.edit_message_text(text=text, reply_markup=build_channel_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_channel_menu(cfg))
        return


    if data.startswith("ui:delfeed:"):
        raw_idx = data.split(":", 2)[2]
        try:
            idx = int(raw_idx) - 1
        except ValueError:
            await send_menu(update, cfg, "Wrong feed index.")
            return

        selected, state = require_channel_context(cfg, context, "rss_feeds")
        if state == "empty":
            await q.answer()
            await q.message.reply_text(ui_text(cfg, "channel_picker_empty"))
            return
        if state == "pick":
            await q.answer()
            await q.message.reply_text(
                ui_text(cfg, "channel_picker_title"),
                reply_markup=build_channel_picker(cfg, "rss_feeds", "ui:mode:rss:menu"),
            )
            return

        feeds = cfg.get("feeds", [])
        if idx < 0 or idx >= len(feeds):
            await send_menu(update, cfg, "Wrong feed index.")
            return

        feeds.pop(idx)
        cfg["feeds"] = feeds
        save_client(user_id, cfg)
        text = ui_text(cfg, "feed_deleted") + "\n\n" + feed_management_text(cfg, selected)
        await q.answer()
        try:
            await q.edit_message_text(text=text, reply_markup=build_feed_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_feed_menu(cfg))
        return

    if data == "ui:backmain":
        await send_menu(update, cfg, tr(cfg, "menu_title"))
        return

    if data == "ui:help":
        await send_menu(update, cfg, build_help_text(cfg))
        return

    if data == "ui:pay":
        await send_menu(update, cfg, tr(cfg, "ui_pay").format(pay=pay_line(update, cfg)))
        return

    if data == "ui:status":
        await status_cmd(update, context)
        return

    await q.answer()

async def setup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    if not cfg.get("language"):
        await update.message.reply_text(ui_text(cfg, "choose_lang"), reply_markup=build_lang_menu())
        return

    clear_mode_channel_selection(context)
    await update.message.reply_text(ui_text(cfg, "setup_menu_title"), reply_markup=build_setup_menu(cfg))

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

    if m == "creator" and not await enforce_mode_paywall(update, cfg, "creator"):
        return
    if m == "rss" and not await enforce_mode_paywall(update, cfg, "rss"):
        return

    cfg["mode"] = m
    save_client(user_id, cfg)
    if m == "rss":
        await update.message.reply_text(ui_text(cfg, "mode_set_rss"))
    elif m == "creator":
        await update.message.reply_text(ui_text(cfg, "mode_set_creator"))
    else:
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

    channels = get_saved_channels(cfg)
    slots = int(cfg.get("channel_slots", 0) or 0)
    if len(channels) >= slots:
        await send_menu(update, cfg, ui_text(cfg, "channel_slots_limit").format(count=len(channels), slots=slots))
        return

    context.user_data["awaiting_channel_forward"] = True
    await update.message.reply_text(tr(cfg, "ui_setchannel"))

async def unsetchannel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    cfg["channel"] = None
    cfg["channels"] = []
    cfg["channel_settings"] = {}
    cfg["channel_labels"] = {}
    cfg["channel_meta"] = {}
    save_client(user_id, cfg)
    context.user_data.pop("active_channel_idx", None)
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
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    awaiting_asset_upload = context.user_data.get("awaiting_asset_upload")
    if awaiting_asset_upload:
        mode = (awaiting_asset_upload.get("mode") or "rss").strip()
        asset_type = (awaiting_asset_upload.get("asset") or "template").strip()
        selected_channel = (awaiting_asset_upload.get("channel") or "").strip()
        if selected_channel:
            switch_active_channel(cfg, selected_channel)

        photo = update.message.photo[-1] if update.message.photo else None
        document = update.message.document
        telegram_file = None
        ext = "jpg"

        if photo:
            telegram_file = photo
            ext = "jpg"
        elif document:
            doc_name = (document.file_name or "").lower()
            doc_ext = doc_name.rsplit(".", 1)[-1] if "." in doc_name else ""
            mime_is_image = (document.mime_type or "").startswith("image/")
            ext_is_image = doc_ext in {"jpg", "jpeg", "png", "webp", "bmp", "gif"}
            if mime_is_image or ext_is_image:
                telegram_file = document
                ext = doc_ext or "png"

        if not telegram_file:
            await update.message.reply_text(ui_text(cfg, "asset_upload_invalid"))
            return

        try:
            file_obj = await context.bot.get_file(telegram_file.file_id)
            target_abs, target_rel = asset_paths(user_id, mode, asset_type, ext)
            target_abs.parent.mkdir(parents=True, exist_ok=True)
            await file_obj.download_to_drive(str(target_abs))
        except Exception:
            await update.message.reply_text(ui_text(cfg, "asset_upload_error"))
            return

        path_key = f"{mode}_{asset_type}_image_path"
        file_key = f"{mode}_{asset_type}_file_id"
        old_path = str(cfg.get(path_key) or "")
        if old_path and old_path != target_rel:
            clear_asset_file(old_path)
        cfg[path_key] = target_rel
        cfg[file_key] = telegram_file.file_id
        save_client(user_id, cfg)
        context.user_data.pop("awaiting_asset_upload", None)

        notice = ui_text(cfg, "asset_saved_watermark") if asset_type == "watermark" else ui_text(cfg, "asset_saved_template")
        menu_text = selected_channel_text(cfg, cfg.get("channel") or selected_channel) + "\n\n" + notice + "\n\n" + output_settings_text(cfg, mode)
        submenu = build_creative_output_submenu(cfg) if mode == "creative" else build_rss_output_submenu(cfg)
        await update.message.reply_text(menu_text, reply_markup=submenu)
        return

    if context.user_data.get("awaiting_channel_forward"):
        channel, channel_meta = _extract_channel_from_forward(update.message)
        if not channel:
            await update.message.reply_text(ui_text(cfg, "channel_forward_invalid"))
            return

        channels = get_saved_channels(cfg)
        slots = int(cfg.get("channel_slots", 0) or 0)
        if channel not in channels and len(channels) >= slots:
            context.user_data.pop("awaiting_channel_forward", None)
            await send_menu(update, cfg, ui_text(cfg, "channel_slots_limit").format(count=len(channels), slots=slots))
            return

        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=context.bot.id)
            if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
                await update.message.reply_text(ui_text(cfg, "channel_forward_admin_missing"))
                return
        except Exception:
            await update.message.reply_text(ui_text(cfg, "channel_forward_access_error"))
            return

        existing_idx = channels.index(channel) if channel in channels else -1
        if existing_idx == -1:
            channels.append(channel)
            existing_idx = len(channels) - 1
        cfg["channels"] = channels
        labels = cfg.get("channel_labels") if isinstance(cfg.get("channel_labels"), dict) else {}
        title = (channel_meta.get("title") or "").strip() if isinstance(channel_meta, dict) else ""
        username = (channel_meta.get("username") or "").strip() if isinstance(channel_meta, dict) else ""
        if title:
            labels[channel] = title
        elif username:
            labels[channel] = username if username.startswith("@") else f"@{username}"
        cfg["channel_labels"] = labels
        meta = cfg.get("channel_meta") if isinstance(cfg.get("channel_meta"), dict) else {}
        existing_meta = meta.get(channel) if isinstance(meta, dict) else {}
        if not isinstance(existing_meta, dict):
            existing_meta = {}
        merged_meta = {
            "username": username or (existing_meta.get("username") or ""),
            "title": title or (existing_meta.get("title") or ""),
        }
        meta[channel] = merged_meta
        cfg["channel_meta"] = meta
        switch_active_channel(cfg, channel)
        ensure_channel_timezone(cfg, channel)
        save_client(user_id, cfg)
        context.user_data["active_channel_idx"] = existing_idx
        context.user_data.pop("awaiting_channel_forward", None)
        await update.message.reply_text(ui_text(cfg, "channel_saved_named").format(channel=channel_display_name(cfg, channel)))
        return

    text = (update.message.text or update.message.caption or "").strip()
    if not text:
        return

    awaiting_campaign_activate = context.user_data.get("awaiting_campaign_activate")
    if awaiting_campaign_activate:
        context.user_data.pop("awaiting_campaign_activate", None)
        try:
            campaign_id = int(text.strip())
        except ValueError:
            await update.message.reply_text(ui_text(cfg, "campaign_activate_invalid"), reply_markup=build_creative_campaigns_submenu(cfg))
            return
        campaigns = creative_campaigns(cfg)
        if not any(item.get("id") == campaign_id for item in campaigns):
            await update.message.reply_text(ui_text(cfg, "campaign_activate_invalid"), reply_markup=build_creative_campaigns_submenu(cfg))
            return
        cfg["creative_active_campaign_id"] = campaign_id
        save_client(user_id, cfg)
        await update.message.reply_text(ui_text(cfg, "campaign_activate_saved"), reply_markup=build_creative_campaigns_submenu(cfg))
        return

    awaiting_campaign_create = context.user_data.get("awaiting_campaign_create")
    if awaiting_campaign_create:
        questions = creative_campaign_questions(cfg)
        step = int(awaiting_campaign_create.get("step", 0))
        answers = awaiting_campaign_create.get("answers") or {}
        normalized = text.lower().strip()
        if normalized == "cancel":
            context.user_data.pop("awaiting_campaign_create", None)
            await update.message.reply_text(ui_text(cfg, "campaign_create_cancelled"), reply_markup=build_creative_campaigns_submenu(cfg))
            return
        if normalized == "resume":
            step = max(0, min(step, len(questions) - 1))
            await update.message.reply_text(_flow_question_prompt(cfg, questions, step))
            return
        if normalized in {"help", "example"}:
            step = max(0, min(step, len(questions) - 1))
            await update.message.reply_text(ui_text(cfg, "flow_help_tip") + "\n\n" + _flow_question_prompt(cfg, questions, step))
            return
        key = questions[step][0]
        if normalized in {"skip", "-"}:
            answers[key] = ""
        else:
            answers[key] = text[:500]
        step += 1
        if step < len(questions):
            context.user_data["awaiting_campaign_create"] = {
                "channel": awaiting_campaign_create.get("channel"),
                "step": step,
                "answers": answers,
            }
            await update.message.reply_text(_flow_question_prompt(cfg, questions, step))
            return
        context.user_data.pop("awaiting_campaign_create", None)
        campaigns = creative_campaigns(cfg)
        campaign = {
            "id": (max([int(item.get('id') or 0) for item in campaigns], default=0) + 1),
            "goal": answers.get("goal", ""),
            "offer": answers.get("offer", ""),
            "duration_days": int(re.sub(r"\\D+", "", answers.get("duration_days", "")) or "7"),
            "target_action": answers.get("target_action", ""),
            "awareness": answers.get("awareness", ""),
            "objections": answers.get("objections", ""),
            "benefits": answers.get("benefits", ""),
            "urgency_context": answers.get("urgency_context", ""),
            "arc": [],
        }
        campaign["duration_days"] = min(max(campaign["duration_days"], 1), 30)
        try:
            campaign["arc"] = llm_generate_campaign_arc(cfg, campaign)
        except Exception:
            logger.exception("Campaign arc generation failed for user %s", user_id)
        campaigns.append(campaign)
        cfg["creative_campaigns"] = campaigns[-30:]
        cfg["creative_active_campaign_id"] = campaign["id"]
        save_client(user_id, cfg)
        lines = [
            ui_text(cfg, "campaign_create_saved"),
            "",
            ui_text(cfg, "campaign_created_for_goal").format(goal=(campaign.get("goal") or ui_text(cfg, "campaign_fallback_goal"))[:140]),
            creative_campaign_arc_readable_text(cfg, campaign),
            "",
            ui_text(cfg, "first_success_next_step_campaign"),
        ]
        await update.message.reply_text("\n".join(lines), reply_markup=build_creative_campaigns_submenu(cfg))
        return

    awaiting_fast_start = context.user_data.get("awaiting_creative_fast_start")
    if awaiting_fast_start:
        questions = creative_fast_start_questions(cfg)
        step = int(awaiting_fast_start.get("step", 0))
        answers = awaiting_fast_start.get("answers") or {}
        normalized = text.lower().strip()
        if normalized == "cancel":
            context.user_data.pop("awaiting_creative_fast_start", None)
            await update.message.reply_text(ui_text(cfg, "quickstart_cancelled"), reply_markup=build_creative_intake_submenu(cfg))
            return
        if normalized == "resume":
            step = max(0, min(step, len(questions) - 1))
            await update.message.reply_text(_flow_question_prompt(cfg, questions, step))
            return
        if normalized in {"help", "example"}:
            step = max(0, min(step, len(questions) - 1))
            await update.message.reply_text(ui_text(cfg, "flow_help_tip") + "\n\n" + _flow_question_prompt(cfg, questions, step))
            return
        key = questions[step][0]
        if normalized in {"skip", "-"}:
            answers[key] = ""
        else:
            answers[key] = text[:700]
        step += 1
        if step < len(questions):
            context.user_data["awaiting_creative_fast_start"] = {
                "channel": awaiting_fast_start.get("channel"),
                "step": step,
                "answers": answers,
            }
            await update.message.reply_text(_flow_question_prompt(cfg, questions, step))
            return
        context.user_data.pop("awaiting_creative_fast_start", None)
        selected_channel = (awaiting_fast_start.get("channel") or "").strip()
        if selected_channel:
            switch_active_channel(cfg, selected_channel)
        quick_intake = cfg.get("creative_channel_intake") if isinstance(cfg.get("creative_channel_intake"), dict) else {}
        quick_intake.update(
            {
                "channel_about": answers.get("channel_about", ""),
                "audience": answers.get("audience", ""),
                "offers": answers.get("offers", ""),
                "creator_goals": answers.get("creator_goals", ""),
            }
        )
        cfg["creative_channel_intake"] = quick_intake
        cfg["creator_profile"] = (
            f"Channel: {answers.get('channel_about','')}\n"
            f"Audience: {answers.get('audience','')}\n"
            f"Offers: {answers.get('offers','')}\n"
            f"Goal: {answers.get('creator_goals','')}"
        )[:1800]
        save_client(user_id, cfg)
        preview = ""
        try:
            preview = creator_make_post(user_id, cfg)
        except Exception:
            logger.exception("Creative quickstart preview failed for user %s", user_id)
        lines = [ui_text(cfg, "quickstart_saved")]
        lines.append(ui_text(cfg, "quickstart_why_post"))
        if preview:
            lines.extend(["", ui_text(cfg, "quickstart_preview_title"), preview[:900]])
        else:
            lines.extend(["", ui_text(cfg, "quickstart_preview_failed")])
        lines.extend(["", ui_text(cfg, "first_success_next_step_quickstart")])
        await update.message.reply_text("\n".join(lines), reply_markup=build_creative_intake_submenu(cfg))
        return

    awaiting_intake = context.user_data.get("awaiting_creative_intake")
    if awaiting_intake:
        questions = creative_channel_intake_questions(cfg)
        step = int(awaiting_intake.get("step", 0))
        answers = awaiting_intake.get("answers") or {}
        normalized = text.lower().strip()
        if normalized == "cancel":
            context.user_data.pop("awaiting_creative_intake", None)
            await update.message.reply_text(ui_text(cfg, "channel_intake_cancelled"), reply_markup=build_creative_intake_submenu(cfg))
            return
        if normalized == "resume":
            step = max(0, min(step, len(questions) - 1))
            await update.message.reply_text(_flow_question_prompt(cfg, questions, step))
            return
        if normalized in {"help", "example"}:
            step = max(0, min(step, len(questions) - 1))
            await update.message.reply_text(ui_text(cfg, "flow_help_tip") + "\n\n" + _flow_question_prompt(cfg, questions, step))
            return
        key = questions[step][0]
        if normalized in {"skip", "-"}:
            answers[key] = ""
        else:
            answers[key] = text[:1200]
        step += 1
        if step < len(questions):
            context.user_data["awaiting_creative_intake"] = {
                "channel": awaiting_intake.get("channel"),
                "step": step,
                "answers": answers,
            }
            await update.message.reply_text(_flow_question_prompt(cfg, questions, step))
            return
        context.user_data.pop("awaiting_creative_intake", None)
        selected_channel = (awaiting_intake.get("channel") or "").strip()
        if selected_channel:
            switch_active_channel(cfg, selected_channel)
        cfg["creative_channel_intake"] = answers
        cfg["creator_profile"] = (
            f"Channel: {answers.get('channel_about','')}\nAudience: {answers.get('audience','')}\n"
            f"Wants: {answers.get('audience_wants','')}\nPains: {answers.get('audience_pains','')}\n"
            f"Tone: {answers.get('tone_style','')}\nOffers: {answers.get('offers','')}\nGoals: {answers.get('creator_goals','')}"
        )[:1800]
        save_client(user_id, cfg)
        await update.message.reply_text(
            ui_text(cfg, "channel_intake_saved") + "\n\n" + creative_intake_summary_text(cfg, selected_channel or (cfg.get("channel") or "")),
            reply_markup=build_creative_intake_submenu(cfg),
        )
        return

    awaiting_prompt_mode = context.user_data.get("awaiting_prompt_mode")
    if awaiting_prompt_mode:
        awaiting_prompt_channel = (context.user_data.pop("awaiting_prompt_channel", None) or "").strip()
        context.user_data.pop("awaiting_prompt_mode", None)
        if text.lower() == "cancel":
            await send_prompt_parent_menu(update, cfg, awaiting_prompt_mode, ui_text(cfg, "prompt_edit_cancelled"))
            return
        if awaiting_prompt_channel:
            switch_active_channel(cfg, awaiting_prompt_channel)
        set_mode_prompt(cfg, awaiting_prompt_mode, text)
        save_client(user_id, cfg)
        await send_prompt_parent_menu(update, cfg, awaiting_prompt_mode, ui_text(cfg, "prompt_edit_saved"))
        return

    awaiting_content_plan_edit = context.user_data.get("awaiting_content_plan_edit")
    if awaiting_content_plan_edit:
        context.user_data.pop("awaiting_content_plan_edit", None)
        if text.lower() == "cancel":
            await update.message.reply_text(
                ui_text(cfg, "content_plan_edit_cancelled"),
                reply_markup=build_creative_content_plan_submenu(cfg),
            )
            return
        selected_channel = (awaiting_content_plan_edit.get("channel") or "").strip()
        if selected_channel:
            switch_active_channel(cfg, selected_channel)
        idx = int(awaiting_content_plan_edit.get("idx", -1))
        items = creative_content_plan(cfg)
        if idx < 0 or idx >= len(items):
            await update.message.reply_text(
                ui_text(cfg, "content_plan_no_plan"),
                reply_markup=build_creative_content_plan_submenu(cfg),
            )
            return
        items[idx]["topic"] = text[:140]
        cfg["creative_content_plan"] = items
        save_client(user_id, cfg)
        await update.message.reply_text(
            ui_text(cfg, "content_plan_item_saved"),
            reply_markup=build_creative_content_plan_submenu(cfg),
        )
        return

    awaiting_source_add = context.user_data.get("awaiting_creative_source_add")
    if awaiting_source_add:
        if text.lower() == "cancel":
            context.user_data.pop("awaiting_creative_source_add", None)
            await update.message.reply_text(ui_text(cfg, "source_add_cancelled"))
            return
        context.user_data.pop("awaiting_creative_source_add", None)
        selected_channel = (awaiting_source_add.get("channel") or "").strip()
        if selected_channel:
            switch_active_channel(cfg, selected_channel)
        source_type = str(awaiting_source_add.get("source_type") or "").strip()
        meta = CREATIVE_SOURCE_META.get(source_type)
        if not meta:
            await update.message.reply_text(ui_text(cfg, "prompt_builder_error"))
            return
        items = creative_source_items(cfg, meta["key"])
        items.append(text[:400])
        cfg[meta["key"]] = items[-100:]
        save_client(user_id, cfg)
        await update.message.reply_text(
            ui_text(cfg, meta["saved_key"]),
            reply_markup=build_creative_source_list_submenu(cfg, source_type),
        )
        return

    if context.user_data.get("awaiting_rss_cta_text"):
        context.user_data.pop("awaiting_rss_cta_text", None)
        cfg["rss_cta_text"] = text
        cfg["rss_cta_entities"] = [_message_entity_to_dict(entity) for entity in (update.message.entities or [])]
        save_client(user_id, cfg)
        await update.message.reply_text(
            ui_text(cfg, "rss_cta_saved") + "\n\n" + output_settings_text(cfg, "rss"),
            reply_markup=build_rss_output_submenu(cfg),
        )
        return

    awaiting_custom_emoji_mode = context.user_data.get("awaiting_custom_emoji_mode")
    if awaiting_custom_emoji_mode:
        context.user_data.pop("awaiting_custom_emoji_mode", None)
        selected_channel = (context.user_data.pop("awaiting_custom_emoji_channel", None) or "").strip()
        if selected_channel:
            switch_active_channel(cfg, selected_channel)
        if _looks_like_link(text):
            cfg[f"{awaiting_custom_emoji_mode}_custom_emojis_link"] = text
        else:
            cfg[f"{awaiting_custom_emoji_mode}_custom_emojis_text"] = text
            cfg[f"{awaiting_custom_emoji_mode}_custom_emojis_entities"] = [_message_entity_to_dict(entity) for entity in (update.message.entities or [])]
        save_client(user_id, cfg)
        submenu = build_emoji_management_submenu(cfg, awaiting_custom_emoji_mode)
        await update.message.reply_text(ui_text(cfg, "emoji_saved") + "\n\n" + emoji_management_text(cfg, awaiting_custom_emoji_mode), reply_markup=submenu)
        return

    prompt_builder = context.user_data.get("prompt_builder")
    if prompt_builder:
        mode = prompt_builder.get("mode")
        if text.lower() == "cancel":
            context.user_data.pop("prompt_builder", None)
            await update.message.reply_text(
                ui_text(cfg, "prompt_builder_cancelled")
                + "\n\n"
                + (creative_menu_text(cfg, cfg.get("channel") or "—") if mode == "creative" else ui_text(cfg, "rss_menu_title")),
                reply_markup=build_creative_submenu(cfg) if mode == "creative" else build_rss_submenu(cfg),
            )
            return

        step = int(prompt_builder.get("step", 0))
        answers = prompt_builder.get("answers") or {}
        answers[f"q{step + 1}"] = text
        prompt_builder["answers"] = answers
        questions = prompt_builder_questions(cfg, mode)

        if step + 1 < len(questions):
            prompt_builder["step"] = step + 1
            context.user_data["prompt_builder"] = prompt_builder
            await update.message.reply_text(questions[step + 1])
            return

        await update.message.reply_text(ui_text(cfg, "prompt_builder_generating"))
        try:
            generated = llm_generate_prompt_builder(mode, answers)
        except Exception:
            context.user_data.pop("prompt_builder", None)
            await update.message.reply_text(ui_text(cfg, "prompt_builder_error"))
            return
        prompt_builder["generated_prompt"] = generated
        context.user_data["prompt_builder"] = prompt_builder
        await update.message.reply_text(
            ui_text(cfg, "prompt_builder_review").format(prompt=generated),
            reply_markup=build_prompt_builder_review(cfg, mode),
        )
        return

    copy_style = context.user_data.get("copy_style")
    if copy_style:
        example_text = (update.message.text or update.message.caption or "").strip()
        if not example_text:
            await update.message.reply_text(ui_text(cfg, "copy_style_invalid"))
            return

        examples = copy_style.get("examples") or []
        examples.append(example_text)
        copy_style["examples"] = examples

        left = 3 - len(examples)
        if left > 0:
            context.user_data["copy_style"] = copy_style
            suffix = "" if ((cfg.get("language") or "en").lower() == "ru" and left == 1) else "а"
            await update.message.reply_text(ui_text(cfg, "copy_style_progress").format(left=left, suffix=suffix))
            return

        context.user_data.pop("copy_style", None)
        mode = copy_style.get("mode") or "rss"
        selected_channel = (copy_style.get("selected_channel") or "").strip()
        if selected_channel:
            switch_active_channel(cfg, selected_channel)

        await update.message.reply_text(ui_text(cfg, "copy_style_loading"))
        try:
            requested_language = "Russian" if (cfg.get("language") or "en") == "ru" else "English"
            generated = llm_generate_style_prompt_from_examples(mode, examples[:3], requested_language)
        except Exception:
            await update.message.reply_text(ui_text(cfg, "prompt_builder_error"))
            return

        context.user_data["copy_style_review"] = {
            "mode": mode,
            "selected_channel": selected_channel,
            "generated_prompt": generated,
        }
        await update.message.reply_text(
            ui_text(cfg, "copy_style_review").format(prompt=generated),
            reply_markup=build_copy_style_review(cfg, mode),
        )
        return


    awaiting_schedule_mode = context.user_data.get("awaiting_schedule_mode")
    if awaiting_schedule_mode:
        if text.lower() == "cancel":
            context.user_data.pop("awaiting_schedule_mode", None)
            await update.message.reply_text(
                schedule_mode_menu_text(cfg, awaiting_schedule_mode),
                reply_markup=build_mode_schedule_submenu(cfg, awaiting_schedule_mode),
            )
            return

        if text.lower() == "clear":
            if awaiting_schedule_mode == "creative":
                cfg["creative_schedule_times"] = []
                cfg["creative_last_schedule_date"] = None
                cfg["creative_last_schedule_time"] = None
            else:
                cfg["rss_schedule_times"] = []
                cfg["rss_last_schedule_date"] = None
                cfg["rss_last_schedule_time"] = None
            save_client(user_id, cfg)
            context.user_data.pop("awaiting_schedule_mode", None)
            await update.message.reply_text(
                ui_text(cfg, "schedule_cleared") + "\n\n" + schedule_mode_menu_text(cfg, awaiting_schedule_mode),
                reply_markup=build_mode_schedule_submenu(cfg, awaiting_schedule_mode),
            )
            return

        parsed = parse_schedule_input(text)
        if not parsed:
            await update.message.reply_text(ui_text(cfg, "schedule_invalid"))
            return

        if awaiting_schedule_mode == "creative":
            cfg["creative_schedule_times"] = parsed
        else:
            cfg["rss_schedule_times"] = parsed
        save_client(user_id, cfg)
        context.user_data.pop("awaiting_schedule_mode", None)
        await update.message.reply_text(
            ui_text(cfg, "schedule_saved") + "\n\n" + schedule_mode_menu_text(cfg, awaiting_schedule_mode),
            reply_markup=build_mode_schedule_submenu(cfg, awaiting_schedule_mode),
        )
        return

    awaiting_interval_mode = context.user_data.get("awaiting_interval_mode")
    if awaiting_interval_mode:
        if text.lower() == "cancel":
            context.user_data.pop("awaiting_interval_mode", None)
            await update.message.reply_text(
                schedule_mode_menu_text(cfg, awaiting_interval_mode),
                reply_markup=build_mode_schedule_submenu(cfg, awaiting_interval_mode),
            )
            return
        if not text.isdigit():
            await update.message.reply_text(ui_text(cfg, "interval_invalid"))
            return
        minutes = int(text)
        if minutes < 1:
            await update.message.reply_text(ui_text(cfg, "interval_invalid"))
            return
        cfg["interval_minutes"] = minutes
        cfg[f"{awaiting_interval_mode}_use_interval"] = True
        _schedule_next_interval_run(cfg, awaiting_interval_mode, user_now(cfg))
        save_client(user_id, cfg)
        context.user_data.pop("awaiting_interval_mode", None)
        await update.message.reply_text(
            ui_text(cfg, "interval_saved").format(interval=minutes) + "\n\n" + schedule_mode_menu_text(cfg, awaiting_interval_mode),
            reply_markup=build_mode_schedule_submenu(cfg, awaiting_interval_mode),
        )
        return

    awaiting_quiet_mode = context.user_data.get("awaiting_quiet_mode")
    if awaiting_quiet_mode:
        selected = cfg.get("channel") or ""
        if text.lower() == "cancel":
            context.user_data.pop("awaiting_quiet_mode", None)
            await update.message.reply_text(
                quiet_hours_management_text(cfg, awaiting_quiet_mode, selected),
                reply_markup=build_mode_quiet_hours_menu(cfg, awaiting_quiet_mode),
            )
            return
        quiet_match = re.fullmatch(r"\s*(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})\s*", text)
        if not quiet_match or not _parse_hhmm(quiet_match.group(1)) or not _parse_hhmm(quiet_match.group(2)):
            await update.message.reply_text(ui_text(cfg, "quiet_hours_invalid"))
            return
        start = quiet_match.group(1)
        end = quiet_match.group(2)
        if start == end:
            await update.message.reply_text(ui_text(cfg, "quiet_hours_invalid"))
            return
        windows = quiet_windows_for_mode(cfg, awaiting_quiet_mode)
        windows.append((start, end))
        set_quiet_windows_for_mode(cfg, awaiting_quiet_mode, windows)
        save_client(user_id, cfg)
        context.user_data.pop("awaiting_quiet_mode", None)
        await update.message.reply_text(
            ui_text(cfg, "quiet_hours_saved").format(start=start, end=end) + "\n\n" + quiet_hours_management_text(cfg, awaiting_quiet_mode, selected),
            reply_markup=build_mode_quiet_hours_menu(cfg, awaiting_quiet_mode),
        )
        return

    awaiting_freshness_mode = context.user_data.get("awaiting_freshness_mode")
    if awaiting_freshness_mode:
        if text.lower() == "cancel":
            context.user_data.pop("awaiting_freshness_mode", None)
            await update.message.reply_text(
                schedule_mode_menu_text(cfg, awaiting_freshness_mode),
                reply_markup=build_mode_schedule_submenu(cfg, awaiting_freshness_mode),
            )
            return
        if not text.isdigit():
            await update.message.reply_text(ui_text(cfg, "freshness_invalid"))
            return
        minutes = int(text)
        if minutes < 15 or minutes > 1440:
            await update.message.reply_text(ui_text(cfg, "freshness_invalid"))
            return
        cfg["rss_freshness_minutes"] = minutes
        context.user_data.pop("awaiting_freshness_mode", None)
        save_client(user_id, cfg)
        await update.message.reply_text(
            ui_text(cfg, "freshness_saved").format(minutes=minutes) + "\n\n" + schedule_mode_menu_text(cfg, awaiting_freshness_mode),
            reply_markup=build_mode_schedule_submenu(cfg, awaiting_freshness_mode),
        )
        return

    if context.user_data.get("awaiting_timezone"):
        if text.lower() == "cancel":
            context.user_data.pop("awaiting_timezone", None)
            context.user_data.pop("awaiting_timezone_mode", None)
            await update.message.reply_text(ui_text(cfg, "schedule_timezone").format(timezone=user_timezone_label(cfg)))
            return
        offset = parse_timezone_offset_hours(text)
        if offset is None:
            await update.message.reply_text(ui_text(cfg, "timezone_invalid"))
            return
        cfg["channel_timezone_offset_hours"] = offset
        save_client(user_id, cfg)
        context.user_data.pop("awaiting_timezone", None)
        context.user_data.pop("awaiting_timezone_mode", None)
        logger.info("[CHANNEL_TIMEZONE] action=manual_set value=%s channel=%s", offset, cfg.get("channel"))
        await update.message.reply_text(ui_text(cfg, "timezone_saved").format(timezone=user_timezone_label(cfg)))
        return

    if context.user_data.get("awaiting_feed_add"):
        stage = context.user_data.get("awaiting_feed_add")
        if stage == "name":
            context.user_data.pop("awaiting_feed_add", None)
            url = context.user_data.pop("pending_feed_url", "").strip()
            if not url:
                await send_menu(update, cfg, "Feed add was canceled. Please add feed again.")
                return
            feed_name = "" if text == "-" else text
            feeds = cfg.get("feeds", [])
            if _find_feed_by_url(feeds, url):
                await send_menu(update, cfg, ui_text(cfg, "feed_duplicate"))
                return
            limit = feed_limit_per_channel(cfg)
            if len(feeds) >= limit:
                await send_menu(update, cfg, ui_text(cfg, "feed_limit_reached").format(limit=limit))
                return
            first_feed_added = len(feeds) == 0
            feeds.append({"url": url, "name": feed_name} if feed_name else url)
            cfg["feeds"] = feeds
            save_client(user_id, cfg)
            selected, state = require_channel_context(cfg, context, "rss_feeds")
            orientation = ui_text(cfg, "rss_first_success_feed")
            if selected and state is None:
                await update.message.reply_text(
                    ui_text(cfg, "feed_added") + "\n\n" + feed_management_text(cfg, selected) + ("\n\n" + orientation if first_feed_added else ""),
                    reply_markup=build_feed_menu(cfg),
                )
            else:
                await send_menu(update, cfg, ui_text(cfg, "feed_added") + "\n\n" + feeds_overview(cfg) + ("\n\n" + orientation if first_feed_added else ""))
            return

        logger.info("[ADD_FEED_TEXT] user_id=%s text=%s", user_id, text.strip())
        try:
            await process_feed_input(update, context, cfg, user_id, text, from_plain_text=True)
        except Exception as exc:
            logger.exception("[ADD_FEED_ERROR] user_id=%s stage=url error=%s", user_id, exc)
            context.user_data.pop("awaiting_feed_add", None)
            await update.message.reply_text(ui_text(cfg, "feed_read_failed"))
        return

    state = context.user_data.get("style_wizard")
    if not state:
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
        await update.message.reply_text("Usage: /addfeed [your link]")
        return

    try:
        await process_feed_input(update, context, cfg, user_id, context.args[0], from_plain_text=False)
    except Exception as exc:
        logger.exception("[ADD_FEED_ERROR] user_id=%s source=command error=%s", user_id, exc)
        await update.message.reply_text(ui_text(cfg, "feed_read_failed"))

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
            await q.edit_message_text(text=text, reply_markup=build_feed_menu(cfg))
        except BadRequest:
            await q.message.reply_text(text=text, reply_markup=build_feed_menu(cfg))
        return

    await update.message.reply_text(text, reply_markup=build_feed_menu(cfg))
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
    removed_url = _feed_url(removed)
    removed_name = _feed_name(removed)
    removed_display = f"{removed_name} — {removed_url}" if removed_name else removed_url
    cfg["feeds"] = feeds
    save_client(user_id, cfg)
    await send_menu(update, cfg, f"✅ Deleted feed:\n{removed_display}\n\n{feeds_overview(cfg)}")

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
        save_client(user_id, cfg)
        creator_entities = apply_bold_title(msg, []) if bool(cfg.get("creative_bold_title", False)) else []
        preview_prefix = "🧪 Preview:\n\n"
        await update.message.reply_text(preview_prefix + msg, entities=_load_message_entities([_message_entity_to_dict(e) for e in creator_entities], offset_shift=len(preview_prefix)) or None, reply_markup=build_main_menu_clean(cfg))
        diagnostics = creative_preview_diagnostics_text(cfg)
        if diagnostics:
            await update.message.reply_text(diagnostics, reply_markup=build_main_menu_clean(cfg))
        return

    feeds = cfg.get("feeds", [])

    if mode == "both":
        creator_msg = creator_make_post(user_id, cfg)
        save_client(user_id, cfg)
        if not feeds:
            creator_entities = apply_bold_title(creator_msg, []) if bool(cfg.get("creative_bold_title", False)) else []
            await update.message.reply_text("🧪 Preview (creator):\n\n" + creator_msg, entities=_load_message_entities([_message_entity_to_dict(e) for e in creator_entities], offset_shift=len("🧪 Preview (creator):\n\n")) or None, reply_markup=build_main_menu_clean(cfg))
            return
        best = pick_newest_unseen(cfg)
        if not best:
            creator_entities = apply_bold_title(creator_msg, []) if bool(cfg.get("creative_bold_title", False)) else []
            await update.message.reply_text("🧪 Preview (creator):\n\n" + creator_msg, entities=_load_message_entities([_message_entity_to_dict(e) for e in creator_entities], offset_shift=len("🧪 Preview (creator):\n\n")) or None, reply_markup=build_main_menu_clean(cfg))
            return
        _, title, link, src = best
        summary, source_context, weak_context, social_source = build_rss_generation_input(src, link, title)
        rss_msg = llm_generate_post(user_id, cfg, title, summary, link, source_context, weak_context, social_source)
        rss_preview = format_rss_message(cfg, rss_msg, link)
        await reply_ui(update, "🧪 Preview (RSS):\n\n" + rss_preview + "\n\n————\n🧪 Preview (Creator):\n\n" + creator_msg, cfg, show_menu=True)
        return

    if not feeds:
        await reply_ui(update, ui_text(cfg, "preview_empty_no_feed"), cfg, show_menu=True)
        return

    best = pick_newest_unseen(cfg)
    if not best:
        await reply_ui(update, preview_empty_state_text(cfg), cfg, show_menu=True)
        return

    preview, image_url, preview_entities, _ = await rss_preview_text(context.bot, user_id, cfg)
    send_image_url, temp_file, preview_notice_key = await prepare_rss_preview_image_for_sending(context.bot, cfg, user_id, image_url)
    try:
        if preview_notice_key and update.message:
            await update.message.reply_text(ui_text(cfg, preview_notice_key))
        if send_image_url and update.message:
            caption_entities = _load_message_entities([_message_entity_to_dict(e) for e in preview_entities], max_offset=1024)
            photo_input = temp_file if temp_file else send_image_url
            await update.message.reply_photo(photo=photo_input, caption=preview[:1024], caption_entities=caption_entities or None, reply_markup=build_main_menu_clean(cfg))
            return
        if update.message:
            await update.message.reply_text(preview, entities=preview_entities or None, reply_markup=build_main_menu_clean(cfg))
            return
        await reply_ui(update, preview, cfg, show_menu=True)
    finally:
        if temp_file:
            try:
                temp_file.unlink(missing_ok=True)
            except Exception:
                pass

async def fetchonce_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)

    mode = cfg.get("mode")
    required_mode = "creator" if mode == "creator" else "rss"
    if not mode_access_allowed(cfg, required_mode):
        await reply_ui(update, mode_paywall_text(cfg, required_mode), cfg, show_menu=True)
        return

    if not can_post_more(cfg, required_mode):
        await reply_ui(update, ui_text(cfg, "posting_limit_reached"), cfg, show_menu=True)
        return

    channel = cfg.get("channel")
    if not channel:
        await reply_ui(update, "Channel not set. Use /setchannel @channelusername", cfg, show_menu=True)
        return

    mode = cfg.get("mode")
    feeds = cfg.get("feeds", [])

    if mode == "creator":
        msg = creator_make_post(user_id, cfg)
        creator_entities = apply_bold_title(msg, []) if bool(cfg.get("creative_bold_title", False)) else []
        await context.bot.send_message(chat_id=channel, text=msg, entities=creator_entities or None)
        bump_daily_count(cfg, "creator")
        save_client(user_id, cfg)
        await reply_ui(update, "✅ Posted 1 creator post.", cfg, show_menu=True)
        return

    if mode == "both":
        best = pick_newest_unseen(cfg) if feeds else None
        if best:
            published, title, link, src = best
            summary, source_context, weak_context, social_source = build_rss_generation_input(src, link, title)
            msg = llm_generate_post(user_id, cfg, title, summary, link, source_context, weak_context, social_source)
            image_url = extract_image_url_for_link(src, link)
            send_image_url, temp_file = await prepare_rss_image_for_sending(context.bot, cfg, user_id, image_url)
            await send_rss_to_channel(context.bot, cfg, channel, msg, link, send_image_url, temp_file)
            _record_posted_rss_item(cfg, link, title, src, published)
            bump_daily_count(cfg, "rss")
            save_client(user_id, cfg)
            await reply_ui(update, "✅ Posted 1 RSS item (both mode).", cfg, show_menu=True)
            return

        msg = creator_make_post(user_id, cfg)
        creator_entities = apply_bold_title(msg, []) if bool(cfg.get("creative_bold_title", False)) else []
        await context.bot.send_message(chat_id=channel, text=msg, entities=creator_entities or None)
        bump_daily_count(cfg, "creator")
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

    published, title, link, src = best
    summary, source_context, weak_context, social_source = build_rss_generation_input(src, link, title)
    msg = llm_generate_post(user_id, cfg, title, summary, link, source_context, weak_context, social_source)
    image_url = extract_image_url_for_link(src, link)
    send_image_url, temp_file = await prepare_rss_image_for_sending(context.bot, cfg, user_id, image_url)

    await send_rss_to_channel(context.bot, cfg, channel, msg, link, send_image_url, temp_file)

    _record_posted_rss_item(cfg, link, title, src, published)
    bump_daily_count(cfg, "rss")
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
    for _m in ("rss", "creative"):
        if mode_uses_interval(cfg, _m):
            _schedule_next_interval_run(cfg, _m, user_now(cfg))
    save_client(user_id, cfg)
    await update.message.reply_text(f"⏱ Interval saved: {minutes} min.")

async def autoposton_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    mode = (cfg.get("mode") or "rss").strip().lower()
    activation_mode = "creative" if mode == "creator" else ("rss" if mode == "rss" else "both")
    ok, notice = activate_posting(cfg, activation_mode, turn_on=True)
    if not ok:
        await reply_ui(update, notice, cfg, show_menu=True)
        return
    save_client(user_id, cfg)
    await reply_ui(update, notice, cfg, show_menu=True)

async def autopostoff_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cfg = load_client(user_id)
    mode = (cfg.get("mode") or "rss").strip().lower()
    activation_mode = "creative" if mode == "creator" else ("rss" if mode == "rss" else "both")
    _, notice = activate_posting(cfg, activation_mode, turn_on=False)
    save_client(user_id, cfg)
    await reply_ui(update, notice, cfg, show_menu=True)

# ===================== Admin commands =====================
async def setrss_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if not is_admin(caller):
        await update.message.reply_text(tr(load_client(caller), "admin_only"))
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setrss <user_id> <posts_per_day> [days]")
        return

    uid_raw, limit_raw = context.args[0].strip(), context.args[1].strip()
    if not uid_raw.isdigit() or not limit_raw.isdigit():
        await update.message.reply_text("Usage: /setrss <user_id> <posts_per_day> [days]")
        return

    uid = int(uid_raw)
    limit = int(limit_raw)
    if limit < 0 or limit > 5000:
        await update.message.reply_text("posts_per_day range: 0..5000")
        return

    expires_text = "unchanged"
    cfg = load_client(uid)
    cfg["rss_daily_limit"] = limit
    if len(context.args) >= 3:
        days_raw = context.args[2].strip()
        if not days_raw.isdigit():
            await update.message.reply_text("Usage: /setrss <user_id> <posts_per_day> [days]")
            return
        days = int(days_raw)
        if days == 0:
            cfg["subscription_until"] = None
            expires_text = "INACTIVE"
        elif 1 <= days <= 3650:
            cfg["subscription_until"] = str(date.today() + timedelta(days=days))
            expires_text = cfg["subscription_until"]
        else:
            await update.message.reply_text("days range: 0..3650")
            return
    save_client(uid, cfg)
    await update.message.reply_text(
        "✅ Access updated\n"
        f"user_id: {uid}\n"
        f"mode: RSS + AI\n"
        f"daily_limit: {limit}\n"
        f"expires: {expires_text}"
    )


async def setcreative_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if not is_admin(caller):
        await update.message.reply_text(tr(load_client(caller), "admin_only"))
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setcreative <user_id> <posts_per_month> [days]")
        return

    uid_raw, limit_raw = context.args[0].strip(), context.args[1].strip()
    if not uid_raw.isdigit() or not limit_raw.isdigit():
        await update.message.reply_text("Usage: /setcreative <user_id> <posts_per_month> [days]")
        return

    uid = int(uid_raw)
    limit = int(limit_raw)
    if limit < 0 or limit > 5000:
        await update.message.reply_text("posts_per_month range: 0..5000")
        return

    expires_text = "unchanged"
    cfg = load_client(uid)
    cfg["creative_monthly_limit"] = limit
    if len(context.args) >= 3:
        days_raw = context.args[2].strip()
        if not days_raw.isdigit():
            await update.message.reply_text("Usage: /setcreative <user_id> <posts_per_month> [days]")
            return
        days = int(days_raw)
        if days == 0:
            cfg["subscription_until"] = None
            expires_text = "INACTIVE"
        elif 1 <= days <= 3650:
            cfg["subscription_until"] = str(date.today() + timedelta(days=days))
            expires_text = cfg["subscription_until"]
        else:
            await update.message.reply_text("days range: 0..3650")
            return
    save_client(uid, cfg)
    await update.message.reply_text(
        "✅ Access updated\n"
        f"user_id: {uid}\n"
        f"mode: Creative\n"
        f"monthly_limit: {limit}\n"
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
    if limit < 0 or limit > 5000:
        await update.message.reply_text("Limit range: 0..5000")
        return

    cfg = load_client(uid)
    cfg["daily_limit"] = limit
    save_client(uid, cfg)
    await update.message.reply_text(f"✅ User {uid} daily_limit set to {limit}")

async def setchannels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if not is_admin(caller):
        await update.message.reply_text(tr(load_client(caller), "admin_only"))
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setchannels <user_id> <count> [days]")
        return

    uid_raw, count_raw = context.args[0].strip(), context.args[1].strip()
    if not uid_raw.isdigit() or not count_raw.isdigit():
        await update.message.reply_text("Usage: /setchannels <user_id> <count> [days]")
        return

    uid = int(uid_raw)
    count = int(count_raw)
    if count < 0 or count > 5000:
        await update.message.reply_text("count range: 0..5000")
        return

    expires_text = "unchanged"
    cfg = load_client(uid)
    cfg["channel_slots"] = count
    if len(context.args) >= 3:
        days_raw = context.args[2].strip()
        if not days_raw.isdigit():
            await update.message.reply_text("Usage: /setchannels <user_id> <count> [days]")
            return
        days = int(days_raw)
        if days == 0:
            cfg["subscription_until"] = None
            expires_text = "INACTIVE"
        elif 1 <= days <= 3650:
            cfg["subscription_until"] = str(date.today() + timedelta(days=days))
            expires_text = cfg["subscription_until"]
        else:
            await update.message.reply_text("days range: 0..3650")
            return

    save_client(uid, cfg)
    await update.message.reply_text(
        "✅ Channel slots updated\n"
        f"user_id: {uid}\n"
        f"channel_slots: {count}\n"
        f"expires: {expires_text}"
    )


async def setfeedlimit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user.id
    if not is_admin(caller):
        await update.message.reply_text(tr(load_client(caller), "admin_only"))
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setfeedlimit <user_id> <count>")
        return

    uid_raw, count_raw = context.args[0].strip(), context.args[1].strip()
    if not uid_raw.isdigit() or not count_raw.isdigit():
        await update.message.reply_text("Usage: /setfeedlimit <user_id> <count>")
        return

    uid = int(uid_raw)
    count = int(count_raw)
    if count < 1 or count > 100:
        await update.message.reply_text("count range: 1..100")
        return

    cfg = load_client(uid)
    cfg["feed_limit_per_channel"] = count
    channel_settings = cfg.get("channel_settings")
    if isinstance(channel_settings, dict):
        for channel_key, bucket in channel_settings.items():
            if isinstance(channel_key, str) and isinstance(bucket, dict):
                bucket["feed_limit_per_channel"] = count
    save_client(uid, cfg)
    await update.message.reply_text(f"✅ User {uid} feed_limit_per_channel set to {count}")


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
    for _m in ("rss", "creative"):
        if mode_uses_interval(cfg, _m):
            _schedule_next_interval_run(cfg, _m, user_now(cfg))
    save_client(uid, cfg)
    await update.message.reply_text(f"✅ User {uid} interval set to {minutes} minutes")

# ===================== Autopost loop =====================
async def autopost_loop(app: Application) -> None:
    last_post_at: dict[tuple[int, str, str], datetime] = {}
    last_diag_at: dict[tuple[int, str], datetime] = {}

    def should_log_diag(uid: int, reason: str, now: datetime, cooldown_minutes: int = 30) -> bool:
        key = (uid, reason)
        prev = last_diag_at.get(key)
        if prev and now - prev < timedelta(minutes=cooldown_minutes):
            return False
        last_diag_at[key] = now
        return True

    while True:
        try:
            ensure_dirs()

            for p in CLIENTS_DIR.glob("*.json"):
                try:
                    user_id = int(p.stem)
                except Exception:
                    continue

                cfg = load_client(user_id)

                mode = cfg.get("mode")
                required_mode = "creator" if mode == "creator" else "rss"
                if not mode_access_allowed(cfg, required_mode):
                    continue

                channels = get_saved_channels(cfg)
                if not channels:
                    continue

                for channel in channels:
                    switch_active_channel(cfg, channel)
                    ensure_channel_timezone(cfg, channel)
                    now = user_now(cfg)
                    if not can_post_more(cfg, required_mode):
                        continue
                    feeds = cfg.get("feeds", [])

                    if mode == "creator":
                        if not mode_autopost_enabled(cfg, "creative"):
                            continue
                        if not should_run_mode_now(cfg, "creative", now, last_post_at, user_id, channel):
                            continue
                        msg = creator_make_post(user_id, cfg)
                        creator_entities = apply_bold_title(msg, []) if bool(cfg.get("creative_bold_title", False)) else []
                        await app.bot.send_message(chat_id=channel, text=msg, entities=creator_entities or None)
                        bump_daily_count(cfg, "creator")
                        mark_mode_scheduled(cfg, "creative", now)
                        save_client(user_id, cfg)
                        last_post_at[(user_id, channel, "creative")] = now
                        continue

                    merged_candidates = collect_rss_candidates(cfg) if feeds else []
                    rss_enabled = mode_autopost_enabled(cfg, "rss")
                    rss_paused = rss_posting_paused(cfg)
                    creative_enabled = mode_autopost_enabled(cfg, "creative")

                    if mode == "both" and not merged_candidates and not _queue_items(cfg):
                        if not creative_enabled:
                            continue
                        if should_log_diag(user_id, "no_fresh_rss_items", now):
                            logger.info("[autopost] user=%s mode=both: no fresh RSS items (none or already posted), fallback to creator", user_id)
                        if not should_run_mode_now(cfg, "creative", now, last_post_at, user_id, channel):
                            continue
                        msg = creator_make_post(user_id, cfg)
                        creator_entities = apply_bold_title(msg, []) if bool(cfg.get("creative_bold_title", False)) else []
                        await app.bot.send_message(chat_id=channel, text=msg, entities=creator_entities or None)
                        bump_daily_count(cfg, "creator")
                        mark_mode_scheduled(cfg, "creative", now)
                        save_client(user_id, cfg)
                        last_post_at[(user_id, channel, "creative")] = now
                        continue

                    if mode == "both" and (merged_candidates or _queue_items(cfg)) and (not rss_enabled or rss_paused):
                        if not creative_enabled:
                            continue
                        if not should_run_mode_now(cfg, "creative", now, last_post_at, user_id, channel):
                            continue
                        msg = creator_make_post(user_id, cfg)
                        creator_entities = apply_bold_title(msg, []) if bool(cfg.get("creative_bold_title", False)) else []
                        await app.bot.send_message(chat_id=channel, text=msg, entities=creator_entities or None)
                        bump_daily_count(cfg, "creator")
                        mark_mode_scheduled(cfg, "creative", now)
                        save_client(user_id, cfg)
                        last_post_at[(user_id, channel, "creative")] = now
                        continue

                    if not merged_candidates and not _queue_items(cfg):
                        if should_log_diag(user_id, "no_fresh_rss_items", now):
                            logger.info("[autopost] user=%s mode=rss: no fresh RSS items (feed has no new entries or all were deduped)", user_id)
                        continue

                    if not rss_enabled:
                        continue
                    if rss_paused:
                        continue
                    if not should_run_mode_now(cfg, "rss", now, last_post_at, user_id, channel):
                        continue

                    blocked_now = is_blocked_now(cfg, "rss", now)
                    candidate = pick_best_candidate_for_cycle(cfg, merged_candidates, blocked_now)
                    if not candidate:
                        if blocked_now:
                            logger.info("[CANDIDATE_SKIPPED_BLOCKED] channel=%s reason=blocked_hours_active", channel)
                            mark_mode_scheduled(cfg, "rss", now)
                            save_client(user_id, cfg)
                        continue

                    if not candidate_is_fresh(
                        cfg,
                        candidate.get("published"),
                        datetime.now(timezone.utc),
                        "pre_post",
                        is_important=bool(candidate.get("important", False)),
                    ):
                        logger.info("[CANDIDATE_SKIPPED_STALE] channel=%s link=%s", channel, candidate.get("link"))
                        mark_mode_scheduled(cfg, "rss", now)
                        save_client(user_id, cfg)
                        continue

                    published, title, link, src = candidate["published"], candidate["title"], candidate["link"], candidate["feed_url"]
                    summary, source_context, weak_context, social_source = build_rss_generation_input(src, link, title)
                    msg = llm_generate_post(user_id, cfg, title, summary, link, source_context, weak_context, social_source)
                    image_url = extract_image_url_for_link(src, link)
                    send_image_url, temp_file = await prepare_rss_image_for_sending(app.bot, cfg, user_id, image_url)

                    await send_rss_to_channel(app.bot, cfg, channel, msg, link, send_image_url, temp_file)

                    _record_posted_rss_item(cfg, link, title, src, published)
                    bump_daily_count(cfg, "rss")
                    mark_mode_scheduled(cfg, "rss", now)
                    logger.info("[CANDIDATE_POSTED] channel=%s link=%s mode=rss", channel, link)
                    save_client(user_id, cfg)
                    last_post_at[(user_id, channel, "rss")] = now

        except Exception:
            logger.exception("[autopost] loop error")

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

    for p in CLIENTS_DIR.glob("*.json"):
        try:
            user_id = int(p.stem)
        except Exception:
            continue

        cfg = load_client(user_id)
        channels = get_saved_channels(cfg)
        if not channels:
            continue

        changed = False
        for channel in channels:
            switch_active_channel(cfg, channel)
            _, tz_reason = ensure_channel_timezone(cfg, channel)
            if tz_reason != "existing":
                changed = True
            for mode in ("rss", "creative"):
                if not mode_uses_interval(cfg, mode):
                    continue
                next_key = _interval_next_run_key(mode)
                next_run = _parse_local_iso_datetime(cfg.get(next_key) or "")
                if next_run:
                    continue
                _schedule_next_interval_run(cfg, mode, user_now(cfg))
                changed = True

        if changed:
            save_client(user_id, cfg)

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
    app.add_handler(CommandHandler("setrss", setrss_cmd))
    app.add_handler(CommandHandler("setcreative", setcreative_cmd))
    app.add_handler(CommandHandler("activate", activate_cmd))
    app.add_handler(CommandHandler("deactivate", deactivate_cmd))
    app.add_handler(CommandHandler("setlimit", setlimit_cmd))
    app.add_handler(CommandHandler("setchannels", setchannels_cmd))
    app.add_handler(CommandHandler("setfeedlimit", setfeedlimit_cmd))
    app.add_handler(CommandHandler("setinterval", setinterval_admin_cmd))

    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.CAPTION | filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND,
            wizard_text_handler,
        )
    )

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
