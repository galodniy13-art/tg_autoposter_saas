TEXTS = {
    "en": {
        "welcome": "Welcome!",
        "menu_title": "Menu. Choose an action:",
        "mode_usage": "Usage: /mode rss OR /mode creator OR /mode both",
        "payment_offer":
            "💳 Access pricing (EUR/month):\n\n"
            "RSS mode:\n"
            "• 10 posts/day — €9/month\n"
            "• 20 posts/day — €15/month\n"
            "• 30 posts/day — €21/month\n\n"
            "Creative mode:\n"
            "• 5 posts/day — €7/month\n"
            "• 10 posts/day — €12/month\n"
            "• 20 posts/day — €20/month\n\n"
            "You can combine RSS + Creative access.\n"
            "To activate, message: @a_karaglan, @a_karaglanov",
        "btn_modes": "🧠 Modes",
        "btn_scheduling": "🕒 Scheduling",
        "modes_title": "🧠 Modes. Choose a mode settings section:",
        "mode_rss_ai": "📰 RSS + AI",
        "mode_creative": "✨ Creative",
        "creative_locked": "🔒 Creative mode is unavailable for your account.",
        "rss_locked": "🔒 RSS + AI mode is unavailable for your account.",
        "creative_paywall":
            "Creative mode pricing (EUR/month):\n"
            "• 5/day — €7/month\n"
            "• 10/day — €12/month\n"
            "• 20/day — €20/month\n\n"
            "To activate, message: @a_karaglan, @a_karaglanov",
        "rss_paywall":
            "RSS mode pricing (EUR/month):\n"
            "• 10/day — €9/month\n"
            "• 20/day — €15/month\n"
            "• 30/day — €21/month\n\n"
            "To activate, message: @a_karaglan, @a_karaglanov",
        "mode_set_rss": "✅ Mode set: 📰 RSS + AI",
        "mode_set_creator": "✅ Mode set: ✨ Creative",
        "btn_payment": "💳 Payment",
        "btn_back": "⬅ Back",
        "btn_back_main": "⬅ Back to Main Menu",
        "btn_autopost_on": "🤖 Autopost: ON",
        "btn_autopost_off": "🤖 Autopost: OFF",
        "setup_menu_title": "⚙️ Setup:",
        "scheduling_menu_title": "🕒 Scheduling:",
        "channel_management_title": "📺 Channel management:",
        "modes_menu_title": "🧠 Modes settings:",
        "creative_menu_title": "✨ Creative settings:",
        "rss_menu_title": "📰 RSS + AI settings:",
        "schedule_mode_title_rss": "📰 RSS + AI schedule",
        "schedule_mode_title_creative": "✨ Creative schedule",
        "schedule_current": "Current schedule:\n{schedule}",
        "schedule_input_instructions": "Send posting times in 24h format, comma-separated.\nExamples:\n09:00\n09:00, 15:00, 21:30\n\nSend \"clear\" to remove all slots.",
        "schedule_invalid": "❌ Invalid format. Use HH:MM or HH:MM, HH:MM",
        "schedule_saved": "✅ Schedule saved.",
        "schedule_cleared": "✅ Schedule cleared.",
        "schedule_enabled": "✅ Schedule turned ON.",
        "schedule_disabled": "⏸ Schedule turned OFF.",
        "preview_no_feeds": "No feeds. Add one first: /addfeed <url>",
        "feed_management_title": "🧾 Feed management:",
        "btn_lang": "🌐 Language",
        "choose_lang": "Choose your language:",
        "btn_setup": "🛠 Setup",
        "btn_help": "❓ Help",
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
        "btn_preview": "🧪 Preview",
        "btn_edit_feeds": "🧾 Edit Feeds",
        "btn_schedule_rss": "📰 RSS + AI Schedule",
        "btn_schedule_creative": "✨ Creative Schedule",
        "btn_schedule_edit": "✍️ Edit Schedule",
        "btn_schedule_toggle_on": "✅ Turn ON",
        "btn_schedule_toggle_off": "⏸ Turn OFF",
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
        "start_welcome": (
            "👋 Welcome to AI autoposting for influencers.\n\n"
            "This bot helps you publish on Telegram using AI in two modes:\n"
            "• RSS + AI — takes news from RSS and rewrites it in your style\n"
            "• Creative — generates original expert/creator posts\n\n"
            "Start here:\n"
            "1) ⚙️ Setup\n"
            "2) Connect channel (/setchannel @yourchannel)\n"
            "3) Choose mode (/mode rss or /mode creator)"
        ),
    },
    "ru": {
        "welcome": "Добро пожаловать!",
        "menu_title": "Меню. Выберите действие:",
        "mode_usage": "Использование: /mode rss ИЛИ /mode creator ИЛИ /mode both",
        "payment_offer":
            "💳 Стоимость доступа (EUR/месяц):\n\n"
            "RSS-режим:\n"
            "• 10 постов/день — €9/месяц\n"
            "• 20 постов/день — €15/месяц\n"
            "• 30 постов/день — €21/месяц\n\n"
            "Creative-режим:\n"
            "• 5 постов/день — €7/месяц\n"
            "• 10 постов/день — €12/месяц\n"
            "• 20 постов/день — €20/месяц\n\n"
            "Можно комбинировать RSS + Creative доступ.\n"
            "Для активации напишите: @a_karaglan, @a_karaglanov",
        "btn_modes": "🧠 Режимы",
        "btn_scheduling": "🕒 Расписание",
        "modes_title": "🧠 Режимы. Выберите раздел настроек:",
        "mode_rss_ai": "📰 RSS + AI",
        "mode_creative": "✨ Creative",
        "creative_locked": "🔒 Режим Creative недоступен для вашего аккаунта.",
        "rss_locked": "🔒 Режим RSS + AI недоступен для вашего аккаунта.",
        "creative_paywall":
            "Стоимость Creative-режима (EUR/месяц):\n"
            "• 5/день — €7/месяц\n"
            "• 10/день — €12/месяц\n"
            "• 20/день — €20/месяц\n\n"
            "Для активации напишите: @a_karaglan, @a_karaglanov",
        "rss_paywall":
            "Стоимость RSS-режима (EUR/месяц):\n"
            "• 10/день — €9/месяц\n"
            "• 20/день — €15/месяц\n"
            "• 30/день — €21/месяц\n\n"
            "Для активации напишите: @a_karaglan, @a_karaglanov",
        "mode_set_rss": "✅ Режим установлен: 📰 RSS + AI",
        "mode_set_creator": "✅ Режим установлен: ✨ Creative",
        "btn_payment": "💳 Оплата",
        "btn_back": "⬅ Назад",
        "btn_back_main": "⬅ В главное меню",
        "btn_autopost_on": "🤖 Автопост: ВКЛ",
        "btn_autopost_off": "🤖 Автопост: ВЫКЛ",
        "setup_menu_title": "⚙️ Настройка:",
        "scheduling_menu_title": "🕒 Расписание:",
        "channel_management_title": "📺 Управление каналом:",
        "modes_menu_title": "🧠 Настройки режимов:",
        "creative_menu_title": "✨ Настройки Creative:",
        "rss_menu_title": "📰 Настройки RSS + AI:",
        "schedule_mode_title_rss": "📰 Расписание RSS + AI",
        "schedule_mode_title_creative": "✨ Расписание Creative",
        "schedule_current": "Текущее расписание:\n{schedule}",
        "schedule_input_instructions": "Отправьте время публикаций в формате 24ч через запятую.\nПримеры:\n09:00\n09:00, 15:00, 21:30\n\nОтправьте \"clear\", чтобы удалить все слоты.",
        "schedule_invalid": "❌ Неверный формат. Используйте HH:MM или HH:MM, HH:MM",
        "schedule_saved": "✅ Расписание сохранено.",
        "schedule_cleared": "✅ Расписание очищено.",
        "schedule_enabled": "✅ Расписание включено.",
        "schedule_disabled": "⏸ Расписание выключено.",
        "preview_no_feeds": "Нет RSS-лент. Сначала добавьте: /addfeed <url>",
        "feed_management_title": "🧾 Управление лентами:",
        "btn_lang": "🌐 Язык",
        "choose_lang": "Выберите язык:",
        "btn_setup": "🛠 Настройка",
        "btn_help": "❓ Помощь",
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
        "btn_preview": "🧪 Превью",
        "btn_edit_feeds": "🧾 Изменить ленты",
        "btn_schedule_rss": "📰 Расписание RSS + AI",
        "btn_schedule_creative": "✨ Расписание Creative",
        "btn_schedule_edit": "✍️ Изменить расписание",
        "btn_schedule_toggle_on": "✅ Включить",
        "btn_schedule_toggle_off": "⏸ Выключить",
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
        "start_welcome": (
            "👋 Добро пожаловать в AI-автопостинг для инфлюенсеров.\n\n"
            "Бот помогает публиковать в Telegram с помощью ИИ в двух режимах:\n"
            "• RSS + AI — берёт новости из RSS и переписывает в вашем стиле\n"
            "• Creative — генерирует оригинальные экспертные/авторские посты\n\n"
            "С чего начать:\n"
            "1) ⚙️ Настройка\n"
            "2) Подключите канал (/setchannel @вашканал)\n"
            "3) Выберите режим (/mode rss или /mode creator)"
        ),
    },
}
