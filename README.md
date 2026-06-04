# Voice Bot — Ultra-Low Latency (<300ms)

End-to-end **streaming** voice assistant. Every stage of the pipeline streams:
audio in, transcript out, LLM tokens out, speech audio out — so the user hears
a response in well under 300ms after they finish speaking.

```
[Mic] -> Silero VAD (browser) -> WebSocket -> Sarvam STT (Saaras v3)
      -> Groq llama-3.3-70b-versatile (streaming) -> Sarvam Bulbul TTS
    -> WebSocket -> AudioContext (gapless playback) -> [Speakers]
```

## Stack

- **Frontend**: Next.js 14 (App Router, TS), Tailwind, Zustand, `@ricky0123/vad-web`
- **Backend**: FastAPI, async WebSockets, Groq SDK, httpx (Sarvam STT + TTS)

## Quick start (local dev)

You need API keys for:

- Groq → https://console.groq.com
- Sarvam → https://dashboard.sarvam.ai

### Backend

```bash
cd backend
cp .env.example .env   # then edit .env with your keys
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend listens on `http://localhost:8000`. WebSocket endpoint is
`ws://localhost:8000/ws/voice`.

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000.

## Production deploy

Docker Compose with Nginx, Certbot SSL, and auto `.env` setup:

- **Frontend:** `https://voice.aavishailab.com`
- **Backend:** `https://api.voice.aavishailab.com` (container port **6120**)

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). Quick start on the VPS:

```bash
./deploy/setup-env.sh   # edit .env with API keys
./deploy/bootstrap.sh
```

## How it works

1. Browser captures mic at native sample rate via an `AudioWorklet`, resamples
   to 16kHz PCM and sends binary frames over a single persistent WebSocket.
2. Silero VAD (WASM, in-browser) detects speech start/end. On end the client
   sends `{"type":"speech_end"}` so the server transcribes the utterance.
3. Sarvam Saaras v3 returns the transcript and detected language (English,
   Hindi, or Gujarati in auto mode); the server forwards each to the client
   and pushes it into the LLM pipeline.
4. Groq streams tokens; the server buffers them until a sentence boundary
   (`. ! ?`), then immediately sends that sentence to Sarvam Bulbul TTS.
5. Sarvam returns `linear16` audio chunks back to the client as binary
   WebSocket frames.
6. The client schedules each chunk on the AudioContext timeline for **gapless
   playback**, and displays the round-trip latency badge.

## Latency

The UI shows the time between `speech_end` and the **first byte of TTS audio**
returning. Typical local-dev numbers (good network):

- Sarvam STT (batch): ~300–500ms
- Groq TTFT: ~30–80ms
- Sarvam Bulbul first chunk: ~150–300ms
- **Total: ~400–700ms**

## Project layout

```
voicebot/
├── backend/
│   ├── main.py
│   ├── routers/voice.py
│   ├── services/{stt_sarvam,llm,tts_sarvam,tts_router}.py
│   ├── models/schemas.py
│   ├── config.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/{layout,page}.tsx, globals.css
│   ├── components/{VoiceBot,AudioVisualizer,TranscriptPanel,StatusIndicator}.tsx
│   ├── hooks/{useVAD,useAudioCapture,useAudioPlayback,useWebSocket}.ts
│   ├── lib/{audioUtils,utils}.ts
│   ├── store/voiceBotStore.ts
│   ├── types/index.ts
│   ├── package.json
│   └── .env.local.example
```

## Protocol

WebSocket `/ws/voice` accepts:

- Binary frames → raw 16-bit PCM @ 16kHz mono → buffered for Sarvam STT.
- JSON control:
  - `{"type":"speech_end"}` → flush STT
  - `{"type":"clear_history"}` → reset conversation
  - `{"type":"interrupt"}` → drop pending response (barge-in)
  - `{"type":"ping"}`

Server sends:

- Binary frames → 16-bit PCM @ 24kHz mono → AudioContext playback queue.
- JSON: `transcript`, `llm_token`, `tts_start`, `tts_end`, `status`, `error`,
  `ready`, `pong`, `history_cleared`.

## Notes / tips

- Open the page in **Chrome / Edge** for best `AudioWorklet` + WebSocket
  performance.
- If you see a microphone-permission modal, allow it.
- All Groq errors fall back to a polite spoken apology so the user hears
  *something* rather than silence.
- Auto mode uses Sarvam `language_code=unknown` to detect English, Hindi, and
  Gujarati automatically.
