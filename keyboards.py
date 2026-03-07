from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🇬🇧 English", callback_data="ui:setlang:en")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="ui:setlang:ru")],
        ]
    )


def build_payment_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(labels["btn_payment"], callback_data="ui:pay")]
    ])


def build_main_menu_minimal(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_setup"], callback_data="ui:setup")],
            [InlineKeyboardButton(labels["btn_payment"], callback_data="ui:pay")],
            [InlineKeyboardButton(labels["btn_help"], callback_data="ui:help")],
            [InlineKeyboardButton(labels["btn_status"], callback_data="ui:status")],
            [InlineKeyboardButton(labels["btn_lang"], callback_data="ui:lang")],
        ]
    )


def build_setup_submenu(labels: dict, autopost_enabled: bool | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_channel_management"], callback_data="ui:setup:channels")],
            [InlineKeyboardButton(labels["btn_modes"], callback_data="ui:modes")],
            [InlineKeyboardButton(labels["btn_scheduling"], callback_data="ui:setup:scheduling")],
            [InlineKeyboardButton(labels["btn_back_main"], callback_data="ui:backmain")],
        ]
    )


def build_channel_management_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_add_channel"], callback_data="ui:setchannel")],
            [InlineKeyboardButton(labels["btn_delete_channel"], callback_data="ui:unsetchannel")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:setup")],
        ]
    )


def build_channel_delete_menu(labels: dict, channels: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for idx, channel in enumerate(channels, start=1):
        rows.append([InlineKeyboardButton(f"🗑 {idx}. {channel}", callback_data=f"ui:delchannel:{idx}")])
    rows.append([InlineKeyboardButton(labels["btn_back"], callback_data="ui:setup:channels")])
    return InlineKeyboardMarkup(rows)


def build_channel_picker_menu(labels: dict, channels: list[str], action: str, back_callback: str) -> InlineKeyboardMarkup:
    rows = []
    for idx, channel in enumerate(channels, start=1):
        rows.append([InlineKeyboardButton(f"{idx}. {channel}", callback_data=f"ui:pickchannel:{action}:{idx}")])
    rows.append([InlineKeyboardButton(labels["btn_back"], callback_data=back_callback)])
    return InlineKeyboardMarkup(rows)


def build_modes_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["mode_creative"], callback_data="ui:mode:creative:menu")],
            [InlineKeyboardButton(labels["mode_rss_ai"], callback_data="ui:mode:rss:menu")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:setup")],
        ]
    )


def build_creative_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_edit_prompt"], callback_data="ui:creative:editprompt")],
            [InlineKeyboardButton(labels["btn_preview"], callback_data="ui:creative:preview")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:modes")],
        ]
    )


def build_rss_ai_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_edit_prompt"], callback_data="ui:rss:editprompt")],
            [InlineKeyboardButton(labels["btn_edit_feeds"], callback_data="ui:rss:feeds")],
            [InlineKeyboardButton(labels["btn_preview"], callback_data="ui:rss:preview")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:modes")],
        ]
    )


def build_scheduling_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_schedule_rss"], callback_data="ui:schedule:rss:menu")],
            [InlineKeyboardButton(labels["btn_schedule_creative"], callback_data="ui:schedule:creative:menu")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:setup")],
        ]
    )


def build_mode_schedule_menu(labels: dict, mode: str, enabled: bool) -> InlineKeyboardMarkup:
    toggle_label = labels["btn_schedule_toggle_off"] if enabled else labels["btn_schedule_toggle_on"]
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_schedule_edit"], callback_data=f"ui:schedule:{mode}:edit")],
            [InlineKeyboardButton(toggle_label, callback_data=f"ui:schedule:{mode}:toggle")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:setup:scheduling")],
        ]
    )


def build_feed_management_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_add_feed"], callback_data="ui:addfeed")],
            [InlineKeyboardButton(labels["btn_delete_feed"], callback_data="ui:feedsdelete")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:mode:rss:menu")],
        ]
    )


def build_feed_delete_menu(labels: dict, feeds: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for idx, url in enumerate(feeds, start=1):
        short = (url[:45] + "…") if len(url) > 46 else url
        rows.append([InlineKeyboardButton(f"❌ {idx}. {short}", callback_data=f"ui:delfeed:{idx}")])
    rows.append([InlineKeyboardButton(labels["btn_back"], callback_data="ui:rss:feeds")])
    return InlineKeyboardMarkup(rows)
