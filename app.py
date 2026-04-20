import streamlit as st
import requests
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from PIL import Image

# URL do Google Apps Script
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Scanner Jumbo v2", layout="centered")

@st.cache_resource
def load_model():
    return YOLO('best.pt')

model = load_model()

# Estado da sessão para garantir a sequência correta
if "ia_ok" not in st.session_state:
    st.session_state.ia_ok = None

st.title("🚀 Sistema de Checkout - Jumbo CDP")

# --- PASSO 1: IA (ROBOFLOW) ---
st.subheader("1. Folha de Pedido")
foto_folha = st.camera_input("Capture a folha", key="cam1")

if foto_folha:
    img_f = Image.open(foto_folha)
    results = model(img_f)
    # Extrai as classes: Nome Detento, Unidade Prisional, etc.
    labels = [model.names[int(box.cls[0])] for box in results[0].boxes]
    
    if labels:
        st.session_state.ia_ok = ", ".join(set(labels))
        st.success(f"✅ Detectado: {st.session_state.ia_ok}")
    else:
        st.warning("IA não detectou campos. Tente focar melhor.")

# --- PASSO 2: CÓDIGO DE BARRAS ---
if st.session_state.ia_ok:
    st.divider()
    st.subheader("2. Pacote (Código de Barras)")
    foto_b = st.camera_input("Escanear rastreio", key="cam2")

    if foto_b:
        img_b = Image.open(foto_b)
        barcodes = decode(img_b)
        
        if barcodes:
            rastreio_lido = barcodes[0].data.decode('utf-8').strip()
            st.info(f"📦 Código: {rastreio_lido}")
            
            # --- ENVIO FINAL ---
            if st.button("CONFIRMAR ENVIO PARA NUVEM", variant="primary"):
                payload = {
                    "rastreio": rastreio_lido,           # Vai para B
                    "classes": st.session_state.ia_ok,   # Vai para C
                    "origem": "App_Streamlit_V2"         # Vai para D
                }
                
                try:
                    # Timeout de 10s para não travar o app se a internet da Jumbo oscilar
                    res = requests.post(URL_GOOGLE, json=payload, timeout=10)
                    if res.status_code == 200:
                        st.balloons()
                        st.success("✅ Pedido arquivado com sucesso!")
                        # Limpa tudo para o próximo operador
                        st.session_state.ia_ok = None
                        st.rerun()
                    else:
                        st.error("Erro no servidor do Google.")
                except Exception as e:
                    st.error(f"Erro de conexão: {e}")
        else:
            st.warning("Aguardando leitura do código de barras...")

# Barra lateral para emergência
if st.sidebar.button("Resetar Scanner"):
    st.session_state.ia_ok = None
    st.rerun()
