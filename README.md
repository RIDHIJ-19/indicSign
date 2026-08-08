# Indian Sign Language Recognition


A dual-version project aimed at recognizing Indian Sign Language (ISL) hand gestures in real time. This system is built to promote accessibility and foster inclusive communication by translating ISL gestures into text.

## 🔀 Project Versions

### 🧠 Version 1: Machine Learning Model

Live Demo: https://drive.google.com/file/d/1ip8d4NJDdsUz1BJOQ8EAsz6bWUCMXd_w/view

A self-trained model using classical machine learning techniques for ISL alphabet recognition.

#### 📌 Highlights
- Custom dataset built with OpenCV (50 images per alphabet)
- MediaPipe used for hand landmark detection
- Random Forest Classifier used for gesture classification
- Real-time alphabet detection via webcam
- Achieves ~89% accuracy

#### 🛠️ Tools & Libraries
- Python
- OpenCV
- MediaPipe
- Scikit-learn

#### 📁 Structure
- Captured images stored in labeled folders (A-Z)
- Preprocessed landmarks used as input features for the model

---

### 🤖 Version 2: Gemini API Integration

LIVE DEMO: https://ridhi-sign-language-gemini.onrender.com



YOUTUBE: https://www.youtube.com/watch?v=d3Ol355ZQiQ



A cloud-powered solution leveraging the Gemini multimodal API to interpret ISL gestures.

#### 📌 Highlights
- Uses Gemini Vision API for image-to-text translation
- Scalable to more complex gestures and sentence-level interpretation
- Cloud-based processing eliminates local training requirements
- User-friendly interface using Gradio

#### 🛠️ Tools & Libraries
- Python
- OpenCV
- Google Gemini API
- Gradio (optional for web interface)

#### 🔐 API Usage
- Requires a valid Gemini API key
- Images or frames from webcam are sent to the API for gesture interpretation

---

## 🎯 Applications
- Real-time communication aids for the hearing/speech impaired
- Educational tools for learning ISL
- Interactive systems in public and customer service areas

---
 

