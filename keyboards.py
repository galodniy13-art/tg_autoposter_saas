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
            [InlineKeyboardButton(labels["btn_channel_management"], callback_data="ui:setup:channels")],
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
            [InlineKeyboardButton(labels["mode_rss_ai"], callback_data="ui:mode:rss:menu")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:setup")],
        ]
    )


def build_creative_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_channel_intake"], callback_data="ui:creative:intake")],
            [InlineKeyboardButton(labels["btn_idea_bank"], callback_data="ui:creative:ideas")],
            [InlineKeyboardButton(labels["btn_campaigns"], callback_data="ui:creative:campaigns")],
            [InlineKeyboardButton(labels["btn_creative_publish_settings"], callback_data="ui:creative:publish_settings")],
            [InlineKeyboardButton(labels["btn_creative_advanced"], callback_data="ui:creative:advanced")],
            [InlineKeyboardButton(labels["btn_preview"], callback_data="ui:creative:preview")],
            [InlineKeyboardButton(labels["btn_back_main"], callback_data="ui:backmain")],
        ]
    )


def build_creative_publish_settings_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_scheduling"], callback_data="ui:schedule:creative:menu")],
            [InlineKeyboardButton(labels["btn_post_format"], callback_data="ui:creative:output")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:mode:creative:menu")],
        ]
    )


def build_creative_intake_menu(labels: dict, show_resume: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(labels["btn_channel_intake_fast_start"], callback_data="ui:creative:intake:fast_start")],
        [InlineKeyboardButton(labels["btn_channel_intake_start"], callback_data="ui:creative:intake:start")],
    ]
    if show_resume:
        rows.append([InlineKeyboardButton(labels["btn_resume_flow"], callback_data="ui:creative:intake:resume")])
    rows.extend(
        [
            [InlineKeyboardButton(labels["btn_channel_intake_view"], callback_data="ui:creative:intake:view")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:mode:creative:menu")],
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_creative_campaigns_menu(labels: dict, show_resume: bool = False) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(labels["btn_campaign_create"], callback_data="ui:creative:campaigns:create")]]
    if show_resume:
        rows.append([InlineKeyboardButton(labels["btn_resume_flow"], callback_data="ui:creative:campaigns:create:resume")])
    rows.extend(
        [
            [InlineKeyboardButton(labels["btn_campaign_view"], callback_data="ui:creative:campaigns:view")],
            [InlineKeyboardButton(labels["btn_campaign_activate"], callback_data="ui:creative:campaigns:activate")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:mode:creative:menu")],
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_creative_advanced_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_content_variety"], callback_data="ui:creative:variety")],
            [InlineKeyboardButton(labels["btn_source_center"], callback_data="ui:creative:sources")],
            [InlineKeyboardButton(labels["btn_content_plan"], callback_data="ui:creative:contentplan")],
            [InlineKeyboardButton(labels["btn_visual_support"], callback_data="ui:creative:visual")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:mode:creative:menu")],
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
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:creative:advanced")],
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


def build_rss_ai_menu(labels: dict, rss_paused: bool = False) -> InlineKeyboardMarkup:
    pause_resume_label = labels["btn_resume_posting"] if rss_paused else labels["btn_pause_posting"]
    pause_resume_callback = "ui:rss:resume_posting" if rss_paused else "ui:rss:pause_posting"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(pause_resume_label, callback_data=pause_resume_callback)],
            [InlineKeyboardButton(labels["btn_rss_quickstart"], callback_data="ui:rss:quickstart")],
            [
                InlineKeyboardButton(labels["btn_edit_prompt"], callback_data="ui:rss:stylemenu"),
                InlineKeyboardButton(labels["btn_edit_feeds"], callback_data="ui:rss:feeds"),
            ],
            [
                InlineKeyboardButton(labels["btn_rss_output_settings"], callback_data="ui:rss:output"),
                InlineKeyboardButton(labels["btn_scheduling"], callback_data="ui:schedule:rss:menu"),
            ],
            [InlineKeyboardButton(labels["btn_preview"], callback_data="ui:rss:preview")],
            [InlineKeyboardButton(labels["btn_back_main"], callback_data="ui:backmain")],
        ]
    )


def build_prompt_builder_review_menu(labels: dict, mode: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_save"], callback_data=f"ui:promptbuilder:{mode}:save")],
            [InlineKeyboardButton(labels["btn_regenerate"], callback_data=f"ui:promptbuilder:{mode}:regenerate")],
            [InlineKeyboardButton(labels["btn_cancel"], callback_data=f"ui:promptbuilder:{mode}:cancel")],
        ]
    )


def build_copy_style_review_menu(labels: dict, mode: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_save"], callback_data=f"ui:copystyle:{mode}:save")],
            [InlineKeyboardButton(labels["btn_edit"], callback_data=f"ui:copystyle:{mode}:edit")],
        ]
    )


def build_style_setup_menu(labels: dict, mode: str, back_callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_copy_my_style"], callback_data=f"ui:{mode}:copystyle")],
            [InlineKeyboardButton(labels["btn_save"], callback_data=f"ui:stylemenu:{mode}:save")],
            [InlineKeyboardButton(labels["btn_edit"], callback_data=f"ui:{mode}:editprompt")],
            [InlineKeyboardButton(labels["btn_back"], callback_data=back_callback)],
        ]
    )


def build_rss_output_menu(labels: dict, include_source_link: bool, use_feed_image: bool, cta_enabled: bool, bold_title_enabled: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_emoji_management"], callback_data="ui:rss:emoji:menu")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:backmain")],
        ]
    )


def build_creative_output_menu(labels: dict, bold_title_enabled: bool) -> InlineKeyboardMarkup:
    bold_label = labels["btn_bold_title_on"] if bold_title_enabled else labels["btn_bold_title_off"]
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(bold_label, callback_data="ui:creative:toggle_bold_title"),
                InlineKeyboardButton(labels["btn_emoji_management"], callback_data="ui:creative:emoji:menu"),
            ],
            [
                InlineKeyboardButton(labels["btn_edit_template_image"], callback_data="ui:creative:asset:template"),
            ],
            [InlineKeyboardButton(labels["btn_edit_watermark"], callback_data="ui:creative:asset:watermark")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:mode:creative:menu")],
        ]
    )


def build_creative_content_plan_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_content_plan_generate"], callback_data="ui:creative:contentplan:generate")],
            [InlineKeyboardButton(labels["btn_content_plan_view"], callback_data="ui:creative:contentplan:view")],
            [InlineKeyboardButton(labels["btn_content_plan_regenerate_item"], callback_data="ui:creative:contentplan:regenerate")],
            [InlineKeyboardButton(labels["btn_content_plan_edit_item"], callback_data="ui:creative:contentplan:edit")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:creative:advanced")],
        ]
    )


def build_creative_content_plan_item_picker_menu(labels: dict, items: list[dict], action: str) -> InlineKeyboardMarkup:
    rows = []
    for idx, item in enumerate(items, start=1):
        topic = str(item.get("topic") or "").strip() or "—"
        rows.append([InlineKeyboardButton(f"{idx}. {topic[:40]}", callback_data=f"ui:creative:contentplan:{action}:{idx}")])
    rows.append([InlineKeyboardButton(labels["btn_back"], callback_data="ui:creative:contentplan")])
    return InlineKeyboardMarkup(rows)


def build_creative_source_center_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_topic_pillars"], callback_data="ui:creative:sources:topic_pillars")],
            [InlineKeyboardButton(labels["btn_idea_bank"], callback_data="ui:creative:sources:idea_bank")],
            [InlineKeyboardButton(labels["btn_inspiration_links"], callback_data="ui:creative:sources:inspiration_links")],
            [InlineKeyboardButton(labels["btn_source_snippets"], callback_data="ui:creative:sources:source_snippets")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:creative:advanced")],
        ]
    )


def build_creative_source_list_menu(labels: dict, source_type: str) -> InlineKeyboardMarkup:
    base = f"ui:creative:sources:{source_type}"
    rows = [
        [InlineKeyboardButton(labels["btn_view_items"], callback_data=f"{base}:view")],
        [InlineKeyboardButton(labels["btn_add_item"], callback_data=f"{base}:add")],
    ]
    if source_type == "idea_bank":
        rows.append([InlineKeyboardButton(labels["btn_idea_generate"], callback_data=f"{base}:generate")])
    rows.append([InlineKeyboardButton(labels["btn_delete_item"], callback_data=f"{base}:delete")])
    rows.append([InlineKeyboardButton(labels["btn_back"], callback_data="ui:mode:creative:menu" if source_type == "idea_bank" else "ui:creative:sources")])
    return InlineKeyboardMarkup(rows)


def build_creative_source_delete_menu(labels: dict, source_type: str, items: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for idx, item in enumerate(items, start=1):
        short = item if len(item) <= 48 else item[:47] + "…"
        rows.append([InlineKeyboardButton(f"❌ {idx}. {short}", callback_data=f"ui:creative:sources:{source_type}:del:{idx}")])
    rows.append([InlineKeyboardButton(labels["btn_back"], callback_data=f"ui:creative:sources:{source_type}")])
    return InlineKeyboardMarkup(rows)


def build_creative_visual_support_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_visual_generate_idea"], callback_data="ui:creative:visual:idea")],
            [InlineKeyboardButton(labels["btn_visual_generate_search_query"], callback_data="ui:creative:visual:search")],
            [InlineKeyboardButton(labels["btn_visual_generate_ai_prompt"], callback_data="ui:creative:visual:aiprompt")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:creative:advanced")],
        ]
    )


def build_emoji_management_menu(labels: dict, mode: str) -> InlineKeyboardMarkup:
    base = f"ui:{mode}:emoji"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_add_update_emoji"], callback_data=f"{base}:add")],
            [InlineKeyboardButton(labels["btn_delete_emoji"], callback_data=f"{base}:delete")],
            [InlineKeyboardButton(labels["btn_back"], callback_data=f"ui:{mode}:output")],
        ]
    )


def build_asset_management_menu(labels: dict, mode: str, asset_type: str, has_asset: bool) -> InlineKeyboardMarkup:
    base = f"ui:{mode}:asset:{asset_type}"
    rows = []
    if has_asset:
        rows.append([InlineKeyboardButton(labels["btn_replace_asset"], callback_data=base + ":add")])
        rows.append([InlineKeyboardButton(labels["btn_delete_asset"], callback_data=base + ":delete")])
    else:
        rows.append([InlineKeyboardButton(labels["btn_add_asset"], callback_data=base + ":add")])
    rows.append([InlineKeyboardButton(labels["btn_back"], callback_data=f"ui:{mode}:output")])
    return InlineKeyboardMarkup(rows)


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
            [
                InlineKeyboardButton(mode_label, callback_data=f"ui:schedule:{mode}:switch_mode"),
                InlineKeyboardButton(labels["btn_schedule_edit"], callback_data=f"ui:schedule:{mode}:edit"),
            ],
            [
                InlineKeyboardButton(labels["btn_schedule_edit_interval"], callback_data=f"ui:schedule:{mode}:interval"),
                InlineKeyboardButton(labels["btn_schedule_quiet_hours"], callback_data=f"ui:schedule:{mode}:quiet"),
            ],
            [
                InlineKeyboardButton(labels["btn_schedule_timezone"], callback_data="ui:schedule:timezone"),
            ],
            [
                InlineKeyboardButton(toggle_label, callback_data=f"ui:schedule:{mode}:toggle"),
                InlineKeyboardButton(labels["btn_back"], callback_data=f"ui:mode:{mode}:menu"),
            ],
        ]
    )


def build_quiet_hours_menu(labels: dict, mode: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_quiet_hours_add"], callback_data=f"ui:schedule:{mode}:quiet:add")],
            [InlineKeyboardButton(labels["btn_quiet_hours_delete"], callback_data=f"ui:schedule:{mode}:quiet:delete")],
            [InlineKeyboardButton(labels["btn_back"], callback_data=f"ui:schedule:{mode}:menu")],
        ]
    )


def build_quiet_hours_delete_menu(labels: dict, mode: str, windows: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for idx, window in enumerate(windows, start=1):
        rows.append([InlineKeyboardButton(f"❌ {idx}. {window}", callback_data=f"ui:schedule:{mode}:quiet:del:{idx}")])
    rows.append([InlineKeyboardButton(labels["btn_back"], callback_data=f"ui:schedule:{mode}:quiet")])
    return InlineKeyboardMarkup(rows)


def build_feed_management_menu(labels: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels["btn_add_feed"], callback_data="ui:addfeed")],
            [InlineKeyboardButton(labels["btn_delete_feed"], callback_data="ui:feedsdelete")],
            [InlineKeyboardButton(labels["btn_back"], callback_data="ui:mode:rss:menu")],
        ]
    )


def build_feed_delete_menu(labels: dict, feeds: list) -> InlineKeyboardMarkup:
    rows = []
    for idx, feed in enumerate(feeds, start=1):
        if isinstance(feed, dict):
            name = str(feed.get("name", "")).strip()
            url = str(feed.get("url", "")).strip()
        else:
            name = ""
            url = str(feed or "")
        short = (url[:33] + "…") if len(url) > 34 else url
        title = f"{name} — {short}" if name else short
        rows.append([InlineKeyboardButton(f"❌ {idx}. {title}", callback_data=f"ui:delfeed:{idx}")])
    rows.append([InlineKeyboardButton(labels["btn_back"], callback_data="ui:rss:feeds")])
    return InlineKeyboardMarkup(rows)
