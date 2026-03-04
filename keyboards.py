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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(labels["btn_payment"], callback_data="ui:pay")]
    ])

def build_setup_submenu(labels: dict, autopost_enabled: bool) -> InlineKeyboardMarkup:
    toggle_label = labels["btn_autopost_on"] if autopost_enabled else labels["btn_autopost_off"]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_label, callback_data="ui:autopost:toggle")],
        [InlineKeyboardButton(labels["btn_back"], callback_data="ui:back")],
    ])
    
def build_main_menu_minimal(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_setup"], callback_data="ui:setup")],
            [InlineKeyboardButton(labels["btn_modes"], callback_data="ui:modes")],
            [InlineKeyboardButton(labels["btn_payment"], callback_data="ui:pay")],
            [InlineKeyboardButton(labels["btn_help"], callback_data="ui:help")],
            [InlineKeyboardButton(labels["btn_status"], callback_data="ui:status")],
            [InlineKeyboardButton(labels["btn_lang"], callback_data="ui:lang")],
        ]
    )


def build_setup_submenu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(labels["btn_setchannel"], callback_data="ui:setchannel"),
                InlineKeyboardButton(labels["btn_unsetchannel"], callback_data="ui:unsetchannel"),
            ],
            [InlineKeyboardButton(labels["btn_addfeed"], callback_data="ui:addfeed")],
            [
                InlineKeyboardButton(labels["btn_addfeed"], callback_data="ui:addfeed"),
                InlineKeyboardButton(labels["btn_deletefeed"], callback_data="ui:feedsdelete"),
            ],
            [
                InlineKeyboardButton(labels["btn_setstyle"], callback_data="ui:setstyle"),
                InlineKeyboardButton(labels["btn_showstyle"], callback_data="ui:showstyle"),
            ],
            [InlineKeyboardButton(labels["btn_resetstyle"], callback_data="ui:resetstyle")],
            [InlineKeyboardButton(toggle_label, callback_data="ui:autoposttoggle")],
            [
                InlineKeyboardButton(labels["btn_on"], callback_data="ui:autoposton"),
                InlineKeyboardButton(labels["btn_off"], callback_data="ui:autopostoff"),
            ],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:backmain")],
        ]
    )
