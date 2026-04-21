import streamlit as st
import requests
import base64
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
import json

# --- CONFIGURAÇÕES DE API ---
# Certifique-se de que a chave 'vision_api_key' está nos Secrets do Streamlit
if "vision_api_key" in st.secrets:
    API_KEY = st.secrets["vision_api_key"]
else:
    st.error("Erro: Adicione 'vision_api_key' nos Secrets do Streamlit Cloud.")
    st.stop()

URL_VISION = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
URL_SHEETS = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Jumbo Vision - OCR Inteligente", layout="centered")

@st.cache_resource
def load_yolo():
    # Carrega o modelo que identifica onde estão os campos
    return YOLO('best.pt')

model = load_yolo()

# Inicializa o estado para não perder os dados lidos
if "resultados_ia" not in st.session_state:
    st.session_state.resultados_ia = {}

st.title("🚀 Scanner Inteligente Jumbo")
st.write("A YOLO localiza os campos e o Google Vision lê o conteúdo.")

# --- PASSO 1: FOTO DA FOLHA ---
foto_folha = st.camera_input("Tire foto da folha de pedido")

if foto_folha:
    # Converter para formato OpenCV
    file_bytes = np.asarray(bytearray(foto_folha.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    
    # YOLO detecta os retângulos (boxes)
    with st.spinner('YOLO localizando campos...'):
        results = model.predict(img, conf=0.25)
    
    temp_dados = {}
    
    # Processa cada caixa detectada pela sua IA
    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        classe = model.names[int(box.cls[0])]
        
        # RECORTA a imagem (Crop) com uma margem de segurança
        pad = 5
        crop = img[max(0, y1-pad):min(img.shape[0], y2+pad), max(0, x1-pad):min(img.shape[1], x2+pad)]
        
        if crop.size > 0:
            # Envia apenas o RECORTE para o Google Vision
            _, buffer = cv2.imencode('.jpg', crop)
            img_b64 = base64.b64encode(buffer).decode("utf-8")
            
            payload = {
                "requests": [{
                    "image": {"content": img_b64},
                    "features": [{"type": "TEXT_DETECTION"}]
                }]
            }
            
            with st.spinner(f'Lendo {classe}...'):
                response = requests.post(URL_VISION, json=payload)
                res_json = response.json()
                
                try:
                    texto = res_json['responses'][0]['textAnnotations'][0]['description'].strip()
                    temp_dados[classe] = texto
                except:
                    temp_dados[classe] = "Erro na leitura"

    st.session_state.resultados_ia = temp_dados
    st.success("Processamento concluído!")

# --- PASSO 2: CONFERÊNCIA E ENVIO ---
if st.session_state.resultados_ia:
    st.divider()
    st.subheader("Conferência de Dados")
    
    # Cria campos de texto baseados no que a YOLO encontrou
    for campo, valor in st.session_state.resultados_ia.items():
        st.session_state.resultados_ia[campo] = st.text_input(f"Confirmar {campo}:", value=valor)

    if st.button("ENVIAR PARA PLANILHA", use_container_width=True):
        # Transforma o dicionário em texto para a coluna 'classes' da planilha
        texto_final = " | ".join([f"{k}: {v}" for k, v in st.session_state.resultados_ia.items()])
        
        payload_sheets = {
            "rastreio": "SCAN_YOLO_VISION",
            "classes": texto_final,
            "origem": "Sistema_Integrado_Jumbo"
        }
        
        try:
            requests.post(URL_SHEETS, json=payload_sheets, timeout=15)
            st.balloons()
            st.success("✅ Tudo enviado com sucesso!")
            st.session_state.resultados_ia = {}
        except:
            st.error("Erro ao conectar com a planilha.")
