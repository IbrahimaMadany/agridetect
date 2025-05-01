import streamlit as st
import tensorflow as tf
import numpy as np
import sqlite3
import pandas as pd
from datetime import datetime
from PIL import Image

# ----------------------------- Configuration -----------------------------
st.set_page_config(page_title="Agridetect", layout="centered")

# ----------------------------- Fonction de prédiction -----------------------------
def model_prediction(test_image):
    model = tf.keras.models.load_model(
        "C:\\Users\\AGUIBOU CAMARA\\Desktop\\New Plant Diseases Dataset(Augmented)\\trained_plant_disease_model.keras"
    )
    image = tf.keras.preprocessing.image.load_img(test_image, target_size=(128, 128))
    input_arr = tf.keras.preprocessing.image.img_to_array(image)
    input_arr = np.expand_dims(input_arr, axis=0)  # Convertir en batch
    predictions = model.predict(input_arr)
    confidence = np.max(predictions) * 100
    result_index = np.argmax(predictions)
    return result_index, confidence

# ----------------------------- Labels des classes -----------------------------
class_name = ['Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy',
              'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew',
              'Cherry_(including_sour)___healthy', 'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
              'Corn_(maize)___Common_rust', 'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy',
              'Grape___Black_rot', 'Grape___Esca_(Black_Measles)', 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)',
              'Grape___healthy', 'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot',
              'Peach___healthy', 'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy',
              'Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy',
              'Raspberry___healthy', 'Soybean___healthy', 'Squash___Powdery_mildew',
              'Strawberry___Leaf_scorch', 'Strawberry___healthy', 'Tomato___Bacterial_spot',
              'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold',
              'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite',
              'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus',
              'Tomato___healthy']

# ----------------------------- Base de données -----------------------------
conn = sqlite3.connect("agridetect_predictions.db", check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        disease TEXT,
        confidence REAL,
        status TEXT
    )
''')
conn.commit()

# ----------------------------- Menu latéral -----------------------------
st.sidebar.image("logo_agridetect.png", width=150)
st.sidebar.title("📋 Menu")
app_mode = st.sidebar.selectbox("Navigation", ["Accueil", "Reconnaissance", "À propos"])

# ----------------------------- Pages -----------------------------

# Accueil
if app_mode == "Accueil":
    st.image("logo_agridetect.png", width=200)
    st.header("🌿 Agridetect - Système intelligent de détection des maladies des plantes")
    st.image("home_page.jpeg", use_column_width=True)
    st.markdown("""
    Bienvenue sur **Agridetect** 🌱🔍  
    Téléversez une image de feuille de plante, et notre système l’analysera pour détecter toute maladie.  
    Protégeons nos cultures pour une agriculture durable ! 🌾
    """)

# Reconnaissance
elif app_mode == "Reconnaissance":
    st.header("🦠 Reconnaissance de maladie")
    st.info("Téléversez une image de feuille (format JPG ou PNG) pour détecter d’éventuelles maladies.")

    test_image = st.file_uploader("📤 Téléverser une image", type=["jpg", "jpeg", "png"])

    if test_image:
        if st.button("📷 Afficher l'image"):
            st.image(test_image, caption="Image téléversée", use_column_width=True)

        if st.button("🔍 Prédire"):
            st.snow()
            result_index, confidence = model_prediction(test_image)
            result_label = class_name[result_index]

            if "healthy" in result_label:
                status = "Saine"
                message = "✅ La feuille est saine."
                color = "green"
            else:
                status = "Malade"
                message = "⚠️ La feuille est infectée !"
                color = "red"

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO predictions (date, disease, confidence, status) VALUES (?, ?, ?, ?)",
                      (now, result_label.replace('_', ' '), confidence, status))
            conn.commit()

            col1, col2 = st.columns(2)
            with col1:
                st.image(test_image, caption="Image analysée", use_column_width=True)
            with col2:
                st.markdown(f"### 🩺 **Diagnostic** : {result_label.replace('_', ' ')}")
                st.markdown(f"<span style='color:{color}; font-size:20px;'>{message}</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='color:{color}; font-size:20px;'>Confiance : {confidence:.2f} %</span>", unsafe_allow_html=True)

    # Historique des prédictions
    st.subheader("📊 Historique des prédictions")
    df = pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC", conn)
    st.dataframe(df)

    # Sélection pour suppression
    if not df.empty:
        ids_to_delete = st.multiselect("🗑️ Sélectionner les prédictions à supprimer (par ID) :", df["id"])
        if st.button("Supprimer les prédictions sélectionnées"):
            if ids_to_delete:
                c.executemany("DELETE FROM predictions WHERE id = ?", [(i,) for i in ids_to_delete])
                conn.commit()
                st.success("✅ Prédictions supprimées avec succès.")
                st.rerun()
            else:
                st.warning("Veuillez sélectionner au moins un ID à supprimer.")

    # Télécharger CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger l’historique (CSV)", csv, "historique_predictions.csv", "text/csv")

    # Feedback
    st.subheader("🗣️ Donnez votre avis")
    with st.form("formulaire_feedback"):
        user_feedback = st.text_area("Que pensez-vous de cette application ?")
        submitted = st.form_submit_button("Envoyer")
        if submitted:
            st.success("Merci pour votre retour ! 🙏")

# À propos
elif app_mode == "À propos":
    st.header("ℹ️ À propos de l'application")
    st.markdown("""
    **Agridetect** est un outil intelligent basé sur un modèle d’IA (CNN) entraîné sur plus de 87 000 images de feuilles saines et malades.  
    Il couvre 38 classes de maladies pour aider les agriculteurs à diagnostiquer plus rapidement les infections.

    - 📌 Basé sur TensorFlow et Streamlit  
    - 📸 Reconnaissance par image  
    - 🧠 Prédiction en temps réel  
    - 📈 Historique des prédictions stocké localement  
    """)

    st.markdown("---")
    st.subheader("👨🏽‍💻 Auteur")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("aguibou.jpg", width=120)
    with col2:
        st.markdown("""
    **Nom et Prénom :** CAMARA Ibrahima Madany  
    **Profil :** Data Scientist & Développeur IA  
    **Email :** camaraimadany@gmail.com  
    **Téléphone :** +221 78 636 52 39  
    **LinkedIn :** [linkedin.com/in/ibrahima-madany-camara-0939a025b](https://www.linkedin.com/in/ibrahima-madany-camara-0939a025b/)  
    **Portfolio :** [sites.google.com/view/camaraibrahimamadany](https://sites.google.com/view/camaraibrahimamadany/accueil)  
    **GitHub :** [github.com/IbrahimaMadany](https://github.com/IbrahimaMadany)       
        """)

