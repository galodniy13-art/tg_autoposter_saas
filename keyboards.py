from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🇬🇧 English", callback_data="ui:setlang:en")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="ui:setlang:ru")],
        ]
    )



def build_setup_submenu(labels: dict, autopost_enabled: bool) -> InlineKeyboardMarkup:
    toggle_label = labels["btn_autopost_on"] if autopost_enabled else labels["btn_autopost_off"]
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(labels["btn_setchannel"], callback_data="ui:setchannel"),
                InlineKeyboardButton(labels["btn_unsetchannel"], callback_data="ui:unsetchannel"),
            ],
            [InlineKeyboardButton(labels["btn_addfeed"], callback_data="ui:addfeed")],
            [
                InlineKeyboardButton(labels["btn_setstyle"], callback_data="ui:setstyle"),
                InlineKeyboardButton(labels["btn_showstyle"], callback_data="ui:showstyle"),
            ],
            [InlineKeyboardButton(labels["btn_resetstyle"], callback_data="ui:resetstyle")],
            [InlineKeyboardButton(toggle_label, callback_data="ui:autoposttoggle")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:backmain")],
        ]
    )
