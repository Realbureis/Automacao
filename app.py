import streamlit as st
import requests
import base64
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image, ImageEnhance, ImageOps
import io

# --- CONFIGURAÇÃO ---
if "vision_api_key" in st.secrets:
    API_KEY = st.secrets["vision_api_key"]
else:
    st.error("Configure a 'vision_api_key' nos Secrets!")
    st.stop()

URL_VISION = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
URL_SHEETS = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Jumbo Vision Pro", layout="centered")

@st.cache_resource
def load_yolo():
    return YOLO('best.pt')

model = load_yolo()

if "dados_finais" not in st.session_state:
    st.session_state.dados_finais = {}

st.title("🚀 Scanner de Alta Resolução")

# --- CAPTURA ---
# DICA: No iPhone, tente manter uma distância de 30cm do papel
foto_bruta = st.camera_input("Capture a folha com nitidez")

if foto_bruta:
    with st.spinner('Otimizando pixels para OCR...'):
        # 1. Converter para PIL e corrigir orientação
        img_pil = Image.open(foto_bruta)
        img_pil = ImageOps.exif_transpose(img_pil)
        
        # 2. TRATAMENTO DE IMAGEM (O segredo para pixels ruins)
        # Aumentamos o contraste e nitidez para as letras "saltarem" para a IA
        img_pil = ImageEnhance.Contrast(img_pil).enhance(2.0)
        img_pil = ImageEnhance.Sharpness(img_pil).enhance(2.0)
        
        # 3. Converter para OpenCV (formato que a YOLO usa)
        img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
        # 4. YOLO localiza os campos
        results = model.predict(img_cv, conf=0.25)
        
        temp_dict = {}
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            classe = model.names[int(box.cls[0])]
            
            # Recorte com margem (padding) maior para garantir que não corta o texto
            pad = 15
            crop = img_cv[max(0, y1-pad):min(img_cv.shape[0], y2+pad), 
                          max(0, x1-pad):min(img_cv.shape[1], x2+pad)]
            
            if crop.size > 0:
                # 5. Salvar o recorte em ALTA QUALIDADE (JPEG 100) para o Google
                _, buffer = cv2.imencode('.jpg', crop, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                img_b64 = base64.b64encode(buffer).decode("utf-8")
                
                payload = {
                    "requests": [{
                        "image": {"content": img_b64},
                        "features": [{"type": "DOCUMENT_TEXT_DETECTION"}] # Modo mais forte de OCR
                    }]
                }
                
                response = requests.post(URL_VISION, json=payload)
                res_json = response.json()
                
                try:
                    # Pega o texto do recorte
                    texto = res_json['responses'][0]['textAnnotations'][0]['description'].strip()
                    temp_dict[classe] = texto
                except:
                    temp_dict[classe] = "Falha na nitidez"

        st.session_state.dados_finais = temp_dict

# --- FORMULÁRIO ---
if st.session_state.dados_finais:
    st.divider()
    st.subheader("Conferência de Dados")
    
    for c, v in st.session_state.dados_finais.items():
        st.session_state.dados_finais[c] = st.text_input(f"Campo {c}:", value=v)

    if st.button("CONFIRMAR E ENVIAR", use_container_width=True):
        res_str = " | ".join([f"{k}: {v}" for k, v in st.session_state.dados_finais.items()])
        payload_sheets = {"rastreio": "SCAN_ALTA_RES", "classes": res_str, "origem": "Vision_Pro_Jumbo"}
        
        try:
            requests.post(URL_SHEETS, json=payload_sheets, timeout=15)
            st.balloons()
            st.success("✅ Enviado!")
            st.session_state.dados_finais = {}
        except:
            st.error("Erro na planilha.")
