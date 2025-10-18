import streamlit as st
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
from gtts import gTTS

st.title("AI Medicine Identifier with Voice")

# Load trained model 
model = load_model('medicine_model.h5')
class_names = ['paracetamol','dolo650','amoxicillin']

# Upload medicine image
uploaded_file = st.file_uploader("Upload Medicine Image", type=['png','jpg','jpeg'])

if uploaded_file:
    img = Image.open(uploaded_file).resize((224,224))
    st.image(img, caption="Uploaded Medicine Image", use_column_width=True)

    x = np.array(img)/255.0
    x = np.expand_dims(x, axis=0)

    pred = model.predict(x)
    pred_class = class_names[np.argmax(pred)]

    # Show prediction
    st.write("Prediction:", pred_class)

    # Convert prediction to voice
    tts = gTTS(text=f"This medicine is {pred_class}", lang='en')
    tts.save("prediction.mp3")
    audio_file = open("prediction.mp3", "rb").read()
    st.audio(audio_file, format="audio/mp3")