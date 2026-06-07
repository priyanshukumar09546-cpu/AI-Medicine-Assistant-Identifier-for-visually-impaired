import streamlit as st
from PIL import Image
import google.generativeai as genai
from gtts import gTTS

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="MediScan AI",
    page_icon="💊",
    layout="centered"
)

# ─────────────────────────────────────────────
#  LOAD EXTERNAL CSS  ← separate design file
# ─────────────────────────────────────────────
def load_css(file_name):
    with open(file_name, "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css("styles.css")   # ← loads your styles.css

# ─────────────────────────────────────────────
#  GEMINI CONFIG  ← paste your key here
# ─────────────────────────────────────────────
GEMINI_API_KEY =  # ← REPLACE THIS
genai.configure(api_key=GEMINI_API_KEY)

# ─────────────────────────────────────────────
#  IDENTIFY FUNCTION
# ─────────────────────────────────────────────
def identify_medicine(img: Image.Image) -> dict:
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = """You are a medicine identification assistant for visually impaired users.
Analyze this medicine image and respond ONLY in this exact format (no extra text, no markdown):

MEDICINE_NAME: <full name with strength e.g. Paracetamol 500mg>
USED_FOR: <one clear sentence about what it treats>
DOSAGE: <dosage info from box, or 'Not visible on packaging'>
WARNING: <one important warning, or 'None visible'>
CONFIDENCE: <High or Medium or Low>

If no medicine is visible, use Unknown for MEDICINE_NAME."""

    response = model.generate_content([img, prompt])
    text = response.text.strip()

    result = {
        "medicine_name": "Unknown",
        "used_for": "Could not identify",
        "dosage": "Not visible",
        "warning": "Please consult a pharmacist",
        "confidence": "Low"
    }

    for line in text.split('\n'):
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip().upper()
            value = value.strip()
            if key == "MEDICINE_NAME": result["medicine_name"] = value
            elif key == "USED_FOR":    result["used_for"]      = value
            elif key == "DOSAGE":      result["dosage"]        = value
            elif key == "WARNING":     result["warning"]       = value
            elif key == "CONFIDENCE":  result["confidence"]    = value

    return result

# ─────────────────────────────────────────────
#  ANIMATED BACKGROUND + HERO
# ─────────────────────────────────────────────
st.markdown('<div class="mesh-bg"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">Gemini Vision · Free · Instant</div>
  <h1 class="hero-title">
    <span class="gradient-word">MediScan</span> <em>AI</em>
  </h1>
  <p class="hero-sub">
    Upload any medicine image for instant identification —
    designed for visually impaired users with voice output.
  </p>
  <div class="stats-bar">
    <div class="stat-item">
      <div class="stat-num">Any</div>
      <div class="stat-label">Medicine</div>
    </div>
    <div class="stat-sep"></div>
    <div class="stat-item">
      <div class="stat-num">&lt;3s</div>
      <div class="stat-label">Response</div>
    </div>
    <div class="stat-sep"></div>
    <div class="stat-item">
      <div class="stat-num">🔊</div>
      <div class="stat-label">Voice Out</div>
    </div>
    <div class="stat-sep"></div>
    <div class="stat-item">
      <div class="stat-num">Free</div>
      <div class="stat-label">API Tier</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-div"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  FILE UPLOADER
# ─────────────────────────────────────────────
st.markdown('<div class="upload-label">📂 Upload Medicine Image</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop your medicine image here",
    type=['png', 'jpg', 'jpeg'],
    label_visibility="collapsed"
)

# ─────────────────────────────────────────────
#  MAIN LOGIC
# ─────────────────────────────────────────────
if uploaded_file:
    img = Image.open(uploaded_file).convert('RGB')

    st.markdown('<div class="section-div"></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 5, 1])
    with col2:
        st.image(img, caption="", use_container_width=True)

    st.markdown('<div class="section-div"></div>', unsafe_allow_html=True)

    with st.spinner("🔬 Scanning medicine with Gemini Vision..."):
        try:
            result = identify_medicine(img)

            conf       = result["confidence"]
            conf_cls   = {"High": "high",      "Medium": "medium"}.get(conf, "low")
            conf_color = {"High": "conf-high",  "Medium": "conf-medium"}.get(conf, "conf-low")

            voice_text = (
                f"Medicine identified: {result['medicine_name']}. "
                f"Used for: {result['used_for']}. "
                f"Dosage: {result['dosage']}. "
                f"Warning: {result['warning']}."
            )

            tts = gTTS(text=voice_text, lang='en', slow=False)
            tts.save("prediction.mp3")
            audio_bytes = open("prediction.mp3", "rb").read()

            st.markdown(f"""
            <div class="result-section">
              <div class="result-top-bar">
                <span class="identified-chip">Medicine Identified</span>
              </div>
              <div class="medicine-hero-name">{result['medicine_name']}</div>
              <div class="medicine-sub-line">AI analysis complete · {conf} confidence</div>
              <div class="cards-grid">
                <div class="card wide">
                  <div class="card-icon-wrap icon-blue">🩺</div>
                  <div class="card-label">Used For</div>
                  <div class="card-text">{result['used_for']}</div>
                </div>
                <div class="card">
                  <div class="card-icon-wrap icon-purple">💉</div>
                  <div class="card-label">Dosage</div>
                  <div class="card-text">{result['dosage']}</div>
                </div>
                <div class="card">
                  <div class="card-icon-wrap icon-green">📊</div>
                  <div class="card-label">AI Confidence</div>
                  <div class="card-text">
                    <span class="conf-dot {conf_cls}"></span>
                    <span class="{conf_color}">{conf}</span>
                  </div>
                </div>
                <div class="card warn-card wide">
                  <div class="card-icon-wrap icon-yellow">⚠️</div>
                  <div class="card-label">Warning</div>
                  <div class="card-text">{result['warning']}</div>
                </div>
              </div>
              <div class="voice-card">
                <div class="voice-label">Voice Output</div>
            """, unsafe_allow_html=True)

            st.audio(audio_bytes, format="audio/mp3")

            st.markdown("""
              </div>
              <div class="disclaimer">
                <strong>⚕ Medical Disclaimer:</strong>
                This tool is for assistance only. Always consult a licensed physician or pharmacist before taking any medication.
              </div>
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            err = str(e)
            if "quota" in err.lower():
                st.error("❌ Quota exceeded. Please wait a minute and try again.")
            elif "api" in err.lower() or "key" in err.lower():
                st.error("❌ Invalid API key. Replace 'paste-your-api-key-here' with your real key.")
            elif "404" in err or "not found" in err.lower():
                st.error("❌ Model not available. Try changing the model name.")
            else:
                st.error(f"❌ Error: {err}")

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div class="footer">
  MediScan AI
  <span class="dot">·</span>
  Built for visually impaired users
  <span class="dot">·</span>
  Powered by Google Gemini Vision
  <br>
  Always consult a licensed doctor for medical advice
</div>
""", unsafe_allow_html=True)