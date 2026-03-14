# Config Persistence Audit (diagnostic)

This document records an inspection of runtime persistence behavior for client configuration.

## Storage path logic

- `BASE_DIR` is the directory containing `main.py`.
- `CLIENTS_DIR = BASE_DIR / "clients"`.
- Per-user config file path is `clients/<user_id>.json` via `client_path(user_id)`.
- Per-user custom style text is stored in `clients/<user_id>_style.txt` via `custom_style_path(user_id)`.

## Central persistence helpers

- `load_client(user_id)`
  - Creates default config + saves immediately when file does not exist.
  - Loads JSON and recovers to defaults on parse errors (writes `*.broken.json`).
  - Applies `setdefault()` from `DEFAULT_CLIENT` for missing keys.
  - Calls `normalize_channels`, `ensure_channel_settings`, `apply_active_channel_settings`.
- `save_client(user_id, cfg)`
  - Calls `normalize_channels`, `ensure_channel_settings`, `persist_active_channel_settings`.
  - Writes JSON back to `clients/<user_id>.json`.
- `normalize_channels(cfg)`
  - Maintains legacy `channel` field as first entry in `channels`.
- `ensure_channel_settings(cfg)` / `apply_active_channel_settings(cfg)` / `persist_active_channel_settings(cfg)`
  - Maintains per-channel bucket in `channel_settings` for `CHANNEL_SCOPED_KEYS`.

## Effective persisted shape

`DEFAULT_CLIENT` includes both old and new fields. Important groups:

- Legacy/global keys still present: `channel`, `daily_limit`, `style_file`, `schedule_enabled`, `schedule_times`, `last_schedule_*`.
- Multi-channel keys: `channels`, `channel_slots`, `channel_settings`.
- Mode limits: `rss_daily_limit`, `creative_daily_limit`.
- Creative diversification: `creative_variation_level`, `creative_post_types`, `creative_avoid_repetition`.
- RSS output toggles: `include_rss_source_link`, `use_rss_feed_image`.
- Mode scheduling keys: `rss_schedule_*`, `creative_schedule_*`.
- Prompt keys: `rss_prompt`, `creative_prompt` (channel-scoped).

Also observed: existing sample client JSON files in `clients/` are still mostly legacy and do not yet contain many of these new keys until the user config is saved again.

## Feature status summary

1) Multi-channel storage
- Status: **persisted in client JSON**.
- Evidence: `channels` list + `channel_settings` dict persisted via save helpers.
- Note: posting loop still sends only to active legacy `channel` (single channel at a time).

2) Channel slots entitlement
- Status: **persisted in client JSON**.
- `channel_slots` used to enforce `/setchannel` add limit and admin `/setchannels` writes it.

3) Separate RSS and Creative daily limits
- Status: **persisted in client JSON**.
- `rss_daily_limit` and `creative_daily_limit` are stored and used by mode paywall/counters.
- Legacy `daily_limit` still exists and can still be written by admin command.

4) Separate RSS and Creative prompts
- Status: **persisted in client JSON**.
- `rss_prompt` and `creative_prompt` are saved.
- Fallback reads legacy prompt keys (`prompt`, `style_prompt`) and style file if mode prompt absent.

5) Per-channel vs per-user prompt storage
- Status: **persisted per-channel (with active-channel overlay)**.
- Prompt keys are in `CHANNEL_SCOPED_KEYS` and mirrored through `channel_settings[channel]`.

6) RSS settings toggles
- include source link ON/OFF: **persisted** (`include_rss_source_link`).
- use feed image ON/OFF: **persisted** (`use_rss_feed_image`).
- Both are channel-scoped keys.

7) Scheduling settings
- Status: **partially persisted / mixed legacy + new behavior**.
- New per-mode settings persist (`rss_schedule_*`, `creative_schedule_*`, `<mode>_use_interval`).
- Legacy `/schedule` command still writes global `schedule_*` keys.
- Runtime `mode_schedule_state()` falls back to legacy `schedule_*` if mode-specific times are empty.

8) Creative diversification settings
- variation level / post types / avoid repetition: **persisted in client JSON**.
- Current scope: global per user config (not channel-scoped).

9) Builder-selected language / content language
- Status: **not saved as standalone config field**.
- Builder language answer affects generated prompt text (`Output language: ...`) and that prompt is persisted if saved.
- Raw builder answers live in `context.user_data` during interaction only.

10) Other newly added mode/channel settings
- Channel-scoped persistence exists for: feeds, posted_urls, prompts, rss output toggles, per-mode schedules.
- But autopost loop loads one client config and posts to only `cfg["channel"]`.

## Redeploy survivability

- Any value written to `clients/<user_id>.json` survives process restart/redeploy (assuming persistent volume remains mounted).
- Any `context.user_data` state does not survive restart.
- Existing users with legacy JSON shape keep working via `setdefault` + normalization; new keys may exist in-memory after load and become materialized in file on next `save_client`.
