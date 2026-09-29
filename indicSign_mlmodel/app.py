"""IndicSign (on-device ML edition) - MediaPipe hand landmarks + Random Forest classifier."""

import base64
import os
import pickle
import threading

import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

with open(os.path.join(BASE_DIR, "model.p"), "rb") as f:
    model_dict = pickle.load(f)
model = model_dict["model"]
max_length = model_dict["max_length"]

labels_dict = {i: chr(65 + i) for i in range(26)}  # A-Z

mp_hands = mp.solutions.hands
# static_image_mode: frames arrive independently over HTTP, so don't rely on tracking state.
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.3)
hands_lock = threading.Lock()  # MediaPipe graphs are not thread-safe


def extract_features(frame):
    """Return the padded landmark feature vector, or None if no hand is visible."""
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    with hands_lock:
        results = hands.process(frame_rgb)

    if not results.multi_hand_landmarks:
        return None

    data_aux, x_, y_ = [], [], []
    for hand_landmarks in results.multi_hand_landmarks:
        for landmark in hand_landmarks.landmark:
            x_.append(landmark.x)
            y_.append(landmark.y)
        for landmark in hand_landmarks.landmark:
            data_aux.append(landmark.x - min(x_))
            data_aux.append(landmark.y - min(y_))

    data_aux = data_aux[:max_length]
    return np.pad(data_aux, (0, max_length - len(data_aux)), mode="constant")


def predict(frame):
    features = extract_features(frame)
    if features is None:
        return {"hand": False, "letter": "", "confidence": None}

    probabilities = model.predict_proba([features])[0]
    best = int(np.argmax(probabilities))
    letter = labels_dict[int(model.classes_[best])]
    return {"hand": True, "letter": letter, "confidence": round(float(probabilities[best]), 3)}


@app.route("/")
def index():
    return render_template("index.html", engine="On-device ML", engine_note="MediaPipe landmarks + Random Forest",
                           interval=700, stable=3)


@app.route("/health")
def health():
    return jsonify({"ok": True, "model": "random-forest", "features": max_length})


@app.route("/process_frame", methods=["POST"])
def process_frame():
    data = request.get_json(silent=True) or {}
    image_data = data.get("image", "")
    if not image_data or "," not in image_data:
        return jsonify({"error": "Empty image data received"}), 400

    try:
        img_bytes = base64.b64decode(image_data.split(",", 1)[1])
        img = cv2.imdecode(np.frombuffer(img_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception:
        img = None
    if img is None:
        return jsonify({"error": "Failed to decode image"}), 400

    try:
        result = predict(img)
    except Exception as exc:
        app.logger.exception("Prediction failed")
        return jsonify({"error": f"Prediction failed: {exc}"}), 500

    return jsonify({**result, "prediction": result["letter"] or "No hand detected"})


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=int(os.getenv("PORT", 5001)))
