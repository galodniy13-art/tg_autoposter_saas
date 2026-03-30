# Creative Mode Product/UX Audit (User-Journey + Weak Points)

## Scope and method
- Audit type: product/UX only (no code changes/fixes), based on current bot flow implementation and user-facing copy.
- Core journey audited: entering Creative mode → understanding value → "Понять канал" (Understand Channel) → "Банк идей" (Idea Bank) → campaigns → publication settings → preview → ongoing management.
- Persona simulation used realistic business intent and time pressure, not technical/admin assumptions.

---

## 1) Executive summary
Creative mode has a **clear high-level promise** (a 5-step path) and some genuinely strong strategic blocks (channel intake, campaign object, idea bank generation, preview, per-channel context). However, as shipped, it still feels **partially productized** rather than commercially "finished" for non-technical paying users.

Main reason: the UX currently asks users to perform many manual, text-heavy steps while **hiding or fragmenting key value loops** (e.g., source center/content plan/variety are implemented but not visible in the main Creative menu). This creates a confidence gap: users see capability, but not a cohesive, guided system.

Commercially, the mode is promising but not yet strong enough for broad self-serve conversion because:
1. setup friction is high for busy users,
2. campaign lifecycle is weak after creation,
3. "what happens next" is unclear in several branches,
4. quota/usage implications are not made visible at decision points.

Verdict: **Strong foundation, medium UX maturity, high monetization upside after flow hardening.**

---

## 2) Persona-by-persona findings

### Persona 1 — Solo creator selling a course
**Goal:** warm audience and convert over time; campaign logic must make sense.

**What works**
- Campaign creation asks for relevant conversion inputs (goal, offer, CTA, awareness, objections, benefits, urgency) and auto-generates a day-by-day arc. This matches real creator launch workflows.
- Active campaign context is injected into generation, so posts can be aligned with campaign intent.

**Pain points**
- Campaign progression is static in practice: post generation always uses the **first arc item** instead of evolving day-by-day, which weakens narrative progression over time.
- After campaign creation, there is no explicit lifecycle dashboard (e.g., "today is day 3", "next stage"), so conversion sequencing feels opaque.
- Activation requires typing campaign number manually; no one-tap selection, more cognitive load.

**Business impact**
- This persona can start fast but may distrust whether the system truly runs strategic warming/conversion sequencing.

---

### Persona 2 — Small expert/business owner
**Goal:** simple setup; bot should understand channel and produce useful content.

**What works**
- "Understand Channel" questionnaire gathers high-value strategic context (audience, pains, offers, tone, goals, good/bad examples).
- Saved intake is summarized clearly and reused in generation.

**Pain points**
- Intake is 10 open-ended questions in chat; high effort before perceived payoff.
- No quality guardrails in intake flow (e.g., if answers are too vague, flow still proceeds).
- Idea bank generation is useful, but users are not clearly told how to turn ideas into a repeatable weekly publishing loop from Creative home.

**Business impact**
- Good strategic depth, but setup can feel heavy for small businesses expecting "quickly useful" output.

---

### Persona 3 — Busy admin wanting idea support, not complexity
**Goal:** quick wins; avoid feature overwhelm.

**What works**
- Main Creative menu is short (5 items), which lowers first-screen overwhelm.
- Preview is one tap and helps verify output quickly.

**Pain points**
- Short menu hides important capabilities already implemented (content plan, source center, variety, visual support), creating discoverability mismatch and uncertainty about "what this product really includes".
- Multiple branches require extra channel picking and manual text input; flow feels operational rather than assistant-like.
- Publication settings are split and somewhat generic; "what minimum I must set to go live" for Creative is not as explicit as RSS quickstart patterns.

**Business impact**
- Fast first impression, but confidence drops as soon as user wants structured ongoing management.

---

### Persona 4 — User who does not understand prompts
**Goal:** results without prompt-engineering skill.

**What works**
- Guided Prompt Builder exists for Creative.
- Channel intake and campaign forms reduce need for writing one perfect mega-prompt.

**Pain points**
- Prompt still remains a primary dependency in several generators; if absent/weak, system falls back but does not coach quality deeply.
- Some labels are expert/internal-sounding (e.g., "Source Center", "Variation level", "Avoid repetition") without concrete expected outcome examples inline.
- User can produce content without understanding why quality is good/bad, reducing trust and retention.

**Business impact**
- Better than prompt-only tools, but still not fully "promptless" in user perception.

---

## 3) Top issues ranked by severity

### Critical (P1)
1. **Campaign arc does not operationally progress by day in generation loop**
   - Arc is generated, but content generation takes first arc item, so long-form conversion logic can degrade into static messaging.
   - Risk: core monetization promise (strategic campaign automation) appears weaker than expected.

2. **Core capability discoverability gap from Creative home**
   - Main Creative menu exposes only intake/idea bank/campaigns/publishing/preview while other strategic modules exist elsewhere.
   - Risk: users perceive product as shallower than actual capability, reducing activation and paid retention.

### High (P2)
3. **High setup friction in channel intake for mainstream users**
   - 10 open-ended questions with no progressive simplification mode.

4. **Weak post-setup guidance / missing “next best action” in Creative flow**
   - Users can complete steps but still not know optimal next move.

5. **Quota/usage clarity not surfaced contextually in Creative journey**
   - Daily limit exists and shows in status/paywall, but not prominently at action points where usage decisions happen.

### Medium (P3)
6. **Activation/selection interactions rely on manual number input**
   - Campaign activation by typed ID adds unnecessary friction.

7. **Terminology density for non-technical users**
   - Some labels lack plain-language benefit framing.

8. **Limited safeguards on low-quality or empty strategic inputs**
   - System accepts very weak responses and proceeds, which can silently reduce output quality.

---

## 4) What is strong right now
- Clear top-level 5-step framing in Creative menu copy.
- Strong strategic data model behind intake + campaigns + sources.
- Per-channel context handling is implemented across major Creative routes.
- Preview flow exists and gives immediate quality check.
- Campaign questionnaire captures real conversion-relevant dimensions.

These are substantial strengths and are a good base for a commercially strong Creative product.

---

## 5) What still feels unfinished
1. **Journey coherence:** features feel like modules, not one guided system.
2. **Lifecycle UX:** creation flows are stronger than management/progression flows.
3. **Commercial instrumentation in UX:** value and usage economics are under-communicated in context.
4. **Prompt abstraction:** still partly expert-oriented despite guidance.
5. **Outcome visibility:** user cannot easily see strategic state (campaign phase, weekly plan status, content diversity status) from one place.

---

## 6) Exact recommended next fixes (ordered)

### 1) Fix campaign progression logic visibility and execution (highest ROI)
- Make campaign arc truly day-aware in generation (not static first-item behavior).
- Add simple campaign state panel: active campaign, current day/stage, next CTA focus.
- Surface this state from Campaigns and Preview screens.

### 2) Turn Creative home into a guided operating system
- Keep existing 5-step simplicity, but add "Advanced tools" entry that exposes Source Center, Content Plan, Variety, Visual Support.
- Add one-line value outcomes under each option (e.g., "reduces repeats", "improves conversion consistency").

### 3) Add Quick Start path for non-expert users
- Offer two setup modes in intake start: "Fast (3 questions)" vs "Full strategy (10 questions)".
- Use defaults/examples when users provide short answers.

### 4) Add proactive next-action hints after every key completion
- After intake save: suggest Idea Bank generate.
- After idea bank generate: suggest Campaign create or Content Plan generate.
- After campaign save: suggest Preview + publishing enable checklist.

### 5) Improve quota transparency inside Creative actions
- Show remaining Creative daily allowance in Creative menu header and before generation-heavy actions (Preview, Idea generation, plan generation).
- Clarify that daily limit is account-wide across channels at those touchpoints.

### 6) Reduce manual activation friction
- Replace typed campaign ID activation with inline selectable campaign buttons.
- Keep text fallback for power users.

### 7) Add lightweight safeguards for weak inputs
- Detect empty/vague intake or campaign responses and request clarification with examples.
- Add basic completion quality indicators (e.g., "context quality: low/medium/high").

### 8) Rename/clarify expert terms with benefit-first labels
- "Source Center" → "Knowledge for better posts" (or equivalent localized phrasing).
- "Variation Level" → "How different each post should feel".
- Keep internal structure, change user-facing clarity.

---

## Evidence map (code-backed)
- Creative main menu currently has 5 visible options only. (`keyboards.py`)
- Creative copy promises simple 5-step path. (`texts.py`)
- Channel intake uses 10 sequential questions. (`main.py`, `texts.py`)
- Campaign creation uses 8-step questionnaire and stores active campaign. (`main.py`, `texts.py`)
- Campaign arc generation exists, but post generation uses first arc item guidance. (`main.py`)
- Source Center / Content Plan / Variety / Visual Support flows exist in callbacks and keyboards but are not on primary Creative menu. (`main.py`, `keyboards.py`, `texts.py`)
- Creative access gated by daily limit/paywall; status shows daily limits. (`main.py`, `texts.py`)

