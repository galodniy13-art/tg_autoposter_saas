from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🇬🇧 English", callback_data="ui:setlang:en")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="ui:setlang:ru")],
        ]
    )


def build_modes_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["mode_rss_ai"], callback_data="ui:modepick:rss")],
            [InlineKeyboardButton(labels["mode_creative"], callback_data="ui:modepick:creator")],
        ]
    )


def build_payment_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(labels["btn_payment"], callback_data="ui:pay")]]
    )
