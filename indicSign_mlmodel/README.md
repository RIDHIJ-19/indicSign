# 🧠 IndicSign: on-device ML version

ISL alphabet recognition that runs fully locally: **MediaPipe** extracts 21 hand landmarks and a **Random Forest** classifies the letter (~89% accuracy on the custom dataset). No API key needed.

## ▶️ Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt   # Python 3.10 – 3.12
python app.py                     # http://127.0.0.1:5001
```

## 🏋️ Train your own model

1. `python collect_imgs.py`: capture images for each letter (A–Z) into `data/`
2. `python create_dataset.py`: extract landmarks → `data.pickle`
3. `python trainclassifier.py`: train → `model.p`
4. `python test_classifier.py`: live test window (press **Q** to quit)

> `scikit-learn` is pinned to 1.6.1 because `model.p` was trained with it. If you retrain, you can upgrade it.
