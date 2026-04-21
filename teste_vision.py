import streamlit as st
import requests
import base64
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image

# Configurações de API
API_KEY = st.secrets["vision_api_key"]
URL_VISION = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"

@st.cache_resource
def load_yolo():
    return YOLO('best.pt')

model = load_yolo()

st.title("🎯 Jumbo Vision - Leitura Direcionada")

foto_bruta = st.camera_input("Tire foto da folha")

if foto_bruta:
    # 1. Converter para formato OpenCV
    file_bytes = np.asarray(bytearray(foto_bruta.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    
    # 2. YOLO detecta os retângulos (boxes)
    results = model.predict(img, conf=0.25)
    
    st.subheader("Resultados da Extração:")
    
    for box in results[0].boxes:
        # Coordenadas do retângulo da YOLO
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        classe = model.names[int(box.cls[0])]
        
        # 3. RECORTE (Crop) - Pegamos apenas o que está dentro do retângulo
        # Adicionamos uma pequena margem (padding) de 5px para não cortar as letras
        crop = img[max(0, y1-5):y2+5, max(0, x1-5):x2+5]
        
        if crop.size > 0:
            # 4. MANDAR PARA O GOOGLE VISION (Apenas o recorte)
            _, buffer = cv2.imencode('.jpg', crop)
            img_base64 = base64.b64encode(buffer).decode("utf-8")
            
            payload = {
                "requests": [{"image": {"content": img_base64}, "features": [{"type": "TEXT_DETECTION"}]}]
            }
            
            response = requests.post(URL_VISION, json=payload)
            res_json = response.json()
            
            try:
                # O Google agora só vê o que está no seu retângulo!
                texto_lido = res_json['responses'][0]['textAnnotations'][0]['description'].strip()
                
                # Exibe o resultado específico para cada campo
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB), caption=classe)
                with col2:
                    st.text_input(f"Valor lido para {classe}:", value=texto_lido, key=f"input_{x1}")
            except:
                st.warning(f"IA localizou {classe}, mas o Google não conseguiu ler o texto interno.")
