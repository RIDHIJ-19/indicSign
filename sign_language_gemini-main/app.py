"""IndicSign (Gemini edition) - translate Indian Sign Language alphabet signs with Gemini."""

import json
import logging
import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("indicsign")

app = Flask(__name__, static_url_path="/static", static_folder="static")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# gemini-1.5-flash (used by the original version) has been shut down by Google,
# which is what caused the "Gemini API error". We now try a preferred model and
# fall back through newer ones if a model is unavailable for this key.
PREFERRED_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-latest", "gemini-3.1-flash-lite"]
REQUEST_TIMEOUT = 20  # seconds per model before trying the next one
MODEL_CHAIN = [PREFERRED_MODEL] + [m for m in FALLBACK_MODELS if m != PREFERRED_MODEL]

PROMPT = (
    "You are an expert in Indian Sign Language (ISL) fingerspelling. "
    "Look at the hand sign in this webcam image and identify which English alphabet letter (A-Z) it represents. "
    "If no hand is clearly visible, set hand_visible to false and letter to an empty string. "
    "confidence is a number from 0 to 1 describing how sure you are."
)

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "hand_visible": {"type": "BOOLEAN"},
        "letter": {"type": "STRING"},
        "confidence": {"type": "NUMBER"},
    },
    "required": ["hand_visible", "letter", "confidence"],
}

session = requests.Session()
_working_model = None  # remembered after the first successful call


class GeminiError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def _payload(base64_image, mime_type):
    return {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": PROMPT},
                {"inline_data": {"mime_type": mime_type, "data": base64_image}},
            ],
        }],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }


def _parse(result):
    try:
        candidate = result["candidates"][0]
        parts = candidate["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
    except (KeyError, IndexError, TypeError):
        reason = (result.get("promptFeedback") or {}).get("blockReason")
        raise GeminiError(f"Gemini returned no answer{f' ({reason})' if reason else ''}.")

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Model ignored the schema; salvage a single letter if possible.
        letters = [c for c in text.upper() if c.isalpha()]
        return {"hand": bool(letters), "letter": letters[0] if letters else "", "confidence": None}

    letter = str(data.get("letter", "")).strip().upper()[:1]
    if not letter.isalpha():
        letter = ""
    confidence = data.get("confidence")
    if isinstance(confidence, (int, float)):
        confidence = max(0.0, min(1.0, float(confidence)))
    else:
        confidence = None
    return {"hand": bool(data.get("hand_visible")) and bool(letter), "letter": letter, "confidence": confidence}


def call_gemini_vision(base64_image, mime_type="image/jpeg"):
    global _working_model

    if not GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY is not set. Add it to a .env file next to app.py.", 500)

    # Start with the model that worked last time, then fall back through the rest.
    models = [_working_model] + [m for m in MODEL_CHAIN if m != _working_model] if _working_model else MODEL_CHAIN
    last_error = None

    for model in models:
        try:
            response = session.post(
                f"{API_BASE}/{model}:generateContent",
                headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY},
                json=_payload(base64_image, mime_type),
                timeout=REQUEST_TIMEOUT,
            )
        except requests.Timeout:
            log.warning("Gemini %s timed out", model)
            last_error = GeminiError("Gemini is responding slowly. Retrying shortly.", 503)
            continue
        except requests.RequestException as exc:
            raise GeminiError(f"Could not reach Gemini: {exc.__class__.__name__}", 503)

        if response.ok:
            if _working_model != model:
                log.info("Using Gemini model: %s", model)
                _working_model = model
            return _parse(response.json())

        try:
            message = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            message = response.text
        log.warning("Gemini %s -> HTTP %s: %s", model, response.status_code, message[:300])

        if response.status_code == 404:
            last_error = GeminiError(f"Model '{model}' is unavailable.", 502)
            continue  # try the next model
        if response.status_code in (400, 403) and "API key" in message:
            raise GeminiError("Your Gemini API key was rejected. Check GEMINI_API_KEY.", 401)
        if response.status_code == 429:
            last_error = GeminiError("Gemini rate limit reached - taking a short breather.", 429)
            continue  # quotas are per model, so another one may still have room
        if response.status_code >= 500:
            last_error = GeminiError("Gemini is busy right now. Retrying shortly.", 503)
            continue  # "high demand" overloads are per model
        raise GeminiError(f"Gemini error: {message[:200]}", 502)

    _working_model = None
    raise last_error or GeminiError("No Gemini model available.")


@app.route("/")
def index():
    return render_template("index.html", engine="Gemini", engine_note="Powered by Google Gemini vision",
                           interval=2000, stable=2)


@app.route("/health")
def health():
    return jsonify({"ok": True, "api_key_set": bool(GEMINI_API_KEY), "model": _working_model or PREFERRED_MODEL})


@app.route("/process_frame", methods=["POST"])
def process_frame():
    data = request.get_json(silent=True) or {}
    image_data = data.get("image", "")

    if not image_data or "," not in image_data:
        return jsonify({"error": "Empty image data received"}), 400

    header, base64_image = image_data.split(",", 1)
    mime_type = header.split(":", 1)[-1].split(";", 1)[0] or "image/jpeg"

    try:
        result = call_gemini_vision(base64_image, mime_type)
    except GeminiError as exc:
        return jsonify({"error": str(exc)}), exc.status
    except Exception:
        log.exception("Unexpected server error")
        return jsonify({"error": "Server error"}), 500

    # `prediction` kept for backwards compatibility with the old frontend.
    return jsonify({**result, "prediction": result["letter"] or "No hand detected"})


if __name__ == "__main__":
    if not GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY is not set - predictions will fail until you add it to .env")
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=int(os.getenv("PORT", 5000)))
