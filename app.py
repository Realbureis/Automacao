import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
from ultralytics import YOLO
import requests
import base64
import io
import json

# --- 1. CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="Jumbo Vision Pro", layout="centered")

# Puxa a API Key do Gmail pessoal dos Secrets
if "vision_api_key" in st.secrets:
    API_KEY = st.secrets["vision_api_key"]
else:
    st.error("Erro: Adicione 'vision_api_key' nos Secrets do Streamlit!")
    st.stop()

URL_VISION = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
URL_SHEETS = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

# Carrega a YOLO (Certifique-se de que o 'best.pt' está no GitHub)
@st.cache_resource
def load_model():
    return YOLO('best.pt')

model = load_model()

# Inicializa o estado da memória para não perder dados
if "dados_identificados" not in st.session_state:
    st.session_state.dados_identificados = {}

st.title("🚀 Scanner Logístico Jumbo")
st.write("IA de alta precisão para leitura de pedidos.")

# --- 2. CAPTURA DE IMAGEM (Definindo a variável antes de usar) ---
foto_bruta = st.camera_input("Capture a folha de pedido")

# --- 3. PROCESSAMENTO (Apenas se a foto existir) ---
if foto_bruta is not None:
    with st.spinner('Otimizando pixels e identificando campos...'):
        # Converter para formato OpenCV
        file_bytes = np.asarray(bytearray(foto_bruta.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        # YOLO localiza onde estão os campos (Telefone, Nome, etc)
        results = model.predict(img, conf=0.25)
        
        temp_dados = {}
        
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            classe = model.names[int(box.cls[0])]
            
            # Recorte com margem de segurança (Padding)
            pad = 15
            crop = img[max(0, y1-pad):min(img.shape[0], y2+pad), 
                       max(0, x1-pad):min(img.shape[1], x2+pad)]
            
            if crop.size > 0:
                # --- MELHORIA DE PIXEL (SUPER RESOLUÇÃO DIGITAL) ---
                # Aumentamos o recorte em 2x para o Google enxergar melhor as letras
                crop_high_res = cv2.resize(crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                
                # Aumentar contraste e nitidez via PIL
                pil_crop = Image.fromarray(cv2.cvtColor(crop_high_res, cv2.COLOR_BGR2RGB))
                pil_crop = ImageEnhance.Contrast(pil_crop).enhance(2.0)
                pil_crop = ImageEnhance.Sharpness(pil_crop).enhance(2.0)
                
                # Converter para Base64 (PNG para não perder qualidade)
                buffer = io.BytesIO()
                pil_crop.save(buffer, format="PNG")
                img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                
                # Enviar para o Google Vision
                payload = {
                    "requests": [{
                        "image": {"content": img_b64},
                        "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
                    }]
                }
                
                try:
                    response = requests.post(URL_VISION, json=payload, timeout=10)
                    res_json = response.json()
                    texto = res_json['responses'][0]['textAnnotations'][0]['description'].strip()
                    temp_dados[classe] = texto
                except:
                    temp_dados[classe] = "Erro na leitura"

        st.session_state.dados_identificados = temp_dados

# --- 4. EXIBIÇÃO E CONFERÊNCIA ---
if st.session_state.dados_identificados:
    st.divider()
    st.subheader("📝 Conferência de Dados")
    
    # Gera campos de edição para o operador confirmar
    for campo, valor in st.session_state.dados_identificados.items():
        st.session_state.dados_identificados[campo] = st.text_input(f"{campo}:", value=valor)

    if st.button("✅ TUDO CERTO, ENVIAR NUVEM", use_container_width=True):
        # Formata os dados para a planilha
        texto_final = " | ".join([f"{k}: {v}" for k, v in st.session_state.dados_identificados.items()])
        
        payload_sheets = {
            "rastreio": "SCAN_PRO_ALTA_RES",
            "classes": texto_final,
            "origem": "iPhone_Galpão_Jumbo"
        }
        
        try:
            requests.post(URL_SHEETS, json=payload_sheets, timeout=15)
            st.balloons()
            st.success("Enviado com sucesso!")
            st.session_state.dados_identificados = {} # Limpa para o próximo
        except:
            st.error("Erro ao salvar na planilha.")
