from __future__ import annotations

from telegram import InlineKeyboardButton

_MODE_LABELS = {
    "en": {
        "rss": "📰 Mode: RSS",
        "creator": "✍️ Mode: Creator",
        "both": "🧩 Mode: Both",
        "set": "✅ Mode set: {mode}",
    },
    "ru": {
        "rss": "📰 Режим: RSS",
        "creator": "✍️ Режим: Creator",
        "both": "🧩 Режим: Оба",
        "set": "✅ Режим установлен: {mode}",
    },
}


def _lang(cfg: dict) -> str:
    lang = (cfg.get("language") or "en").lower()
    return lang if lang in ("en", "ru") else "en"


def build_mode_buttons(cfg: dict) -> list[InlineKeyboardButton]:
    lang = _lang(cfg)
    labels = _MODE_LABELS[lang]
    return [
        InlineKeyboardButton(labels["rss"], callback_data="ui:mode:rss"),
        InlineKeyboardButton(labels["creator"], callback_data="ui:mode:creator"),
    ]


def mode_set_text(cfg: dict, mode: str) -> str:
    lang = _lang(cfg)
    labels = _MODE_LABELS[lang]
    mode_label = labels.get(mode, mode)
    return labels["set"].format(mode=mode_label)
