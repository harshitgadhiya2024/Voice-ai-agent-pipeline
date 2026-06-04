# Vibe Coding Prompt — Website Voice Bot + Chat Bot (Knowledge Base, Multi-Language)

Copy everything inside the **“PROMPT START”** block below into Cursor, Claude, or any coding agent when you want to build (or extend) a **production-style voice + chat assistant** for **your own website**, powered by **your knowledge base**.

Fill in the `[BRACKETS]` sections with your business details before pasting.

---

## How to use this file

1. Duplicate this file or copy the prompt block.
2. Replace every `[PLACEHOLDER]` with your real data (company name, URLs, languages, KB JSON path, etc.).
3. Paste into your AI coding tool as the **main task message**.
4. Point the agent at your repo (or ask it to scaffold a new monorepo).
5. Iterate: “implement Phase 1 only”, then voice, then chat, then polish.

---

## PROMPT START

You are a senior full-stack engineer building a **client-ready Voice AI + Chat AI assistant** for my website. Treat this like a **paid demo / production MVP** — not a toy chatbot.

### My business (fill these in)

| Field | My value |
|-------|----------|
| **Company / brand** | `[YOUR_COMPANY_NAME]` |
| **Website** | `[https://your-website.com]` |
| **What we do (1 sentence)** | `[e.g. We sell X and support customers in Y industry]` |
| **Primary audience** | `[e.g. students, buyers, patients, bank customers]` |
| **Bot name (female voice)** | `[e.g. Priya]` |
| **Bot name (male voice)** | `[e.g. Rahul]` |
| **Default language** | `[auto \| en \| hi \| gu]` |
| **Languages to support** | `[English, Hindi, Gujarati — add or remove]` |
| **Knowledge base source** | `[JSON file path / Notion export / scrape of site — describe]` |
| **Tone** | `[warm professional / formal / sales / support]` |
| **Compliance / disclaimer** | `[e.g. demo data only, not legal advice, verify on website]` |

### Product goals

Build **two ways** for users to talk to the same brain:

1. **Voice mode** — real-time microphone, VAD, STT, streaming LLM, TTS playback (like a phone call).
2. **Chat mode** *(optional — include only if I ask for chat UI)* — text input, same LangGraph agents, no STT/TTS, streaming tokens in a chat window.

Both modes must:

- Use **one shared knowledge base** (my company data — no hallucinated prices, dates, or policies).
- Support **multi-language**: English, Hindi, Gujarati, and **auto-detect** from user speech/text.
- Use **natural Indian spoken style** when replying in Hindi/Gujarati: **Hinglish / Guenglish** — keep brand names, product names, acronyms, URLs in **English (Latin script)** for correct TTS pronunciation (e.g. `LDCE`, `Computer Engineering`, `admission`, `ldce.ac.in`).
- Use **LangGraph** multi-agent routing (router → clarify missing info → specialist agent).
- Be suitable for **embedding on my marketing site** or a `/support` / `/assistant` page.

### Reference architecture (match this unless I say otherwise)

Use a proven stack (this is what works in production):

**Frontend**

- Next.js 14+ (App Router), TypeScript, Tailwind CSS
- Zustand for UI state
- Single WebSocket to backend: `ws://[API_HOST]/ws/voice`
- **Voice**: `@ricky0123/vad-web` (Silero VAD), AudioWorklet for 16 kHz PCM capture, gapless PCM playback for TTS
- **Half-duplex**: while bot is **thinking** or **speaking**, **mute mic + pause VAD**; resume only after TTS playback fully ends (handle gaps between audio chunks — do not reopen mic mid-sentence)
- Env: `NEXT_PUBLIC_WS_URL`, `NEXT_PUBLIC_API_URL`, optional `NEXT_PUBLIC_AUTO_LISTEN=false` (listen only after TTS ends unless true)

**Backend**

- FastAPI, async WebSocket, Python 3.11+
- **STT**: Sarvam Saaras v3 (`language_code=unknown` for auto EN/HI/GU)
- **LLM**: Groq `llama-3.3-70b-versatile` (streaming tokens)
- **TTS**: Sarvam Bulbul v3 (`priya` female, `rahul` male), 24 kHz PCM over WebSocket binary frames
- **Agents**: LangGraph `StateGraph` — one generic graph, **config-driven** use cases / domains

**Pipeline (voice)**

```
Mic → VAD → PCM chunks → WS → STT → transcript
     → LangGraph (router + slots + specialist + my KB)
     → stream LLM tokens → sentence chunking → TTS → PCM → gapless playback
```

### Knowledge base requirements

1. Store my data as structured JSON, e.g. `backend/knowledge/data/[my_id].json` or per vertical under `backend/use_cases/`.
2. Include realistic fields for my domain: FAQs, pricing notes, contact, policies, product catalog, locations, hours, etc.
3. Provide a loader: `context_for_intent(intent_id)` returns only the JSON slice that agent needs.
4. **Hard rule for LLM**: answer **only** from knowledge JSON; if missing, say “check [website] or contact [phone/email]” — never invent numbers.

Example JSON shape (adapt to my business):

```json
{
  "id": "my_brand",
  "name": "Full Legal Name",
  "short_name": "Brand",
  "website": "https://example.com",
  "about": "...",
  "contact": { "phone": "...", "email": "...", "hours": "..." },
  "products_or_services": [],
  "policies": {},
  "faqs": []
}
```

### LangGraph agent design

Implement **one reusable graph** for all topics:

| Node | Role |
|------|------|
| `router` | Classify user message → `intent` + extract `slots` + list `missing_slots` |
| `clarify` | If required slots missing → one short follow-up question |
| `specialist` | Answer using KB for that intent |

Define intents for **my** business (example set — replace):

- `general` — about us, contact, hours
- `[intent_2]` — e.g. pricing / menu / listings
- `[intent_3]` — e.g. booking / order / application
- `[intent_4]` — e.g. support / returns / complaints

Each intent has:

- `required_slots` (e.g. `location`, `date`, `product_id`)
- `knowledge_keys` (which JSON sections to inject)
- `slot_questions` for clarify node fallback

Persist slots per WebSocket `session_id` across turns.

### LLM system prompt rules (mandatory)

Include in every specialist + clarify prompt:

**Voice / speakability**

- Output is read by TTS: 1–3 short spoken sentences, no markdown, no bullet lists.
- Sound like a real human on a phone call.

**Multi-language**

- Match user language (EN / HI / GU or auto-detected).
- Hindi/Gujarati replies: natural code-mixing; **keep in English script**: company name, product names, technical terms, acronyms, URLs, branch names, `UG`, `PG`, `fees`, `admission`, etc.
- Example Hinglish: “`[BRAND]` में `Computer Engineering` की admission `ACPC` counselling से होती है। details के लिए `[website]` check कर सकते हैं।”

**Persona**

- Female voice → feminine Hindi/Gujarati grammar (करती हूँ, बताती हूँ).
- Male voice → masculine (करता हूँ, बताता हूँ).
- Use my bot names: `[FEMALE_NAME]` / `[MALE_NAME]`.

### WebSocket protocol

**Client → server (JSON)**

| type | purpose |
|------|---------|
| `speech_end` | User finished speaking (VAD) |
| `set_language` | `en` \| `hi` \| `gu` \| `auto` |
| `set_voice_gender` | `female` \| `male` |
| `set_use_case` | Switch KB / agent profile (if multiple) |
| `text_message` | Chat-only turn `{ text }` *(if chat UI enabled)* |
| `clear_history` | Reset conversation |
| `end_session` | End call + request session report |
| `ping` | keepalive |

**Server → client**

| type | purpose |
|------|---------|
| `ready` | Connected + metadata |
| `transcript` | STT result |
| `llm_token` | Streaming reply token |
| `tts_start` / binary PCM | Start speaking |
| `tts_end` | Server done sending audio |
| `status` | `idle` \| `listening` \| `thinking` \| `speaking` |
| `text_done` | Chat turn complete *(if chat)* |
| `session_report` | Summary + entities + full transcript |
| `error` | User-visible error |

**Critical**: Do not send `status: idle` after LLM finishes if TTS is still playing locally. Client resumes mic only after playback queue drains + `tts_end` + debounce between chunks.

### Frontend pages to build

1. **Landing / gallery** (optional) — cards for each use case or single “Talk to us” CTA.
2. **Assistant page** — `VoiceBot` widget:
   - Mic toggle, status (Listening / Thinking / Speaking — mic paused)
   - Language + voice gender selectors
   - Live transcript panel (user + bot)
   - Audio visualizer during TTS
   - Session report modal on end (summary, entities, conversation log)
3. **Chat panel** *(only if I explicitly want chat)* — side or tab; same WS, `text_message` only.

Embed path for my website: iframe or React component export `[AssistantWidget]`.

### Environment variables

**Backend `.env`**

```env
GROQ_API_KEY=
SARVAM_API_KEY=
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000,https://[MY_DOMAIN]
DEFAULT_LANGUAGE=auto
```

**Frontend `.env.local`**

```env
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/voice
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AUTO_LISTEN=false
```

### Implementation phases (do in order)

**Phase 1 — KB + LangGraph (text-only smoke test)**

- [ ] JSON knowledge base for `[YOUR_COMPANY_NAME]`
- [ ] Router + clarify + specialist nodes
- [ ] `stream_response()` with session slots
- [ ] CLI or `/chat` HTTP test returning JSON reply

**Phase 2 — WebSocket + voice pipeline**

- [ ] `VoiceSession` + worker queue per utterance
- [ ] Sarvam STT on `speech_end`
- [ ] Streaming LLM → sentence boundaries → Sarvam TTS
- [ ] Frontend: capture, VAD, playback, half-duplex gates

**Phase 3 — Multi-language + persona**

- [ ] Language selector + auto STT language
- [ ] `voice_speech_style_instruction()` for Hinglish/Guenglish
- [ ] Dynamic no-speech + error messages from LLM

**Phase 4 — Production polish**

- [ ] Session report + entity extraction
- [ ] Rate limits / max history length (20 messages)
- [ ] Health check `/health`
- [ ] Docker Compose
- [ ] README with setup steps

**Phase 5 — Website embed** *(optional)*

- [ ] Branded UI matching `[MY_BRAND_COLORS]`
- [ ] SEO page title/description
- [ ] CORS for production domain

### Acceptance tests (must pass before done)

**Voice**

- [ ] User speaks → transcript appears → bot thinks → speaks full sentence without mic opening mid-TTS
- [ ] Hindi question → mixed-language reply with English product terms
- [ ] Gujarati question → same code-mixing rules
- [ ] Female vs male voice changes TTS speaker
- [ ] “Clear conversation” resets state
- [ ] End session shows report with transcript

**Knowledge**

- [ ] Ask for something **not** in KB → bot admits uncertainty, points to website
- [ ] Ask for something **in** KB → correct data (no invented fees/dates)

**Chat** *(if enabled)*

- [ ] Text message streams tokens → `text_done` with full reply
- [ ] Same LangGraph answers as voice for same question

### Code quality rules

- Minimize scope per PR; no unrelated refactors.
- Config-driven agents (one graph, many JSON configs) — do not copy-paste 8 separate codebases.
- Match existing naming if extending a repo; otherwise follow FastAPI + Next.js conventions above.
- No secrets in git; use `.env.example` templates.
- Comments only for non-obvious half-duplex / playback timing logic.

### Deliverables

When finished, provide:

1. File tree of what you created/changed
2. How to run backend + frontend locally
3. List of env vars I must set
4. 5 example questions I can try in EN / HI / GU
5. Known limitations (STT latency, demo data, etc.)

---

## PROMPT END

---

## Optional: shorter “one-shot” prompt

If you only need a compact version, paste this:

```text
Build a production Voice AI (+ optional Chat) assistant for [COMPANY] using Next.js, FastAPI, WebSocket, Sarvam STT/TTS, Groq LLM, and LangGraph (router → clarify → specialist). Use my knowledge base at [PATH/URL] — never hallucinate. Support English, Hindi, Gujarati (auto-detect). Replies in HI/GU must use natural Hinglish/Guenglish with brand and technical terms in English script for TTS. Half-duplex: mute mic during thinking and speaking; resume after full TTS playback (debounce inter-chunk gaps). Include language + voice gender selectors, transcript UI, session report on end. Phase 1: graph + KB; Phase 2: voice pipeline; Phase 3: polish + Docker.
```

---

## Optional: chat-only add-on block

Append this **only** if you want chat UI back:

```text
Also add a ChatPanel component: text input, streaming llm_token display, sample question chips, uses same WebSocket with `text_message` / `text_done`. Place on demo page beside VoiceBot with a Voice/Chat toggle. If I did not ask for chat, do not build ChatPanel.
```

---

## Mapping to this repository

This repo already implements most of the above. Use it as a **reference implementation**:

| Feature | Location |
|---------|----------|
| Use-case registry + KB | `backend/use_cases/` |
| LangGraph nodes | `backend/agents/nodes.py`, `graph.py` |
| Voice WebSocket | `backend/routers/voice.py` |
| Voice UI | `frontend/components/VoiceBot.tsx` |
| Demo gallery | `frontend/app/page.tsx`, `app/demo/[id]/` |
| Mixed-language prompts | `backend/config.py` → `voice_speech_style_instruction()` |
| Half-duplex + playback | `frontend/hooks/useAudioPlayback.ts`, `VoiceBot.tsx` |

To adapt for **your** website only:

1. Add `backend/use_cases/[your_id].py` + JSON knowledge.
2. Register in `backend/use_cases/registry.py`.
3. Update branding in `frontend/app/layout.tsx` and demo copy.
4. Set `DEFAULT_USE_CASE_ID` to your id.

---

## License / usage

This prompt template is for your internal use with AI coding tools. Customize freely for client projects.
