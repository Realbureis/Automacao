import streamlit as st
import requests
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from PIL import Image
import os

# CONFIGURAÇÕES
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Checkout Jumbo", layout="centered")

@st.cache_resource
def load_model():
    model_path = 'best.pt'
    # Verifica se o arquivo existe e tem tamanho de um modelo real (> 1MB)
    if os.path.exists(model_path) and os.path.getsize(model_path) > 1000000:
        return YOLO(model_path)
    return None

model = load_model()

if "ia_ok" not in st.session_state:
    st.session_state.ia_ok = None

st.title("🚀 Checkout Logístico - Jumbo")

if model is None:
    st.error("⏳ O arquivo 'best.pt' está sendo carregado pelo servidor. Aguarde 30 segundos e atualize a página.")
    st.stop()

# --- PASSO 1: IA ---
st.subheader("1. Escanear Folha de Pedido")
foto_folha = st.camera_input("Foto da folha", key="c1")

if foto_folha:
    img_f = Image.open(foto_folha)
    results = model(img_f)
    labels = [model.names[int(box.cls[0])] for box in results[0].boxes]
    
    if labels:
        st.session_state.ia_ok = ", ".join(set(labels))
        st.success(f"✅ IA Detectou: {st.session_state.ia_ok}")
    else:
        st.warning("IA não reconheceu os campos.")

# --- PASSO 2: BARCODE ---
if st.session_state.ia_ok:
    st.divider()
    st.subheader("2. Escanear Código do Pacote")
    foto_b = st.camera_input("Foto do código", key="c2")

    if foto_b:
        img_b = Image.open(foto_b)
        barcodes = decode(img_b)
        
        if barcodes:
            rastreio = barcodes[0].data.decode('utf-8').strip()
            st.info(f"📦 Código: {rastreio}")
            
            if st.button("FINALIZAR E ENVIAR"):
                payload = {
                    "rastreio": str(rastreio),
                    "classes": str(st.session_state.ia_ok),
                    "origem": "Sistema_HF_Final"
                }
                
                try:
                    res = requests.post(URL_GOOGLE, json=payload, timeout=15)
                    if res.status_code == 200:
                        st.balloons()
                        st.success("✅ Pedido arquivado na nuvem!")
                        st.session_state.ia_ok = None
                        st.rerun()
                except:
                    st.error("Erro na conexão.")
