TEXTS = {
    "en": {
        "welcome": "Welcome!",
        "menu_title": "Menu. Choose an action:",
        "mode_usage": "Usage: /mode rss OR /mode creator OR /mode both",
        "payment_offer":
            "💳 Access pricing (USD/month):\n\n"
            "RSS mode (account-wide daily limit shared across all your channels):\n"
            "• 5 posts/day — $3/month\n"
            "• 10 posts/day — $5/month\n"
            "• 20 posts/day — $8/month\n• 40 posts/day — $12/month\n\n"
            "Creative mode (account-wide daily limit shared across all your channels):\n"
            "• 5 posts/day — $5/month\n"
            "• 10 posts/day — $8/month\n"
            "• 20 posts/day — $13/month\n• 40 posts/day — $20/month\n\n"
            "Channel slots are purchased separately (how many channels you can connect).\n"
            "You can combine RSS + Creative access.\n"
            "To activate, message: @a_karaglan, @a_karaglanov\n\n"
            "🔻 Discount for upfront payment\n\n"
            "• 3 months — −10%\n"
            "• 6 months — −20%",
        "btn_modes": "🧠 Modes",
        "btn_scheduling": "🕒 Scheduling",
        "modes_title": "🧠 Modes. Choose a mode settings section:",
        "mode_rss_ai": "📰 RSS + AI",
        "mode_creative": "✨ Creative",
        "creative_locked": "🔒 Creative mode is unavailable for your account.",
        "rss_locked": "🔒 RSS + AI mode is unavailable for your account.",
        "creative_paywall":
            "Creative mode pricing (USD/month):\n"
            "(Account-wide daily limit shared across all connected channels)\n"
            "• 5/day — $5/month\n"
            "• 10/day — $8/month\n"
            "• 20/day — $13/month\n• 40/day — $20/month\n\n"
            "Channel slots are managed separately.\n"
            "To activate, message: @a_karaglan, @a_karaglanov\n\n"
            "🔻 Discount for upfront payment\n\n"
            "• 3 months — −10%\n"
            "• 6 months — −20%",
        "rss_paywall":
            "RSS mode pricing (USD/month):\n"
            "(Account-wide daily limit shared across all connected channels)\n"
            "• 5/day — $3/month\n"
            "• 10/day — $5/month\n"
            "• 20/day — $8/month\n• 40/day — $12/month\n\n"
            "Channel slots are managed separately.\n"
            "To activate, message: @a_karaglan, @a_karaglanov\n\n"
            "🔻 Discount for upfront payment\n\n"
            "• 3 months — −10%\n"
            "• 6 months — −20%",
        "mode_set_rss": "✅ Mode set: 📰 RSS + AI",
        "mode_set_creator": "✅ Mode set: ✨ Creative",
        "btn_payment": "💳 Buy posting plan",
        "btn_back": "⬅ Back",
        "btn_back_main": "⬅ Back to Main Menu",
        "btn_autopost_on": "🤖 Autopost: ON",
        "btn_autopost_off": "🤖 Autopost: OFF",
        "setup_menu_title": "⚙️ Setup:",
        "scheduling_menu_title": "🕒 Scheduling:",
        "channel_management_title": "📺 Channel management:",
        "modes_menu_title": "🧠 Modes settings:",
        "creative_menu_title": "✨ Creative settings\n\n✍️ Set your prompt (or use Guided Prompt Builder).\n🎛 Tune Content Variety if needed.\n🕒 Open Scheduling and choose: Scheduled Times or Interval.\n✅ For Scheduled Times, add slots and turn Scheduling ON.\n🚀 Run /autoposton to start posting (next slot or by interval).\n🧪 Tap Preview to check the final result.",
        "rss_menu_title": "📰 RSS + AI settings\n\n✍️ Set your prompt.\n🧾 Add feeds for news sources.\n🧩 Open Post Format and tune output.\n🕒 Open Scheduling and choose: Scheduled Times or Interval.\n✅ For Scheduled Times, add slots and turn Scheduling ON.\n🚀 Run /autoposton to start posting (next slot or by interval).\n🧪 Tap Preview to check the final result.",
        "schedule_mode_title_rss": "📰 RSS + AI schedule",
        "schedule_mode_title_creative": "✨ Creative schedule",
        "schedule_current": "Current schedule:\n{schedule}",
        "schedule_input_instructions": "Send posting times in 24h format, comma-separated.\nExamples:\n09:00\n09:00, 15:00, 21:30\n\nSend \"clear\" to remove all slots.",
        "schedule_invalid": "❌ Invalid format. Use HH:MM or HH:MM, HH:MM",
        "schedule_saved": "✅ Schedule saved.",
        "schedule_cleared": "✅ Schedule cleared.",
        "schedule_enabled": "✅ Schedule turned ON.",
        "schedule_disabled": "⏸ Schedule turned OFF.",
        "schedule_posting_mode": "Posting mode: {mode}",
        "posting_mode_scheduled": "Scheduled Times",
        "posting_mode_interval": "Interval",
        "posting_mode_scheduled_set": "✅ Posting mode set to Scheduled Times.",
        "posting_mode_interval_set": "✅ Posting mode set to Interval.",
        "schedule_interval_current": "Current interval: every {interval} min",
        "preview_no_feeds": "No feeds. Add one first: /addfeed <url>",
        "preview_fallback_text_only": "Could not build image preview, so text preview is shown below.",
        "preview_temporarily_unavailable": "Preview is temporarily unavailable for this setup.",
        "preview_stage_config_failed": "Could not load the selected mode/channel for preview.",
        "preview_stage_rss_failed": "Could not fetch an RSS item for preview.",
        "preview_stage_ai_failed": "Could not generate preview text. Check the AI model and API key.",
        "preview_stage_image_failed": "Could not build the preview image.",
        "preview_stage_send_failed": "Could not send the preview to Telegram.",
        "preview_loading": "Preparing preview, this may take a few seconds.",
        "preview_status_template_build_failed_normal": "Could not build the template image. Showing normal preview.",
        "preview_status_no_rss_image_text_only": "No usable RSS image was found. Showing text preview.",
        "preview_status_asset_load_failed_normal": "Could not load the template or watermark. Showing normal preview.",
        "feed_management_title": "🧾 Feed management:",
        "feed_management_help": "Tip: Want to use an X/Twitter profile as a source? Convert the profile link to RSS at https://rss.app/ and paste the generated RSS link here.",
        "feed_name_prompt": "Send a short name for this feed, or send \"-\" to skip.",
        "btn_lang": "🌐 Language",
        "choose_lang": "Choose your language:",
        "btn_setup": "🛠 Setup",
        "btn_help": "❓ Help",
        "help_link": "https://telegra.ph/Instructions-on-how-to-use-the-bot-and-additional-materials-02-27",
        "help_open_link": "Open this link:",
        "help_contact": "If something is unclear, contact me.",
        "btn_status": "ℹ️ Status",
        "btn_channel_management": "📺 Channel Management",
        "btn_add_channel": "➕ Add Channel",
        "btn_delete_channel": "🗑 Delete Channel",
        "btn_setchannel": "📌 Set channel",
        "btn_unsetchannel": "🧹 Unset channel",
        "btn_addfeed": "🧾 Add feed",
        "btn_deletefeed": "🗑 Delete feed",
        "btn_add_feed": "➕ Add Feed",
        "btn_delete_feed": "🗑 Delete Feed",
        "btn_edit_prompt": "✍️ Edit Prompt",
        "btn_build_prompt_ai": "🪄 Guided Prompt Builder",
        "btn_copy_my_style": "🎭 Copy my style",
        "btn_preview": "🧪 Preview",
        "btn_content_variety": "🎛 Content Variety",
        "btn_variation_level": "Variation Level",
        "btn_post_types": "Post Types",
        "btn_avoid_repetition_on": "♻️ Avoid Repetition: ON",
        "btn_avoid_repetition_off": "♻️ Avoid Repetition: OFF",
        "btn_edit_feeds": "🧾 Edit Feeds",
        "btn_rss_output_settings": "🧩 Post Format",
        "btn_post_format": "🧩 Post Format",
        "rss_output_settings_title": "🧩 Post format settings (RSS + AI):",
        "creative_output_settings_title": "🧩 Post format settings (Creative):",
        "post_format_assets_info": "Visual assets:\n• Template image: {template}\n• Watermark: {watermark}\n• Bold title: {bold_title}\n• Custom emoji: {emoji}\n\nTemplate image = your background/frame for branded visuals.\nWatermark = your logo or channel mark placed on top.\nRecommended: JPG/PNG template, PNG watermark (transparent if possible).\nAuto composition applies when RSS item has an image.",
        "status_added": "added",
        "status_not_added": "not added",
        "btn_edit_template_image": "🖼 Edit template",
        "btn_edit_watermark": "🏷 Edit watermark",
        "btn_add_asset": "➕ Add",
        "btn_replace_asset": "♻️ Replace",
        "btn_delete_asset": "🗑 Delete",
        "asset_manage_template_title": "🖼 Template management",
        "asset_manage_watermark_title": "🏷 Watermark management",
        "asset_manage_template_help": "Here you can manage your template image.",
        "asset_manage_watermark_help": "Here you can manage your watermark.",
        "asset_manage_status": "Current status: {status}",
        "asset_prompt_send_template": "Send one image for the template/background (photo or image document).",
        "asset_prompt_send_watermark": "Send one image for the watermark/logo (photo or image document).\n\nTip: You can remove the background here: https://www.remove.bg/\nBest result: PNG, preferably sent as a document. A slightly transparent watermark usually looks better.",
        "asset_saved_template": "✅ Template image saved.",
        "asset_saved_watermark": "✅ Watermark saved.",
        "asset_deleted_template": "✅ Template image deleted.",
        "asset_deleted_watermark": "✅ Watermark deleted.",
        "asset_upload_invalid": "Please send an image as a photo or image document.",
        "asset_upload_error": "❌ Could not save the image. Please try again.",
        "btn_source_link_on": "🔗 Source Link: ON",
        "btn_source_link_off": "🔗 Source Link: OFF",
        "btn_feed_image_on": "🖼 Feed Image: ON",
        "btn_feed_image_off": "🖼 Feed Image: OFF",
        "btn_rss_cta_on": "📣 CTA: ON",
        "btn_rss_cta_off": "📣 CTA: OFF",
        "btn_bold_title_on": "🅱️ Bold title: ON",
        "btn_bold_title_off": "🅱️ Bold title: OFF",
        "btn_add_emoji": "✨ Add emoji",
        "btn_delete_emoji": "🗑 Delete emoji",
        "emoji_prompt_send": "Send one message with one or several emoji (including premium/custom emoji). I will save this exact message as your emoji style source.",
        "emoji_saved": "✅ Emoji style saved.",
        "emoji_deleted": "✅ Emoji style deleted.",
        "rss_cta_prompt": "Send the CTA text in one message. It will be appended to every RSS post when CTA is ON.",
        "rss_cta_saved": "✅ CTA text saved.",
        "btn_schedule_rss": "📰 RSS + AI Schedule",
        "btn_schedule_creative": "✨ Creative Schedule",
        "btn_schedule_edit": "✍️ Edit Schedule",
        "btn_schedule_edit_interval": "⏱ Edit Interval",
        "btn_posting_mode_scheduled": "🔁 Mode: Scheduled Times",
        "btn_posting_mode_interval": "🔁 Mode: Interval",
        "btn_schedule_toggle_on": "✅ Turn ON",
        "btn_schedule_toggle_off": "⏸ Turn OFF",
        "interval_input_instructions": "Send interval in minutes (numbers only).\nExamples: 60, 120, 180\n\nSend \"cancel\" to go back.",
        "interval_invalid": "❌ Invalid interval. Send a whole number in minutes (for example: 60).",
        "interval_saved": "✅ Interval saved: every {interval} min.",
        "variation_level_title": "🎚 Variation level. Choose one:",
        "variation_level_value_low": "Low",
        "variation_level_value_balanced": "Balanced",
        "variation_level_value_high": "High",
        "post_types_title": "🧩 Post types. Enable one or more:",
        "post_type_educational": "Educational",
        "post_type_opinion": "Opinion",
        "post_type_story": "Story",
        "post_type_checklist": "Checklist",
        "post_type_question": "Question",
        "post_type_myth_vs_fact": "Myth vs Fact",
        "post_type_mini_case": "Mini Case",
        "creative_variety_title": "🎛 Creative content variety settings:",
        "creative_variety_note": "These controls add lightweight diversity while keeping your Creative prompt as the main instruction.",
        "creative_variety_summary": "Level: {level}\nPost types: {post_types}\nAvoid repetition: {avoid}",
        "label_on": "ON",
        "label_off": "OFF",
        "status_id": "ID",
        "status_channels": "Channels",
        "status_rss_daily": "RSS posts/day available",
        "status_creative_daily": "Creative posts/day available",
        "status_valid_until": "Subscription valid until",
        "status_not_set": "not set",
        "status_inactive": "inactive",
        "status_title": "📊 Account status",
        "btn_setstyle": "✍️ Set style",
        "btn_showstyle": "📄 Show style",
        "btn_resetstyle": "♻️ Reset style",
        "btn_on": "🤖 Autopost ON",
        "btn_off": "🛑 OFF",
        "modes_help": "Choose mode with commands:\n/mode rss\n/mode creator\n/mode both",
        "prompt_current": "Current prompt:\n{prompt}",
        "prompt_current_rss": "Current RSS + AI prompt:\n{prompt}",
        "prompt_current_creative": "Current Creative prompt:\n{prompt}",
        "prompt_empty": "No prompt saved yet. The default style is used.",
        "prompt_edit_instructions": "Send your final prompt in one message. Send \"cancel\" to keep the current one.",
        "prompt_edit_cancel_hint": "Send \"cancel\" to keep the current prompt.",
        "prompt_guidance_creative": (
            "How to write a strong Creative prompt for Telegram:\n"
            "• Topic/niche: what exactly you post about.\n"
            "• Tone/voice: expert, friendly, bold, etc.\n"
            "• Audience: who reads your channel.\n"
            "• Length: typical size in lines/characters.\n"
            "• Structure: hook → key points → takeaway.\n"
            "• CTA: soft invite, question, DM, link, etc.\n"
            "• Avoid: clichés, clickbait, banned/off-topic themes.\n\n"
            "Template (copy and edit):\n"
            "You write Telegram posts for [niche].\n"
            "Tone: [tone/voice]. Audience: [target audience].\n"
            "Each post is about [length].\n"
            "Structure: 1) hook, 2) 2–4 practical points/examples, 3) concise conclusion, 4) CTA: [CTA style].\n"
            "Avoid: [what to avoid]."
        ),
        "prompt_guidance_rss": (
            "How to write a strong RSS + AI prompt for Telegram:\n"
            "• Transform feed content: rewrite in your own style, not copy-paste.\n"
            "• Tone/voice: professional, neutral, energetic, etc.\n"
            "• Summary style: brief digest or more detailed explanation.\n"
            "• Length: typical size in lines/characters.\n"
            "• Opinion: allow your commentary or keep neutral.\n"
            "• Ending/CTA: question, subscribe, share, none.\n"
            "• Avoid: fake facts, hype, repetition, overly long intros.\n\n"
            "Template (copy and edit):\n"
            "Rewrite RSS/news items into Telegram posts in [tone].\n"
            "Format: short hook + clear summary + key takeaway.\n"
            "Length: [length].\n"
            "Opinion mode: [neutral / add brief commentary].\n"
            "Ending: [CTA or no CTA].\n"
            "Avoid: [what to avoid]."
        ),
        "prompt_edit_cancelled": "Prompt unchanged.",
        "prompt_edit_saved": "✅ Prompt updated.",
        "prompt_builder_intro_creative": "🪄 Guided Prompt Builder (Creative)\n\nI will ask a few short questions and generate a polished Creative prompt for you.\n\nSend \"cancel\" anytime to exit.",
        "prompt_builder_intro_rss": "🪄 Guided Prompt Builder (RSS + AI)\n\nI will ask a few short questions and generate a polished RSS + AI prompt for you.\n\nSend \"cancel\" anytime to exit.",
        "prompt_builder_q_creative_1": "1/7 What is your niche/topic?\n\nExamples:\n• local football news\n• esports updates\n• nutrition for runners",
        "prompt_builder_q_creative_2": "2/7 Who is the target audience?\n\nExamples:\n• football fans\n• Barcelona supporters\n• general sports readers\n• casual Telegram audience",
        "prompt_builder_q_creative_3": "3/7 What tone should the posts have?\n\nExamples:\n• professional news style\n• friendly fan voice\n• neutral informative\n• energetic sports commentary",
        "prompt_builder_q_creative_4": "4/7 What types of posts do you want most?\n\nExamples:\n• quick news recaps\n• opinions\n• checklists\n• Q&A posts",
        "prompt_builder_q_creative_5": "5/7 What length should the posts usually be?\n\nFor example:\n• short (2–3 sentences)\n• medium (4–6 sentences)\n• up to ~100 words",
        "prompt_builder_q_creative_6": "6/7 What should be avoided?\n\nExamples:\n• clickbait\n• slang\n• political topics\n• aggressive wording",
        "prompt_builder_q_creative_7": "7/7 What language should the posts be in? (English/Russian)",
        "prompt_builder_q_rss_1": "1/7 What is the feed/topic about?\n\nExamples:\n• football transfer news\n• esports tournaments\n• startup funding",
        "prompt_builder_q_rss_2": "2/7 Who is the target audience?\n\nExamples:\n• football fans\n• Barcelona supporters\n• general sports readers\n• casual Telegram audience",
        "prompt_builder_q_rss_3": "3/7 What tone should the posts have?\n\nExamples:\n• professional news style\n• friendly fan voice\n• neutral informative\n• energetic sports commentary",
        "prompt_builder_q_rss_4": "4/7 What length should the posts usually be?\n\nFor example:\n• short (2–3 sentences)\n• medium (4–6 sentences)\n• up to ~100 words",
        "prompt_builder_q_rss_5": "5/7 Neutral summaries or a stronger rewritten angle?\n\nExamples:\n• mostly neutral digest\n• concise editorial spin",
        "prompt_builder_q_rss_6": "6/7 What should be avoided?\n\nExamples:\n• hype\n• duplicate phrases\n• too many hashtags\n• long intros",
        "prompt_builder_q_rss_7": "7/7 What language should the posts be in? (English/Russian)",
        "prompt_builder_generating": "⏳ Generating prompt...",
        "prompt_builder_review": "Here is your generated prompt:\n\n{prompt}\n\nSave it for this mode?",
        "prompt_builder_saved": "✅ Prompt saved for this mode.",
        "prompt_builder_cancelled": "Prompt builder cancelled. No changes saved.",
        "prompt_builder_error": "❌ Could not generate a prompt right now. Please try again.",
        "copy_style_intro": "Send me 3 posts from your channel.\nI will analyze the tone, wording, and structure and create a prompt in your style.",
        "copy_style_progress": "Got it. Send {left} more posts.",
        "copy_style_invalid": "Please send text posts so I can analyze your style.",
        "copy_style_success": "✅ Done. Prompt updated for this mode based on your style.",
        "copy_style_loading": "Got it. Preparing your prompt, this will take a few seconds.",
        "copy_style_review": "Your style-based prompt is ready.\n\n{prompt}\n\nBefore saving, you may want to add details like output language, post length, what to avoid, audience, CTA/ending, or whether to stay neutral vs add commentary.\nYou can save it now or edit it first. You can also copy the full prompt, adjust it, and send back the final version.",
        "copy_style_edit_ready": "Your generated draft is below. Edit it and send your final version:\n\n{prompt}",
        "btn_save": "💾 Save",
        "btn_edit": "✍️ Edit",
        "btn_regenerate": "🔄 Regenerate",
        "btn_cancel": "❌ Cancel",
        "feeds_empty": "No feeds yet.",
        "feed_added": "✅ Feed added.",
        "feed_deleted": "✅ Feed deleted.",
        "channel_deleted": "✅ Channel removed.",
        "channel_empty": "No channel configured.",
        "channels_list_title": "Saved channels ({count}/{slots}):",
        "channels_empty_state": "No saved channels yet.\nSlots available: {slots}.",
        "channel_choose_delete": "Choose a channel to delete:",
        "channel_deleted_named": "✅ Channel removed: {channel}",
        "channel_slots_limit": "Channel limit reached ({count}/{slots}). Buy/add channel capacity to connect more channels.",
        "channel_picker_title": "Select channel to continue:",
        "channel_picker_empty": "No channels found yet. Add a channel first in Channel Management.",
        "channel_selected_now": "📌 Selected channel: {channel}",
        "start_welcome": (
            "👋 Welcome to Postora.\n\n"
            "I help you create and schedule posts for your Telegram channel.\n\n"
            "To begin, open ⚙️ Setup, choose a mode, connect your channel, and configure your prompt, feeds, and schedule.\n"
            "You can manage plans/payment separately anytime."
        ),
    },
    "ru": {
        "welcome": "Добро пожаловать!",
        "menu_title": "Меню. Выберите действие:",
        "mode_usage": "Использование: /mode rss ИЛИ /mode creator ИЛИ /mode both",
        "payment_offer":
            "💳 Стоимость доступа (USD/месяц):\n\n"
            "RSS-режим (дневной лимит на аккаунт, общий для всех каналов):\n"
            "• 5 постов/день — $3/месяц\n"
            "• 10 постов/день — $5/месяц\n"
            "• 20 постов/день — $8/месяц\n• 40 постов/день — $12/месяц\n\n"
            "Creative-режим (дневной лимит на аккаунт, общий для всех каналов):\n"
            "• 5 постов/день — $5/месяц\n"
            "• 10 постов/день — $8/месяц\n"
            "• 20 постов/день — $13/месяц\n• 40 постов/день — $20/месяц\n\n"
            "Слоты каналов покупаются отдельно (сколько каналов можно подключить).\n"
            "Можно комбинировать RSS + Creative доступ.\n"
            "Для активации напишите: @a_karaglan, @a_karaglanov\n\n"
            "🔻 Скидка при оплате сразу\n\n"
            "• 3 месяца — −10%\n"
            "• 6 месяцев — −20%",
        "btn_modes": "🧠 Режимы",
        "btn_scheduling": "🕒 Расписание",
        "modes_title": "🧠 Режимы. Выберите раздел настроек:",
        "mode_rss_ai": "📰 RSS + AI",
        "mode_creative": "✨ Creative",
        "creative_locked": "🔒 Режим Creative недоступен для вашего аккаунта.",
        "rss_locked": "🔒 Режим RSS + AI недоступен для вашего аккаунта.",
        "creative_paywall":
            "Стоимость Creative-режима (USD/месяц):\n"
            "(Дневной лимит на аккаунт, общий для всех подключённых каналов)\n"
            "• 5/день — $5/месяц\n"
            "• 10/день — $8/месяц\n"
            "• 20/день — $13/месяц\n• 40/день — $20/месяц\n\n"
            "Слоты каналов управляются отдельно.\n"
            "Для активации напишите: @a_karaglan, @a_karaglanov\n\n"
            "🔻 Скидка при оплате сразу\n\n"
            "• 3 месяца — −10%\n"
            "• 6 месяцев — −20%",
        "rss_paywall":
            "Стоимость RSS-режима (USD/месяц):\n"
            "(Дневной лимит на аккаунт, общий для всех подключённых каналов)\n"
            "• 5/день — $3/месяц\n"
            "• 10/день — $5/месяц\n"
            "• 20/день — $8/месяц\n• 40/день — $12/месяц\n\n"
            "Слоты каналов управляются отдельно.\n"
            "Для активации напишите: @a_karaglan, @a_karaglanov\n\n"
            "🔻 Скидка при оплате сразу\n\n"
            "• 3 месяца — −10%\n"
            "• 6 месяцев — −20%",
        "mode_set_rss": "✅ Режим установлен: 📰 RSS + AI",
        "mode_set_creator": "✅ Режим установлен: ✨ Creative",
        "btn_payment": "💳 Купить пакет постов",
        "btn_back": "⬅ Назад",
        "btn_back_main": "⬅ В главное меню",
        "btn_autopost_on": "🤖 Автопост: ВКЛ",
        "btn_autopost_off": "🤖 Автопост: ВЫКЛ",
        "setup_menu_title": "⚙️ Настройка:",
        "scheduling_menu_title": "🕒 Расписание:",
        "channel_management_title": "📺 Управление каналом:",
        "modes_menu_title": "🧠 Настройки режимов:",
        "creative_menu_title": "✨ Настройки Creative\n\n✍️ Задайте промпт (или используйте конструктор).\n🎛 При необходимости настройте Разнообразие контента.\n🕒 Откройте Расписание и выберите: По времени или По интервалу.\n✅ Для режима По времени задайте слоты и включите Расписание.\n🚀 Выполните /autoposton для запуска публикаций (в ближайший слот или по интервалу).\n🧪 Нажмите Превью, чтобы посмотреть итог.",
        "rss_menu_title": "📰 Настройки RSS + AI\n\n✍️ Задайте промпт.\n🧾 Добавьте ленты-источники.\n🧩 Откройте Формат поста и настройте вывод.\n🕒 Откройте Расписание и выберите: По времени или По интервалу.\n✅ Для режима По времени задайте слоты и включите Расписание.\n🚀 Выполните /autoposton для запуска публикаций (в ближайший слот или по интервалу).\n🧪 Нажмите Превью, чтобы посмотреть итог.",
        "schedule_mode_title_rss": "📰 Расписание RSS + AI",
        "schedule_mode_title_creative": "✨ Расписание Creative",
        "schedule_current": "Текущее расписание:\n{schedule}",
        "schedule_input_instructions": "Отправьте время публикаций в формате 24ч через запятую.\nПримеры:\n09:00\n09:00, 15:00, 21:30\n\nОтправьте \"clear\", чтобы удалить все слоты.",
        "schedule_invalid": "❌ Неверный формат. Используйте HH:MM или HH:MM, HH:MM",
        "schedule_saved": "✅ Расписание сохранено.",
        "schedule_cleared": "✅ Расписание очищено.",
        "schedule_enabled": "✅ Расписание включено.",
        "schedule_disabled": "⏸ Расписание выключено.",
        "schedule_posting_mode": "Режим публикации: {mode}",
        "posting_mode_scheduled": "По времени",
        "posting_mode_interval": "По интервалу",
        "posting_mode_scheduled_set": "✅ Режим публикации: по времени.",
        "posting_mode_interval_set": "✅ Режим публикации: по интервалу.",
        "schedule_interval_current": "Текущий интервал: каждые {interval} мин",
        "preview_no_feeds": "Нет RSS-лент. Сначала добавьте: /addfeed <url>",
        "preview_fallback_text_only": "Не удалось собрать изображение, поэтому ниже показан текстовый превью-вариант.",
        "preview_temporarily_unavailable": "Сейчас не удалось создать превью для этой настройки.",
        "preview_stage_config_failed": "Не удалось получить данные канала или режима для превью.",
        "preview_stage_rss_failed": "Не удалось получить RSS-запись для превью.",
        "preview_stage_ai_failed": "Не удалось сгенерировать текст для превью. Проверьте AI-модель и API-ключ.",
        "preview_stage_image_failed": "Не удалось собрать изображение для превью.",
        "preview_stage_send_failed": "Не удалось отправить превью в Telegram.",
        "preview_loading": "Готовлю превью, это может занять несколько секунд.",
        "preview_status_template_build_failed_normal": "Не удалось собрать изображение по шаблону. Показываю обычное превью.",
        "preview_status_no_rss_image_text_only": "У RSS-записи нет доступного изображения. Показываю текстовый вариант.",
        "preview_status_asset_load_failed_normal": "Не удалось загрузить шаблон или водяной знак. Показываю обычное превью.",
        "feed_management_title": "🧾 Управление лентами:",
        "feed_management_help": "Подсказка: хотите использовать профиль X/Twitter как источник? Преобразуйте ссылку на профиль в RSS через https://rss.app/ и вставьте полученную RSS-ссылку сюда.",
        "feed_name_prompt": "Отправьте короткое название для этой ленты или отправьте \"-\" чтобы пропустить.",
        "btn_lang": "🌐 Язык",
        "choose_lang": "Выберите язык:",
        "btn_setup": "🛠 Настройка",
        "btn_help": "❓ Помощь",
        "help_link": "https://telegra.ph/Instrukciya-po-polzovaniyu-botom-i-poleznye-materialy-02-27",
        "help_open_link": "Откройте эту ссылку:",
        "help_contact": "Если что-то непонятно, напишите мне.",
        "btn_status": "ℹ️ Статус",
        "btn_channel_management": "📺 Управление каналом",
        "btn_add_channel": "➕ Добавить канал",
        "btn_delete_channel": "🗑 Удалить канал",
        "btn_setchannel": "📌 Канал",
        "btn_unsetchannel": "🧹 Отключить канал",
        "btn_addfeed": "🧾 Лента (RSS)",
        "btn_deletefeed": "🗑 Удалить ленту",
        "btn_add_feed": "➕ Добавить ленту",
        "btn_delete_feed": "🗑 Удалить ленту",
        "btn_edit_prompt": "✍️ Изменить промпт",
        "btn_build_prompt_ai": "🪄 Промпт ассистент",
        "btn_copy_my_style": "🎭 Скопировать мой стиль",
        "btn_preview": "🧪 Превью",
        "btn_content_variety": "🎛 Разнообразие контента",
        "btn_variation_level": "Уровень вариативности",
        "btn_post_types": "Типы постов",
        "btn_avoid_repetition_on": "♻️ Избегать повторов: ВКЛ",
        "btn_avoid_repetition_off": "♻️ Избегать повторов: ВЫКЛ",
        "btn_edit_feeds": "🧾 Настройка лент",
        "btn_rss_output_settings": "🧩 Формат поста",
        "btn_post_format": "🧩 Формат поста",
        "rss_output_settings_title": "🧩 Настройки формата поста (RSS + AI):",
        "creative_output_settings_title": "🧩 Настройки формата поста (Creative):",
        "post_format_assets_info": "Визуальные элементы:\n• Шаблон: {template}\n• Водяной знак: {watermark}\n• Жирный заголовок: {bold_title}\n• Кастомные эмодзи: {emoji}\n\nШаблон = фон/заготовка для оформления изображений.\nВодяной знак = логотип или отметка канала поверх изображения.\nРекомендуется: шаблон JPG/PNG, водяной знак PNG (лучше с прозрачностью).\nАвтокомпоновка используется, когда в RSS-записи есть изображение.",
        "status_added": "добавлен",
        "status_not_added": "не добавлен",
        "btn_edit_template_image": "🖼 Шаблон",
        "btn_edit_watermark": "🏷 Водяной знак",
        "btn_add_asset": "➕ Добавить",
        "btn_replace_asset": "♻️ Заменить",
        "btn_delete_asset": "🗑 Удалить",
        "asset_manage_template_title": "🖼 Управление шаблоном",
        "asset_manage_watermark_title": "🏷 Управление водяным знаком",
        "asset_manage_template_help": "Здесь можно управлять изображением шаблона.",
        "asset_manage_watermark_help": "Здесь можно управлять водяным знаком.",
        "asset_manage_status": "Текущий статус: {status}",
        "asset_prompt_send_template": "Отправьте одно изображение для шаблона/фона (как фото или документ-изображение).",
        "asset_prompt_send_watermark": "Отправьте одно изображение для водяного знака/логотипа (как фото или документ-изображение).\n\nПодсказка: если нужно, фон можно удалить здесь: https://www.remove.bg/\nЛучше загружать PNG, желательно как файл (документ). Небольшая прозрачность обычно выглядит лучше.",
        "asset_saved_template": "✅ Шаблон сохранён.",
        "asset_saved_watermark": "✅ Водяной знак сохранён.",
        "asset_deleted_template": "✅ Шаблон удалён.",
        "asset_deleted_watermark": "✅ Водяной знак удалён.",
        "asset_upload_invalid": "Пожалуйста, отправьте изображение как фото или документ-изображение.",
        "asset_upload_error": "❌ Не удалось сохранить изображение. Попробуйте ещё раз.",
        "btn_source_link_on": "🔗 Ссылка на источник: ВКЛ",
        "btn_source_link_off": "🔗 Ссылка на источник: ВЫКЛ",
        "btn_feed_image_on": "🖼 Картинка из ленты: ВКЛ",
        "btn_feed_image_off": "🖼 Картинка из ленты: ВЫКЛ",
        "btn_rss_cta_on": "📣 CTA: ВКЛ",
        "btn_rss_cta_off": "📣 CTA: ВЫКЛ",
        "btn_bold_title_on": "🅱️ Жирный заголовок: ВКЛ",
        "btn_bold_title_off": "🅱️ Жирный заголовок: ВЫКЛ",
        "btn_add_emoji": "✨ Добавить эмодзи",
        "btn_delete_emoji": "🗑 Удалить эмодзи",
        "emoji_prompt_send": "Отправьте одним сообщением один или несколько эмодзи (включая premium/custom). Я сохраню это сообщение как источник стиля эмодзи.",
        "emoji_saved": "✅ Стиль эмодзи сохранён.",
        "emoji_deleted": "✅ Стиль эмодзи удалён.",
        "rss_cta_prompt": "Отправьте CTA-текст одним сообщением. Он будет добавляться к каждому RSS-посту, когда CTA включён.",
        "rss_cta_saved": "✅ CTA-текст сохранён.",
        "btn_schedule_rss": "📰 Расписание RSS + AI",
        "btn_schedule_creative": "✨ Расписание Creative",
        "btn_schedule_edit": "✍️ Изменить расписание",
        "btn_schedule_edit_interval": "⏱ Изменить интервал",
        "btn_posting_mode_scheduled": "🔁 Режим: По времени",
        "btn_posting_mode_interval": "🔁 Режим: По интервалу",
        "btn_schedule_toggle_on": "✅ Включить",
        "btn_schedule_toggle_off": "⏸ Выключить",
        "interval_input_instructions": "Отправьте интервал в минутах (только число).\nПримеры: 60, 120, 180\n\nНапишите \"cancel\" для возврата.",
        "interval_invalid": "❌ Неверный интервал. Отправьте целое число в минутах (например: 60).",
        "interval_saved": "✅ Интервал сохранён: каждые {interval} мин.",
        "variation_level_title": "🎚 Вариативность. Выберите уровень:",
        "variation_level_value_low": "Низкий",
        "variation_level_value_balanced": "Сбалансированный",
        "variation_level_value_high": "Высокий",
        "post_types_title": "🧩 Типы постов. Включите один или несколько:",
        "post_type_educational": "Обучающий",
        "post_type_opinion": "Мнение",
        "post_type_story": "История",
        "post_type_checklist": "Чек-лист",
        "post_type_question": "Вопрос",
        "post_type_myth_vs_fact": "Миф vs Факт",
        "post_type_mini_case": "Мини-кейс",
        "creative_variety_title": "🎛 Настройки разнообразия Creative:",
        "creative_variety_note": "Настройки мягко добавляют вариативность, но главный приоритет у вашего Creative-промпта.",
        "creative_variety_summary": "Уровень: {level}\nТипы постов: {post_types}\nИзбегать повторов: {avoid}",
        "label_on": "ВКЛ",
        "label_off": "ВЫКЛ",
        "status_id": "ID",
        "status_channels": "Каналы",
        "status_rss_daily": "Доступно RSS постов/день",
        "status_creative_daily": "Доступно Creative постов/день",
        "status_valid_until": "Подписка активна до",
        "status_not_set": "не задано",
        "status_inactive": "не активна",
        "status_title": "📊 Статус аккаунта",
        "btn_setstyle": "✍️ Стиль",
        "btn_showstyle": "📄 Показать стиль",
        "btn_resetstyle": "♻️ Сбросить стиль",
        "btn_on": "🤖 Автопост ВКЛ",
        "btn_off": "🛑 ВЫКЛ",
        "modes_help": "Выберите режим командами:\n/mode rss\n/mode creator\n/mode both",
        "prompt_current": "Текущий промпт:\n{prompt}",
        "prompt_current_rss": "Текущий промпт RSS + AI:\n{prompt}",
        "prompt_current_creative": "Текущий промпт Creative:\n{prompt}",
        "prompt_empty": "Промпт пока не сохранён. Используется стиль по умолчанию.",
        "prompt_edit_instructions": "Отправьте готовый промпт одним сообщением. Напишите \"cancel\", чтобы оставить текущий без изменений.",
        "prompt_edit_cancel_hint": "Напишите \"cancel\", чтобы оставить текущий промпт без изменений.",
        "prompt_guidance_creative": (
            "Как написать хороший Creative-промпт для Telegram:\n"
            "• Тема/ниша: о чём именно вы пишете.\n"
            "• Тон/голос: экспертный, дружелюбный, дерзкий и т.д.\n"
            "• Аудитория: для кого ваш канал.\n"
            "• Длина: типичный объём в строках/символах.\n"
            "• Структура: хук → основные мысли → вывод.\n"
            "• CTA: мягкий призыв, вопрос, переход в ЛС, ссылка и т.д.\n"
            "• Избегать: клише, кликбейта, запрещённых/нерелевантных тем.\n\n"
            "Шаблон (скопируйте и отредактируйте):\n"
            "Ты пишешь Telegram-посты для [ниша].\n"
            "Тон: [тон/голос]. Аудитория: [целевая аудитория].\n"
            "Объём каждого поста: [длина].\n"
            "Структура: 1) цепляющий хук, 2) 2–4 практичные мысли/примера, 3) короткий вывод, 4) CTA: [стиль CTA].\n"
            "Избегай: [что избегать]."
        ),
        "prompt_guidance_rss": (
            "Как написать хороший RSS + AI промпт для Telegram:\n"
            "• Преобразование контента: переписывай в вашем стиле, не копируй текст.\n"
            "• Тон/голос: деловой, нейтральный, энергичный и т.д.\n"
            "• Формат саммари: короткий дайджест или более подробное объяснение.\n"
            "• Длина: типичный объём в строках/символах.\n"
            "• Мнение: добавлять ваш комментарий или строго нейтрально.\n"
            "• Завершение/CTA: вопрос, подписка, репост, без призыва.\n"
            "• Избегать: выдуманных фактов, хайпа, повторов, слишком длинных вступлений.\n\n"
            "Шаблон (скопируйте и отредактируйте):\n"
            "Переписывай RSS/новости в Telegram-посты в тоне [тон].\n"
            "Формат: короткий хук + понятное саммари + ключевой вывод.\n"
            "Объём: [длина].\n"
            "Режим мнения: [нейтрально / добавить краткий комментарий].\n"
            "Завершение: [CTA или без CTA].\n"
            "Избегай: [что избегать]."
        ),
        "prompt_edit_cancelled": "Промпт не изменён.",
        "prompt_edit_saved": "✅ Промпт обновлён.",
        "prompt_builder_intro_creative": "🪄 AI-конструктор промпта (Creative)\n\nЯ задам несколько коротких вопросов и соберу готовый Creative-промпт.\n\nВ любой момент напишите \"cancel\" для выхода.",
        "prompt_builder_intro_rss": "🪄 AI-конструктор промпта (RSS + AI)\n\nЯ задам несколько коротких вопросов и соберу готовый RSS + AI промпт.\n\nВ любой момент напишите \"cancel\" для выхода.",
        "prompt_builder_q_creative_1": "1/7 Какая у вас ниша/тема?\n\nПримеры:\n• местные футбольные новости\n• обновления по киберспорту\n• питание для бегунов",
        "prompt_builder_q_creative_2": "2/7 Кто ваша целевая аудитория?\n\nПримеры:\n• футбольные фанаты\n• болельщики Барселоны\n• широкая спортивная аудитория\n• обычная Telegram-аудитория",
        "prompt_builder_q_creative_3": "3/7 Какой тон должен быть у постов?\n\nПримеры:\n• профессиональный новостной стиль\n• дружелюбный голос фаната\n• нейтрально-информативный\n• энергичный спортивный комментарий",
        "prompt_builder_q_creative_4": "4/7 Какие типы постов вам нужны чаще всего?\n\nПримеры:\n• короткие новостные выжимки\n• мнения\n• чеклисты\n• посты в формате вопрос-ответ",
        "prompt_builder_q_creative_5": "5/7 Какой примерно размер поста вы хотите?\n\nНапример:\n• короткий пост (2–3 предложения)\n• средний пост (4–6 предложений)\n• до ~100 слов",
        "prompt_builder_q_creative_6": "6/7 Чего нужно избегать?\n\nПримеры:\n• кликбейта\n• сленга\n• политических тем\n• агрессивной подачи",
        "prompt_builder_q_creative_7": "7/7 На каком языке должны быть посты? (English/Русский)",
        "prompt_builder_q_rss_1": "1/7 О чём лента/тематика?\n\nПримеры:\n• трансферы в футболе\n• турниры по киберспорту\n• новости о стартапах",
        "prompt_builder_q_rss_2": "2/7 Кто ваша целевая аудитория?\n\nПримеры:\n• футбольные фанаты\n• болельщики Барселоны\n• широкая спортивная аудитория\n• обычная Telegram-аудитория",
        "prompt_builder_q_rss_3": "3/7 Какой тон должен быть у постов?\n\nПримеры:\n• профессиональный новостной стиль\n• дружелюбный голос фаната\n• нейтрально-информативный\n• энергичный спортивный комментарий",
        "prompt_builder_q_rss_4": "4/7 Какой примерно размер поста вы хотите?\n\nНапример:\n• короткий пост (2–3 предложения)\n• средний пост (4–6 предложений)\n• до ~100 слов",
        "prompt_builder_q_rss_5": "5/7 Нейтральные саммари или более выразительный авторский угол?\n\nПримеры:\n• в основном нейтральная выжимка\n• короткий редакторский акцент",
        "prompt_builder_q_rss_6": "6/7 Чего нужно избегать?\n\nПримеры:\n• хайпа\n• повторов\n• слишком большого числа хештегов\n• длинных вступлений",
        "prompt_builder_q_rss_7": "7/7 На каком языке должны быть посты? (English/Русский)",
        "prompt_builder_generating": "⏳ Генерирую промпт...",
        "prompt_builder_review": "Вот сгенерированный промпт:\n\n{prompt}\n\nСохранить его для этого режима?",
        "prompt_builder_saved": "✅ Промпт сохранён для этого режима.",
        "prompt_builder_cancelled": "Конструктор промпта отменён. Изменения не сохранены.",
        "prompt_builder_error": "❌ Сейчас не удалось сгенерировать промпт. Попробуйте ещё раз.",
        "copy_style_intro": "Отправьте мне 3 поста из вашего канала.\nЯ проанализирую тон, подачу и структуру и создам промпт в вашем стиле.",
        "copy_style_progress": "Получил. Отправьте ещё {left} пост{suffix}.",
        "copy_style_invalid": "Пожалуйста, отправьте текстовые посты, чтобы я мог проанализировать стиль.",
        "copy_style_success": "✅ Готово. Промпт для этого режима обновлён по вашему стилю.",
        "copy_style_loading": "Готово. Подготавливаю промпт, это займёт несколько секунд.",
        "copy_style_review": "Промпт в вашем стиле готов.\n\n{prompt}\n\nПеред сохранением можно добавить детали: язык постов, размер, чего избегать, для какой аудитории писать, CTA/концовку и писать нейтрально или с комментариями.\nМожно сохранить его сразу или сначала отредактировать. Вы также можете скопировать весь промпт, поправить его и отправить обратно финальную версию.",
        "copy_style_edit_ready": "Ниже сгенерированный черновик. Отредактируйте его и отправьте финальную версию:\n\n{prompt}",
        "btn_save": "💾 Сохранить",
        "btn_edit": "✍️ Редактировать",
        "btn_regenerate": "🔄 Перегенерировать",
        "btn_cancel": "❌ Отмена",
        "feeds_empty": "Ленты пока не добавлены.",
        "feed_added": "✅ Лента добавлена.",
        "feed_deleted": "✅ Лента удалена.",
        "channel_deleted": "✅ Канал удалён.",
        "channel_empty": "Канал не настроен.",
        "channels_list_title": "Сохранённые каналы ({count}/{slots}):",
        "channels_empty_state": "Пока нет сохранённых каналов.\nДоступно слотов: {slots}.",
        "channel_choose_delete": "Выберите канал для удаления:",
        "channel_deleted_named": "✅ Канал удалён: {channel}",
        "channel_slots_limit": "Достигнут лимит каналов ({count}/{slots}). Увеличьте доступ, чтобы добавить ещё канал.",
        "channel_picker_title": "Выберите канал, чтобы продолжить:",
        "channel_picker_empty": "Каналы не найдены. Сначала добавьте канал в управлении каналами.",
        "channel_selected_now": "📌 Выбран канал: {channel}",
        "start_welcome": (
            "👋 Добро пожаловать в Postora.\n\n"
            "Я помогаю создавать и публиковать посты по расписанию для вашего Telegram-канала.\n\n"
            "Чтобы начать, откройте ⚙️ Настройку, выберите режим, подключите канал и задайте промпт, ленты и расписание.\n"
            "Тариф и оплату можно настроить отдельно в любое время."
        ),
    },
}
