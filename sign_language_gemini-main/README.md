# ✋ IndicSign: Gemini version

Real-time Indian Sign Language (ISL) alphabet recognition powered by **Google Gemini vision**.

<p align="center">
  <img src="../docs/screenshots/hero-light.png" alt="IndicSign home page" width="100%">
  <img src="../docs/screenshots/translate-light.png" alt="Translate section" width="100%">
</p>

🌐 **Live demo:** https://ridhi-sign-language-gemini.onrender.com &nbsp;·&nbsp; 🎥 **Video:** https://www.youtube.com/watch?v=d3Ol355ZQiQ

## ▶️ Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
python app.py                   # open http://127.0.0.1:5000
```

Put your key from https://aistudio.google.com/apikey into `.env`:

```env
GEMINI_API_KEY=your-key-here
# GEMINI_MODEL=gemini-3.5-flash   # optional override
```

## ☁️ Deploy (e.g. Render)

- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`
- Env var: `GEMINI_API_KEY`

## 🔌 API

| Route | Method | Description |
|---|---|---|
| `/` | GET | Web app |
| `/process_frame` | POST | `{ "image": "data:image/jpeg;base64,..." }` → `{ "letter", "confidence", "hand", "prediction" }` |
| `/health` | GET | Shows whether the API key is set and which model is in use |

## 🩺 Troubleshooting

| Message | Fix |
|---|---|
| *GEMINI_API_KEY is not set* | Create `.env` next to `app.py` (see above) and restart |
| *Your Gemini API key was rejected* | Generate a new key in Google AI Studio |
| *Gemini is busy / rate limit reached* | Temporary. The app backs off and retries automatically |

### Why the old "Gemini API error" happened
The app called `gemini-1.5-flash`, which Google has shut down. It now uses `gemini-3.5-flash-lite` by default
and automatically falls back to other current models if one is busy or unavailable. The requirements also listed
the wrong package (`dotenv` instead of `python-dotenv`), so the `.env` key was never loaded.
