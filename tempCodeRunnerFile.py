
    decoded = tf.keras.applications.mobilenet_v2.decode_predictions(preds, top=1)[0][0][1]

    st.success(f"✅ Predicted Medicine (or closest match): {decoded}")

    # Voice output
    text = f"This is {decoded}. Please take it after doctor's advice."
    tts = gTTS(text)
    tts.save("output.mp3")
    st.audio("output.mp3", format="audio/mp3")

    st.markdown("🗣 Audio output generated successfully!")