import streamlit as st
from PIL import Image
import google.generativeai as genai
from gtts import gTTS
import datetime
import os
import json
import io
import base64

# ── try optional deps ──
try:
    from fpdf import FPDF
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="MediScan AI", page_icon="💊", layout="centered")

# ─────────────────────────────────────────────
#  GEMINI CONFIG
# ─────────────────────────────────────────────
GEMINI_API_KEY = ""  # ← PASTE YOUR KEY HERE
genai.configure(api_key=GEMINI_API_KEY)

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    "history": [], "chat_messages": [], "current_med": None,
    "active_tab": "scan", "selected_lang": "English",
    "favourites": [], "camera_mode": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=DM+Mono:wght@400;500&display=swap');
:root{--bg:#03070f;--bg2:#070d1a;--bg3:#0b1425;--border:#0f2040;--border2:#162d52;
  --accent:#0ea5e9;--accent2:#6366f1;--accent3:#34d399;--warn:#f59e0b;--danger:#ef4444;
  --text:#e2eaf6;--muted:#3d5478;--muted2:#1e3358;--card:#070f20;}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body,[class*="css"],.stApp{font-family:'DM Sans',sans-serif!important;background:var(--bg)!important;color:var(--text)!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:0 1.5rem 5rem!important;max-width:860px!important;}
.mesh-bg{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;}
.mesh-bg::before{content:'';position:absolute;width:700px;height:700px;border-radius:50%;
  background:radial-gradient(circle,rgba(14,165,233,0.08) 0%,transparent 70%);
  top:-200px;left:-200px;animation:orb1 14s ease-in-out infinite alternate;filter:blur(40px);}
.mesh-bg::after{content:'';position:absolute;width:600px;height:600px;border-radius:50%;
  background:radial-gradient(circle,rgba(99,102,241,0.07) 0%,transparent 70%);
  bottom:-150px;right:-150px;animation:orb2 18s ease-in-out infinite alternate;filter:blur(50px);}
@keyframes orb1{from{transform:translate(0,0);}to{transform:translate(60px,40px) scale(1.1);}}
@keyframes orb2{from{transform:translate(0,0);}to{transform:translate(-50px,-30px) scale(1.15);}}
.hero{text-align:center;padding:2.5rem 1rem 1.2rem;position:relative;z-index:1;}
.hero-eyebrow{display:inline-flex;align-items:center;gap:0.5rem;background:rgba(14,165,233,0.08);
  border:1px solid rgba(14,165,233,0.2);border-radius:999px;padding:0.35rem 1rem;
  font-size:0.65rem;font-weight:600;letter-spacing:0.16em;text-transform:uppercase;
  color:var(--accent);font-family:'DM Mono',monospace!important;margin-bottom:1rem;}
.hero-eyebrow::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--accent3);animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.2;}}
.hero-title{font-family:'DM Serif Display',serif!important;font-size:3rem!important;
  font-weight:400!important;line-height:1.05!important;margin-bottom:0.6rem!important;}
.grad{background:linear-gradient(135deg,#7dd3fc,#38bdf8,#818cf8,#a78bfa);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.hero-title em{font-style:italic;color:var(--accent3);-webkit-text-fill-color:var(--accent3);}
.hero-sub{color:var(--muted)!important;font-size:0.92rem!important;font-weight:300!important;
  line-height:1.75!important;max-width:460px;margin:0 auto 1.2rem!important;}
.sdiv{height:1px;background:linear-gradient(90deg,transparent,var(--border2),transparent);margin:1.2rem 0;}
[data-testid="stFileUploader"]{background:linear-gradient(145deg,var(--bg2),var(--bg3))!important;
  border:1.5px dashed var(--border2)!important;border-radius:20px!important;padding:1.5rem!important;transition:all 0.3s!important;}
[data-testid="stFileUploader"]:hover{border-color:var(--accent)!important;box-shadow:0 0 0 3px rgba(14,165,233,0.06)!important;}
[data-testid="stFileUploaderDropzoneInstructions"] span{color:var(--muted)!important;font-size:0.85rem!important;}
[data-testid="stFileUploader"] button{background:linear-gradient(135deg,var(--accent),var(--accent2))!important;
  border:none!important;border-radius:12px!important;color:#fff!important;font-weight:600!important;
  font-size:0.8rem!important;padding:0.5rem 1.2rem!important;}
[data-testid="stImage"] img{border-radius:18px!important;border:1px solid var(--border2)!important;
  box-shadow:0 25px 60px rgba(0,0,0,0.6)!important;}
.card{background:var(--card);border:1px solid var(--border);border-radius:18px;
  padding:1.2rem 1.3rem;transition:all 0.25s;position:relative;overflow:hidden;}
.card:hover{border-color:var(--border2);transform:translateY(-2px);box-shadow:0 10px 30px rgba(0,0,0,0.3);}
.card.wide{grid-column:1/-1;}
.card.warn{background:linear-gradient(145deg,#0f0e03,#18150a);border-color:rgba(245,158,11,0.15);}
.card.danger{background:linear-gradient(145deg,#130505,#1a0808);border-color:rgba(239,68,68,0.15);}
.card.safe{background:linear-gradient(145deg,#031210,#051a14);border-color:rgba(52,211,153,0.15);}
.card.info{background:linear-gradient(145deg,#030f1a,#051528);border-color:rgba(14,165,233,0.15);}
.card-grid{display:grid;grid-template-columns:1fr 1fr;gap:0.7rem;margin-bottom:0.7rem;}
.clabel{font-size:0.58rem;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;
  color:var(--muted);font-family:'DM Mono',monospace!important;margin-bottom:0.35rem;}
.cval{font-size:0.9rem;color:#94afd4;line-height:1.6;}
.warn .clabel{color:#7a5c1a;}.warn .cval{color:#fde68a;}
.danger .clabel{color:#7a1a1a;}.danger .cval{color:#fca5a5;}
.safe .clabel{color:#1a5c40;}.safe .cval{color:#6ee7b7;}
.info .clabel{color:#0c3a5c;}.info .cval{color:#7dd3fc;}
.cicon{width:32px;height:32px;border-radius:9px;display:flex;align-items:center;
  justify-content:center;font-size:0.9rem;margin-bottom:0.7rem;}
.ib{background:rgba(14,165,233,0.1);}.ip{background:rgba(99,102,241,0.1);}
.ig{background:rgba(52,211,153,0.1);}.iy{background:rgba(245,158,11,0.1);}
.ir{background:rgba(239,68,68,0.1);}
.med-name{font-family:'DM Serif Display',serif;font-size:2.2rem;font-weight:400;
  letter-spacing:-0.02em;line-height:1.1;margin-bottom:0.3rem;
  background:linear-gradient(135deg,#f0f9ff,#7dd3fc,#818cf8);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.med-sub{font-size:0.75rem;color:var(--muted);font-family:'DM Mono',monospace;margin-bottom:1.2rem;}
.chip{display:inline-flex;align-items:center;gap:0.35rem;border-radius:999px;
  padding:0.28rem 0.8rem;font-size:0.62rem;font-weight:700;letter-spacing:0.12em;
  text-transform:uppercase;font-family:'DM Mono',monospace!important;}
.chip-green{background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.25);color:var(--accent3);}
.chip-blue{background:rgba(14,165,233,0.1);border:1px solid rgba(14,165,233,0.2);color:var(--accent);}
.chip-red{background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:#f87171;}
.chip-yellow{background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.2);color:var(--warn);}
.chip-purple{background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2);color:#a5b4fc;}
.cdot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px;vertical-align:middle;}
.cdot.h{background:var(--accent3);box-shadow:0 0 5px var(--accent3);}
.cdot.m{background:var(--warn);box-shadow:0 0 5px var(--warn);}
.cdot.l{background:#f87171;box-shadow:0 0 5px #f87171;}
.ch{color:var(--accent3)!important;font-weight:600;}
.cm{color:var(--warn)!important;font-weight:600;}
.cl{color:#f87171!important;font-weight:600;}
.voice-card{background:linear-gradient(145deg,#060f20,#08122a);border:1px solid var(--border);
  border-radius:18px;padding:1.2rem 1.3rem;margin-top:0.7rem;position:relative;overflow:hidden;}
.voice-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--accent),var(--accent2),var(--accent3));}
.vlabel{font-size:0.58rem;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;
  color:var(--accent3);font-family:'DM Mono',monospace!important;margin-bottom:0.6rem;
  display:flex;align-items:center;gap:0.4rem;}
.vlabel::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--accent3);animation:blink 1.5s infinite;}
audio{width:100%!important;border-radius:10px!important;height:40px!important;filter:invert(0.85) hue-rotate(180deg);}
.chat-wrap{max-height:400px;overflow-y:auto;padding:0.5rem 0;margin-bottom:1rem;
  scrollbar-width:thin;scrollbar-color:var(--border2) transparent;}
.msg{display:flex;gap:0.7rem;margin-bottom:1rem;animation:fadeIn 0.3s ease;}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
.msg.user{flex-direction:row-reverse;}
.msg-avatar{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.85rem;flex-shrink:0;}
.ai-av{background:linear-gradient(135deg,var(--accent),var(--accent2));}
.user-av{background:linear-gradient(135deg,var(--accent3),#059669);}
.msg-bubble{max-width:75%;padding:0.85rem 1.1rem;border-radius:18px;font-size:0.88rem;line-height:1.6;}
.ai-bubble{background:var(--bg3);border:1px solid var(--border);color:var(--text);border-radius:4px 18px 18px 18px;}
.user-bubble{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border-radius:18px 4px 18px 18px;}
[data-testid="stTextInput"] input{background:var(--bg2)!important;border:1px solid var(--border2)!important;
  border-radius:14px!important;color:var(--text)!important;font-size:0.9rem!important;padding:0.75rem 1rem!important;}
[data-testid="stTextInput"] input:focus{border-color:var(--accent)!important;box-shadow:0 0 0 3px rgba(14,165,233,0.08)!important;}
.hist-item{background:var(--card);border:1px solid var(--border);border-radius:14px;
  padding:1rem 1.2rem;margin-bottom:0.6rem;transition:all 0.2s;}
.hist-item:hover{border-color:var(--border2);transform:translateX(3px);}
.hist-med{font-size:1rem;font-weight:600;color:var(--text);margin-bottom:0.25rem;}
.hist-meta{font-size:0.7rem;color:var(--muted);font-family:'DM Mono',monospace;}
.fav-item{background:var(--card);border:1px solid rgba(245,158,11,0.2);border-radius:14px;
  padding:1rem 1.2rem;margin-bottom:0.6rem;transition:all 0.2s;}
.fav-item:hover{border-color:rgba(245,158,11,0.4);transform:translateX(3px);}
.result-section{animation:slideUp 0.5s cubic-bezier(.4,0,.2,1) forwards;}
@keyframes slideUp{from{opacity:0;transform:translateY(24px);}to{opacity:1;transform:translateY(0);}}
.disc{margin-top:0.7rem;padding:0.8rem 1.1rem;background:rgba(99,102,241,0.04);
  border:1px solid rgba(99,102,241,0.1);border-radius:12px;font-size:0.72rem;
  color:var(--muted);line-height:1.6;text-align:center;}
.sos-btn{background:linear-gradient(135deg,#dc2626,#991b1b)!important;
  border:none!important;border-radius:14px!important;color:#fff!important;
  font-weight:700!important;font-size:1rem!important;padding:1rem 2rem!important;
  box-shadow:0 4px 20px rgba(239,68,68,0.4)!important;width:100%!important;}
.footer{text-align:center;margin-top:4rem;padding-top:1.5rem;border-top:1px solid var(--border);
  font-size:0.68rem;color:var(--muted2);font-family:'DM Mono',monospace;line-height:2;}
.dot{color:var(--muted);margin:0 0.35rem;}
[data-testid="stAlert"]{border-radius:14px!important;}
.stButton>button{background:linear-gradient(135deg,var(--accent),var(--accent2))!important;
  border:none!important;border-radius:12px!important;color:#fff!important;font-weight:600!important;
  font-size:0.82rem!important;padding:0.55rem 1.2rem!important;
  box-shadow:0 4px 16px rgba(14,165,233,0.25)!important;transition:all 0.2s!important;}
.stButton>button:hover{box-shadow:0 6px 24px rgba(14,165,233,0.4)!important;transform:translateY(-1px)!important;}
[data-testid="stSelectbox"]>div{background:var(--bg2)!important;border:1px solid var(--border2)!important;border-radius:12px!important;}
.scan-anim{text-align:center;padding:2rem;}
.scan-ring{width:70px;height:70px;border-radius:50%;border:3px solid var(--border2);
  border-top-color:var(--accent);animation:spin 1s linear infinite;margin:0 auto 1rem;}
@keyframes spin{to{transform:rotate(360deg);}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  AI HELPERS
# ─────────────────────────────────────────────
def gmodel():
    return genai.GenerativeModel("gemini-2.5-flash")

def identify_medicine(img):
    prompt = """Analyze this medicine image. Respond ONLY in this exact format:
MEDICINE_NAME: <name + strength>
TYPE: <tablet/syrup/injection/capsule/cream>
USED_FOR: <one sentence>
DOSAGE: <dosage or Not visible>
SIDE_EFFECTS: <3 side effects comma separated>
SIDE_MILD: <mild side effect score 0-10>
SIDE_MODERATE: <moderate side effect score 0-10>
SIDE_SEVERE: <severe side effect score 0-10>
WARNING: <one key warning>
DOCTOR_VISIT: <when to see doctor, one sentence>
EXPIRY_DATE: <expiry date if visible or Not visible>
CONFIDENCE: <High or Medium or Low>
If no medicine visible use Unknown."""
    r = gmodel().generate_content([img, prompt])
    out = {"medicine_name":"Unknown","type":"Unknown","used_for":"Could not identify",
           "dosage":"Not visible","side_effects":"Not available",
           "side_mild":"3","side_moderate":"2","side_severe":"1",
           "warning":"Consult pharmacist","doctor_visit":"If symptoms worsen",
           "expiry_date":"Not visible","confidence":"Low"}
    for line in r.text.strip().split('\n'):
        if ':' in line:
            k,_,v = line.partition(':')
            k=k.strip().upper(); v=v.strip()
            m = {"MEDICINE_NAME":"medicine_name","TYPE":"type","USED_FOR":"used_for",
                 "DOSAGE":"dosage","SIDE_EFFECTS":"side_effects","SIDE_MILD":"side_mild",
                 "SIDE_MODERATE":"side_moderate","SIDE_SEVERE":"side_severe",
                 "WARNING":"warning","DOCTOR_VISIT":"doctor_visit",
                 "EXPIRY_DATE":"expiry_date","CONFIDENCE":"confidence"}
            if k in m: out[m[k]] = v
    return out

def search_medicine(name):
    prompt = f"""Give information about {name} medicine. Respond ONLY in this exact format:
MEDICINE_NAME: <name + strength>
TYPE: <tablet/syrup/injection/capsule>
USED_FOR: <one sentence>
DOSAGE: <standard dosage>
SIDE_EFFECTS: <3 side effects comma separated>
WARNING: <one key warning>
DOCTOR_VISIT: <when to see doctor>
ALTERNATIVES: <2 alternatives comma separated>"""
    r = gmodel().generate_content(prompt)
    out = {"medicine_name":name,"type":"Unknown","used_for":"","dosage":"",
           "side_effects":"","warning":"","doctor_visit":"","alternatives":""}
    for line in r.text.strip().split('\n'):
        if ':' in line:
            k,_,v = line.partition(':')
            k=k.strip().upper(); v=v.strip()
            m = {"MEDICINE_NAME":"medicine_name","TYPE":"type","USED_FOR":"used_for",
                 "DOSAGE":"dosage","SIDE_EFFECTS":"side_effects","WARNING":"warning",
                 "DOCTOR_VISIT":"doctor_visit","ALTERNATIVES":"alternatives"}
            if k in m: out[m[k]] = v
    return out

def read_prescription(img):
    prompt = """This is a prescription image. Extract all medicines.
For each medicine found, provide one line:
MEDICINE: <name> | DOSAGE: <dosage> | DURATION: <duration if visible>
List all medicines found. If none found say: NO_MEDICINES_FOUND"""
    r = gmodel().generate_content([img, prompt])
    return r.text.strip()

def translate_text(text, lang):
    if lang == "English" or not text: return text
    prompt = f"""Translate to {lang}. Keep medicine names and numbers in English. Return ONLY translated text:
{text}"""
    r = gmodel().generate_content(prompt)
    return r.text.strip()

def chat_with_ai(question, med_context, lang="English"):
    lang_inst = f"Respond in {lang}." if lang != "English" else "Respond in English."
    prompt = f"""You are a helpful medical assistant. Medicine context: {med_context}.
{lang_inst} Keep medicine names in English. Answer in 2-4 sentences: {question}
End with a short disclaimer."""
    r = gmodel().generate_content(prompt)
    return r.text.strip()

def drug_interaction(med1, med2):
    prompt = f"""Check interaction between {med1} and {med2}. Format:
LEVEL: <Safe or Moderate or Severe>
EFFECT: <one sentence>
ADVICE: <one sentence>"""
    r = gmodel().generate_content(prompt)
    out = {"level":"Unknown","effect":"Could not determine","advice":"Consult your doctor"}
    for line in r.text.strip().split('\n'):
        if ':' in line:
            k,_,v = line.partition(':')
            k=k.strip().upper(); v=v.strip()
            if k=="LEVEL": out["level"]=v
            elif k=="EFFECT": out["effect"]=v
            elif k=="ADVICE": out["advice"]=v
    return out

def get_alternatives(name):
    r = gmodel().generate_content(f"List 3 alternatives for {name}. Format: NAME: description (one line each). No markdown.")
    return r.text.strip()

def check_expiry(s):
    if s in ("Not visible","Unknown",""): return None, None
    for fmt in ("%m/%Y","%m-%Y","%b %Y","%B %Y","%Y-%m-%d","%d/%m/%Y"):
        try:
            exp = datetime.datetime.strptime(s.strip(), fmt)
            days = (exp - datetime.datetime.now()).days
            return exp.strftime("%b %Y"), days
        except: pass
    return s, None

def make_pdf(result):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 12, "MediScan AI - Medicine Report", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Generated: {datetime.datetime.now().strftime('%d %b %Y %I:%M %p')}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, result.get("medicine_name","Unknown"), ln=True)
    pdf.set_font("Arial", "", 11)
    fields = [("Type", "type"),("Used For","used_for"),("Dosage","dosage"),
              ("Side Effects","side_effects"),("Warning","warning"),
              ("When to See Doctor","doctor_visit"),("Expiry Date","expiry_date"),
              ("AI Confidence","confidence")]
    for label, key in fields:
        pdf.set_font("Arial","B",10)
        pdf.cell(45, 8, f"{label}:", border=0)
        pdf.set_font("Arial","",10)
        val = result.get(key,"N/A")
        pdf.multi_cell(0, 8, val[:200] if len(val)>200 else val)
    pdf.ln(5)
    pdf.set_font("Arial","I",9)
    pdf.multi_cell(0,6,"DISCLAIMER: This report is for informational purposes only. Always consult a licensed physician or pharmacist before taking any medication.")
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()

# ─────────────────────────────────────────────
#  MESH BG + HERO
# ─────────────────────────────────────────────
st.markdown('<div class="mesh-bg"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">Gemini Vision · AI Powered · Free</div>
  <h1 class="hero-title"><span class="grad">MediScan</span> <em>AI</em></h1>
  <p class="hero-sub">Complete AI healthcare assistant — scan, search, chat, check interactions & more.</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  NAV TABS
# ─────────────────────────────────────────────
tab_defs = [("scan","💊 Scan"),("search","🔍 Search"),("chat","💬 Chat"),
            ("checker","⚗️ Interact"),("rx","📄 Rx Reader"),
            ("favourites","⭐ Saved"),("history","📋 History")]
cols = st.columns(len(tab_defs))
for i,(key,label) in enumerate(tab_defs):
    with cols[i]:
        if st.button(label, key=f"nav_{key}"):
            st.session_state.active_tab = key
            st.rerun()

st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  TAB — SCAN
# ══════════════════════════════════════════════
if st.session_state.active_tab == "scan":

    lang_map = {"English":"en","Hindi":"hi","Bengali":"bn","Tamil":"ta","Telugu":"te","Marathi":"mr"}
    c1,c2 = st.columns([3,1])
    with c1:
        lang = st.selectbox("🌐 Language",list(lang_map.keys()),label_visibility="collapsed")
        st.session_state.selected_lang = lang
    with c2:
        cam_toggle = st.button("📸 Camera" if not st.session_state.camera_mode else "📁 Upload")
        if cam_toggle:
            st.session_state.camera_mode = not st.session_state.camera_mode
            st.rerun()

    img = None
    if st.session_state.camera_mode:
        st.markdown('<p style="font-size:0.7rem;color:#3d5478;font-family:DM Mono,monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.4rem;">📸 Take a Photo</p>', unsafe_allow_html=True)
        cam_img = st.camera_input("Take photo", label_visibility="collapsed")
        if cam_img:
            img = Image.open(cam_img).convert('RGB')
    else:
        st.markdown('<p style="font-size:0.7rem;color:#3d5478;font-family:DM Mono,monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.4rem;">📂 Upload Medicine Image</p>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload", type=['png','jpg','jpeg'], label_visibility="collapsed")
        if uploaded:
            img = Image.open(uploaded).convert('RGB')

    if img:
        c1,c2,c3 = st.columns([1,5,1])
        with c2: st.image(img, use_container_width=True)
        st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)

        with st.spinner("🔬 Scanning with Gemini Vision..."):
            try:
                result = identify_medicine(img)
                st.session_state.current_med = result
                st.session_state.history.append({
                    "name":result["medicine_name"],"date":datetime.datetime.now().strftime("%d %b %Y, %I:%M %p"),
                    "confidence":result["confidence"],"expiry":result["expiry_date"]
                })

                # translate if needed
                if lang != "English":
                    with st.spinner(f"🌐 Translating to {lang}..."):
                        for field in ["used_for","dosage","side_effects","warning","doctor_visit"]:
                            result[field] = translate_text(result[field], lang)

                conf = result["confidence"]
                cc = {"High":"h","Medium":"m"}.get(conf,"l")
                cf = {"High":"ch","Medium":"cm"}.get(conf,"cl")

                exp_label, exp_days = check_expiry(result["expiry_date"])
                if exp_days is not None:
                    if exp_days < 0:
                        exp_html = f'<span style="color:#f87171;font-weight:700;">⛔ EXPIRED {abs(exp_days)} days ago</span>'
                    elif exp_days < 90:
                        exp_html = f'<span style="color:#f59e0b;font-weight:700;">⚠️ Expires in {exp_days} days</span>'
                    else:
                        exp_html = f'<span style="color:#34d399;font-weight:700;">✅ Safe — {exp_days} days left</span>'
                else:
                    exp_html = f'<span style="color:#3d5478;">{result["expiry_date"]}</span>'

                st.markdown(f"""
                <div class="result-section">
                  <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.6rem;">
                    <span class="chip chip-green">✓ Identified</span>
                    <span class="chip chip-blue">{result['type']}</span>
                  </div>
                  <div class="med-name">{result['medicine_name']}</div>
                  <div class="med-sub">AI analysis complete &nbsp;·&nbsp; <span class="cdot {cc}"></span><span class="{cf}">{conf} confidence</span></div>
                  <div class="card-grid">
                    <div class="card wide"><div class="cicon ib">🩺</div><div class="clabel">Used For</div><div class="cval">{result['used_for']}</div></div>
                    <div class="card"><div class="cicon ip">💉</div><div class="clabel">Dosage</div><div class="cval">{result['dosage']}</div></div>
                    <div class="card"><div class="cicon ig">⚗️</div><div class="clabel">Side Effects</div><div class="cval">{result['side_effects']}</div></div>
                    <div class="card warn wide"><div class="cicon iy">⚠️</div><div class="clabel">Warning</div><div class="cval">{result['warning']}</div></div>
                    <div class="card info wide"><div class="cicon ib">🏥</div><div class="clabel">When to See Doctor</div><div class="cval">{result['doctor_visit']}</div></div>
                    <div class="card wide"><div class="cicon ig">📅</div><div class="clabel">Expiry Date</div><div class="cval">{exp_html}</div></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # SIDE EFFECTS CHART
                if HAS_PLOTLY:
                    try:
                        mild = int(result.get("side_mild","3"))
                        mod  = int(result.get("side_moderate","2"))
                        sev  = int(result.get("side_severe","1"))
                    except: mild,mod,sev = 3,2,1
                    fig = go.Figure(go.Bar(
                        x=["Mild","Moderate","Severe"], y=[mild,mod,sev],
                        marker_color=["#34d399","#f59e0b","#ef4444"],
                        text=[mild,mod,sev], textposition="outside"
                    ))
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(7,15,32,0.8)",
                        font=dict(color="#94afd4",family="DM Sans"),
                        height=220, margin=dict(t=30,b=20,l=20,r=20),
                        xaxis=dict(gridcolor="#0f2040"), yaxis=dict(gridcolor="#0f2040",range=[0,12]),
                        title=dict(text="Side Effect Severity",font=dict(size=13,color="#e2eaf6"))
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # VOICE
                voice_text = f"Medicine: {result['medicine_name']}. Used for: {result['used_for']}. Dosage: {result['dosage']}. Warning: {result['warning']}."
                tts = gTTS(text=voice_text, lang=lang_map.get(lang,"en"), slow=False)
                tts.save("prediction.mp3")
                audio_bytes = open("prediction.mp3","rb").read()
                st.markdown('<div class="voice-card"><div class="vlabel">🔊 Voice Output</div>', unsafe_allow_html=True)
                st.audio(audio_bytes, format="audio/mp3")
                st.markdown('</div>', unsafe_allow_html=True)

                # ACTION BUTTONS
                col1, col2, col3 = st.columns(3)
                with col1:
                    # Save to favourites
                    if st.button("⭐ Save to Favourites"):
                        fav = {"name":result["medicine_name"],"used_for":result["used_for"],
                               "dosage":result["dosage"],"date":datetime.datetime.now().strftime("%d %b %Y")}
                        if not any(f["name"]==fav["name"] for f in st.session_state.favourites):
                            st.session_state.favourites.append(fav)
                            st.success("Saved!")
                        else:
                            st.info("Already saved!")
                with col2:
                    # PDF Download
                    if HAS_PDF:
                        pdf_bytes = make_pdf(result)
                        st.download_button("📄 Download PDF", data=pdf_bytes,
                            file_name=f"MediScan_{result['medicine_name'].replace(' ','_')}.pdf",
                            mime="application/pdf")
                    else:
                        st.info("Install fpdf2 for PDF")
                with col3:
                    # Alternatives
                    if st.button("💡 Alternatives"):
                        with st.spinner("Finding..."):
                            alts = get_alternatives(result['medicine_name'])
                        st.markdown(f'<div class="card" style="margin-top:0.7rem;"><div class="clabel">Alternatives</div><div class="cval" style="white-space:pre-line;">{alts}</div></div>', unsafe_allow_html=True)

                st.markdown('<div class="disc">⚕ For informational purposes only. Always consult a licensed physician.</div>', unsafe_allow_html=True)

                # seed chat
                st.session_state.chat_messages = [{"role":"ai","text":f"I've identified **{result['medicine_name']}**. Ask me anything about it!"}]

            except Exception as e:
                err = str(e)
                if "quota" in err.lower(): st.error("❌ Quota exceeded. Wait a minute.")
                elif "api" in err.lower() or "key" in err.lower(): st.error("❌ Invalid API key.")
                elif "404" in err: st.error("❌ Model not available.")
                else: st.error(f"❌ {err}")

# ══════════════════════════════════════════════
#  TAB — SEARCH
# ══════════════════════════════════════════════
elif st.session_state.active_tab == "search":
    st.markdown('<div style="font-family:DM Serif Display,serif;font-size:1.8rem;margin-bottom:0.4rem;">Medicine <em style="color:#34d399;">Search</em></div><div style="font-size:0.85rem;color:#3d5478;margin-bottom:1.2rem;">Search any medicine by name without scanning.</div>', unsafe_allow_html=True)

    search_query = st.text_input("Type medicine name...", placeholder="e.g. Paracetamol, Amoxicillin, Metformin", label_visibility="collapsed")
    if st.button("🔍 Search Medicine", use_container_width=True):
        if search_query.strip():
            with st.spinner(f"Searching {search_query}..."):
                try:
                    result = search_medicine(search_query)
                    st.session_state.current_med = result
                    st.markdown(f"""
                    <div class="result-section">
                      <div class="med-name">{result['medicine_name']}</div>
                      <div class="card-grid">
                        <div class="card wide"><div class="cicon ib">🩺</div><div class="clabel">Used For</div><div class="cval">{result['used_for']}</div></div>
                        <div class="card"><div class="cicon ip">💉</div><div class="clabel">Dosage</div><div class="cval">{result['dosage']}</div></div>
                        <div class="card"><div class="cicon ig">⚗️</div><div class="clabel">Side Effects</div><div class="cval">{result['side_effects']}</div></div>
                        <div class="card warn wide"><div class="cicon iy">⚠️</div><div class="clabel">Warning</div><div class="cval">{result['warning']}</div></div>
                        <div class="card info wide"><div class="cicon ib">🏥</div><div class="clabel">When to See Doctor</div><div class="cval">{result['doctor_visit']}</div></div>
                        <div class="card wide"><div class="cicon ig">💡</div><div class="clabel">Alternatives</div><div class="cval">{result['alternatives']}</div></div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state.chat_messages = [{"role":"ai","text":f"I found info on **{result['medicine_name']}**. Ask me anything!"}]
                except Exception as e:
                    st.error(f"❌ {str(e)}")
        else:
            st.warning("Please enter a medicine name.")

# ══════════════════════════════════════════════
#  TAB — CHAT
# ══════════════════════════════════════════════
elif st.session_state.active_tab == "chat":
    if not st.session_state.current_med:
        st.markdown('<div style="text-align:center;padding:3rem;color:#3d5478;"><div style="font-size:3rem;margin-bottom:1rem;">💬</div><div style="font-size:1rem;font-weight:600;color:#1e3358;margin-bottom:0.5rem;">No medicine loaded yet</div><div style="font-size:0.85rem;">Scan or search a medicine first!</div></div>', unsafe_allow_html=True)
    else:
        med = st.session_state.current_med
        lang = st.session_state.selected_lang
        st.markdown(f'<div style="background:var(--bg2);border:1px solid var(--border2);border-radius:14px;padding:0.9rem 1.1rem;margin-bottom:1rem;display:flex;align-items:center;gap:0.8rem;"><span style="font-size:1.5rem;">💊</span><div><div style="font-size:0.95rem;font-weight:600;">{med["medicine_name"]}</div><div style="font-size:0.7rem;color:var(--muted);font-family:DM Mono,monospace;">Language: {lang}</div></div></div>', unsafe_allow_html=True)

        quick = ["What are the side effects?","Can I take after food?","What is the dosage?","Any drug interactions?","Is it safe for children?","What if I miss a dose?"]
        qc = st.columns(3)
        for i,q in enumerate(quick):
            with qc[i%3]:
                if st.button(q, key=f"q{i}"):
                    st.session_state.chat_messages.append({"role":"user","text":q})
                    med_ctx = f"{med['medicine_name']}, used for {med.get('used_for','')}"
                    with st.spinner("Thinking..."):
                        reply = chat_with_ai(q, med_ctx, lang)
                    st.session_state.chat_messages.append({"role":"ai","text":reply})
                    st.rerun()

        st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)
        chat_html = '<div class="chat-wrap">'
        for msg in st.session_state.chat_messages:
            if msg["role"]=="ai":
                chat_html += f'<div class="msg"><div class="msg-avatar ai-av">🤖</div><div class="msg-bubble ai-bubble">{msg["text"]}</div></div>'
            else:
                chat_html += f'<div class="msg user"><div class="msg-avatar user-av">👤</div><div class="msg-bubble user-bubble">{msg["text"]}</div></div>'
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

        ci1,ci2 = st.columns([5,1])
        with ci1:
            user_input = st.text_input("Ask anything...", placeholder="e.g. Can I take this with paracetamol?", key="chat_in", label_visibility="collapsed")
        with ci2:
            if st.button("Send"):
                if user_input.strip():
                    st.session_state.chat_messages.append({"role":"user","text":user_input})
                    med_ctx = f"{med['medicine_name']}, used for {med.get('used_for','')}"
                    with st.spinner(""):
                        reply = chat_with_ai(user_input, med_ctx, lang)
                    st.session_state.chat_messages.append({"role":"ai","text":reply})
                    st.rerun()

        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_messages = [{"role":"ai","text":f"Chat cleared! Ask me anything about {med['medicine_name']}."}]
            st.rerun()

# ══════════════════════════════════════════════
#  TAB — DRUG INTERACTION CHECKER
# ══════════════════════════════════════════════
elif st.session_state.active_tab == "checker":
    st.markdown('<div style="font-family:DM Serif Display,serif;font-size:1.8rem;margin-bottom:0.4rem;">Drug <em style="color:#34d399;">Interaction</em> Checker</div><div style="font-size:0.85rem;color:#3d5478;margin-bottom:1.2rem;">Check if two medicines are safe to take together.</div>', unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1: med1 = st.text_input("Medicine 1", placeholder="e.g. Paracetamol")
    with c2: med2 = st.text_input("Medicine 2", placeholder="e.g. Ibuprofen")

    if st.button("⚗️ Check Interaction", use_container_width=True):
        if med1.strip() and med2.strip():
            with st.spinner("Checking..."):
                result = drug_interaction(med1, med2)
            level = result["level"]
            card_cls = {"Safe":"safe","Severe":"danger"}.get(level,"warn")
            chip_cls = {"Safe":"chip-green","Severe":"chip-red"}.get(level,"chip-yellow")
            icon = {"Safe":"✅","Severe":"🚨"}.get(level,"⚠️")
            st.markdown(f"""
            <div class="result-section" style="margin-top:1.2rem;">
              <span class="chip {chip_cls}" style="margin-bottom:1rem;display:inline-flex;">{icon} {level} Interaction</span>
              <div class="card-grid">
                <div class="card {card_cls} wide"><div class="clabel">{med1} + {med2}</div><div class="cval" style="font-size:1rem;">{result['effect']}</div></div>
                <div class="card wide"><div class="cicon ig">💡</div><div class="clabel">Advice</div><div class="cval">{result['advice']}</div></div>
              </div>
              <div class="disc">Always consult your doctor before combining medicines.</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.warning("Enter both medicine names.")

    st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.7rem;color:#1e3358;font-family:DM Mono,monospace;text-align:center;">Try: Paracetamol + Ibuprofen · Aspirin + Warfarin · Metformin + Alcohol</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  TAB — PRESCRIPTION READER
# ══════════════════════════════════════════════
elif st.session_state.active_tab == "rx":
    st.markdown('<div style="font-family:DM Serif Display,serif;font-size:1.8rem;margin-bottom:0.4rem;">Prescription <em style="color:#34d399;">Reader</em></div><div style="font-size:0.85rem;color:#3d5478;margin-bottom:1.2rem;">Upload a prescription image to extract all medicine names automatically.</div>', unsafe_allow_html=True)

    rx_file = st.file_uploader("Upload Prescription", type=['png','jpg','jpeg'], label_visibility="collapsed")
    if rx_file:
        rx_img = Image.open(rx_file).convert('RGB')
        c1,c2,c3 = st.columns([1,4,1])
        with c2: st.image(rx_img, use_container_width=True)

        with st.spinner("📄 Reading prescription..."):
            try:
                rx_result = read_prescription(rx_img)
                if "NO_MEDICINES_FOUND" in rx_result:
                    st.warning("No medicines found. Try a clearer image.")
                else:
                    st.markdown('<div class="sdiv"></div>', unsafe_allow_html=True)
                    st.markdown('<div style="font-size:0.65rem;color:#3d5478;font-family:DM Mono,monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.8rem;">Medicines Found in Prescription</div>', unsafe_allow_html=True)
                    lines = [l.strip() for l in rx_result.split('\n') if l.strip() and 'MEDICINE:' in l]
                    if not lines: lines = [l for l in rx_result.split('\n') if l.strip()]
                    for line in lines:
                        st.markdown(f'<div class="card" style="margin-bottom:0.5rem;"><div class="cval">💊 {line}</div></div>', unsafe_allow_html=True)
                    st.markdown('<div class="disc">⚕ Always verify extracted medicines with your doctor or pharmacist.</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ {str(e)}")

# ══════════════════════════════════════════════
#  TAB — FAVOURITES
# ══════════════════════════════════════════════
elif st.session_state.active_tab == "favourites":
    st.markdown('<div style="font-family:DM Serif Display,serif;font-size:1.8rem;margin-bottom:0.4rem;">⭐ Saved <em style="color:#34d399;">Medicines</em></div><div style="font-size:0.85rem;color:#3d5478;margin-bottom:1.2rem;">Your favourite medicines saved for quick reference.</div>', unsafe_allow_html=True)

    if not st.session_state.favourites:
        st.markdown('<div style="text-align:center;padding:3rem;color:#3d5478;"><div style="font-size:3rem;margin-bottom:1rem;">⭐</div><div style="font-size:1rem;font-weight:600;color:#1e3358;margin-bottom:0.5rem;">No saved medicines yet</div><div style="font-size:0.85rem;">Scan a medicine and click Save to Favourites!</div></div>', unsafe_allow_html=True)
    else:
        for i, fav in enumerate(st.session_state.favourites):
            st.markdown(f"""
            <div class="fav-item">
              <div style="display:flex;align-items:center;justify-content:space-between;">
                <div class="hist-med">⭐ {fav['name']}</div>
                <span class="chip chip-yellow" style="font-size:0.55rem;">{fav['date']}</span>
              </div>
              <div class="hist-meta">🩺 {fav['used_for'][:80]}... &nbsp;·&nbsp; 💉 {fav['dosage'][:40]}</div>
            </div>
            """, unsafe_allow_html=True)
        if st.button("🗑️ Clear Favourites"):
            st.session_state.favourites = []
            st.rerun()

# ══════════════════════════════════════════════
#  TAB — HISTORY
# ══════════════════════════════════════════════
elif st.session_state.active_tab == "history":
    st.markdown('<div style="font-family:DM Serif Display,serif;font-size:1.8rem;margin-bottom:0.4rem;">Scan <em style="color:#34d399;">History</em></div><div style="font-size:0.85rem;color:#3d5478;margin-bottom:1.2rem;">All medicines scanned in this session.</div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown('<div style="text-align:center;padding:3rem;color:#3d5478;"><div style="font-size:3rem;margin-bottom:1rem;">📋</div><div style="font-size:1rem;font-weight:600;color:#1e3358;margin-bottom:0.5rem;">No scans yet</div><div style="font-size:0.85rem;">Go to Scan tab to get started!</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chip chip-blue" style="margin-bottom:1rem;">{len(st.session_state.history)} scans this session</div>', unsafe_allow_html=True)
        for item in reversed(st.session_state.history):
            conf = item['confidence']
            chip = {"High":"chip-green","Medium":"chip-yellow"}.get(conf,"chip-red")
            st.markdown(f"""
            <div class="hist-item">
              <div style="display:flex;align-items:center;justify-content:space-between;">
                <div class="hist-med">💊 {item['name']}</div>
                <span class="chip {chip}" style="font-size:0.55rem;">{conf}</span>
              </div>
              <div class="hist-meta">📅 {item['date']} &nbsp;·&nbsp; Expiry: {item['expiry']}</div>
            </div>
            """, unsafe_allow_html=True)
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div class="footer">
  MediScan AI <span class="dot">·</span> Built for visually impaired users
  <span class="dot">·</span> Powered by Google Gemini Vision
  <br>Always consult a licensed doctor for medical advice
</div>
""", unsafe_allow_html=True)