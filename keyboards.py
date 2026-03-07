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
            [InlineKeyboardButton(labels["btn_content_variety"], callback_data="ui:creative:variety")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:modes")],
        ]
    )


def build_creative_variety_menu(labels: dict, variation_level: str, avoid_repetition: bool) -> InlineKeyboardMarkup:
    level_label = labels["variation_level_value_" + variation_level]
    avoid_label = labels["btn_avoid_repetition_on"] if avoid_repetition else labels["btn_avoid_repetition_off"]
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_variation_level"] + f": {level_label}", callback_data="ui:creative:variety:level")],
            [InlineKeyboardButton(labels["btn_post_types"], callback_data="ui:creative:variety:types")],
            [InlineKeyboardButton(avoid_label, callback_data="ui:creative:variety:avoid")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:mode:creative:menu")],
        ]
    )


def build_creative_variation_level_menu(labels: dict, variation_level: str) -> InlineKeyboardMarkup:
    rows = []
    for level in ("low", "balanced", "high"):
        marker = "✅ " if level == variation_level else ""
        rows.append([InlineKeyboardButton(marker + labels["variation_level_value_" + level], callback_data=f"ui:creative:variety:level:{level}")])
    rows.append([InlineKeyboardButton(labels["btn_back"], callback_data="ui:creative:variety")])
    return InlineKeyboardMarkup(rows)


def build_creative_post_types_menu(labels: dict, selected_types: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for post_type in ("educational", "opinion", "story", "checklist", "question", "myth_vs_fact", "mini_case"):
        enabled = post_type in selected_types
        marker = "✅ " if enabled else "◻️ "
        rows.append([InlineKeyboardButton(marker + labels["post_type_" + post_type], callback_data=f"ui:creative:variety:type:{post_type}")])
    rows.append([InlineKeyboardButton(labels["btn_back"], callback_data="ui:creative:variety")])
    return InlineKeyboardMarkup(rows)


def build_rss_ai_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_edit_prompt"], callback_data="ui:rss:editprompt")],
            [InlineKeyboardButton(labels["btn_edit_feeds"], callback_data="ui:rss:feeds")],
            [InlineKeyboardButton(labels["btn_rss_output_settings"], callback_data="ui:rss:output")],
            [InlineKeyboardButton(labels["btn_preview"], callback_data="ui:rss:preview")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:modes")],
        ]
    )


def build_rss_output_menu(labels: dict, include_source_link: bool, use_feed_image: bool) -> InlineKeyboardMarkup:
    source_label = labels["btn_source_link_on"] if include_source_link else labels["btn_source_link_off"]
    image_label = labels["btn_feed_image_on"] if use_feed_image else labels["btn_feed_image_off"]
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(source_label, callback_data="ui:rss:toggle_source_link")],
            [InlineKeyboardButton(image_label, callback_data="ui:rss:toggle_feed_image")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:mode:rss:menu")],
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


def build_mode_schedule_menu(labels: dict, mode: str, enabled: bool, use_interval: bool) -> InlineKeyboardMarkup:
    toggle_label = labels["btn_schedule_toggle_off"] if enabled else labels["btn_schedule_toggle_on"]
    mode_label = labels["btn_posting_mode_interval"] if use_interval else labels["btn_posting_mode_scheduled"]
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(mode_label, callback_data=f"ui:schedule:{mode}:switch_mode")],
            [InlineKeyboardButton(labels["btn_schedule_edit"], callback_data=f"ui:schedule:{mode}:edit")],
            [InlineKeyboardButton(labels["btn_schedule_edit_interval"], callback_data=f"ui:schedule:{mode}:interval")],
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
