import streamlit as st
import requests
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from PIL import Image
import time

# 1. LINK DO GOOGLE
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Checkout Jumbo", layout="centered")

# 2. CARREGAMENTO DO MODELO
@st.cache_resource
def load_model():
    # Tenta carregar o arquivo vindo do Hugging Face que você subiu
    return YOLO('best.pt')

try:
    model = load_model()
    st.success("🤖 Inteligência carregada com sucesso!")
except Exception as e:
    st.error(f"Erro ao carregar o arquivo 'best.pt'. Certifique-se de que ele está no GitHub. Erro: {e}")
    st.stop()

# Controle de estado
if "ia_status" not in st.session_state:
    st.session_state.ia_status = None

st.title("🚀 Checkout Jumbo CDP")

# --- PASSO 1: FOTO DA FOLHA ---
st.subheader("1. Escanear Folha de Pedido")
foto_folha = st.camera_input("Capture a folha", key="cam1")

if foto_folha:
    img_f = Image.open(foto_folha)
    results = model(img_f)
    labels = [model.names[int(box.cls[0])] for box in results[0].boxes]
    
    if labels:
        st.session_state.ia_status = ", ".join(set(labels))
        st.info(f"Campos identificados: {st.session_state.ia_status}")
    else:
        st.session_state.ia_status = "Nenhum campo detectado"

# --- PASSO 2: CÓDIGO DE BARRAS ---
if st.session_state.ia_status:
    st.divider()
    st.subheader("2. Escanear Rastreio")
    foto_bar = st.camera_input("Capture o código do pacote", key="cam2")

    if foto_bar:
        img_b = Image.open(foto_bar)
        barcodes = decode(img_b)
        
        if barcodes:
            rastreio = barcodes[0].data.decode('utf-8').strip()
            st.success(f"📦 Código: {rastreio}")
            
            if st.button("CONFIRMAR E ENVIAR"):
                payload = {
                    "rastreio": str(rastreio),
                    "classes": str(st.session_state.ia_status),
                    "origem": "Jumbo_Producao_Final"
                }
                
                with st.spinner('Enviando...'):
                    try:
                        res = requests.post(URL_GOOGLE, json=payload, timeout=20)
                        if res.status_code in [200, 302]:
                            st.balloons()
                            st.success("✅ Pedido arquivado!")
                            time.sleep(2)
                            st.session_state.ia_status = None
                            st.rerun()
                        else:
                            st.error(f"Erro no Google Script: {res.status_code}")
                    except Exception as e:
                        st.error(f"Falha de conexão: {e}")
