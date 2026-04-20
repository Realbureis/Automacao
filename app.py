import streamlit as st
import requests
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from PIL import Image
import time

# 1. LINK DO GOOGLE (Certifique-se de que é a versão 'Anyone')
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Checkout Jumbo", layout="centered")

@st.cache_resource
def load_model():
    # Tenta carregar o modelo que você subiu do Hugging Face
    return YOLO('best.pt')

try:
    model = load_model()
except Exception as e:
    st.error(f"Erro ao carregar 'best.pt': {e}")
    st.stop()

if "ia_status" not in st.session_state:
    st.session_state.ia_status = None

st.title("🚀 Checkout Jumbo")

# --- PASSO 1: FOTO DA FOLHA (IA) ---
st.subheader("1. Escanear Marcação na Folha")
foto_folha = st.camera_input("Tire foto da marcação", key="cam1")

if foto_folha:
    img_f = Image.open(foto_folha)
    # Roda a detecção com um pouco mais de sensibilidade (conf=0.3)
    results = model.predict(img_f, conf=0.3)
    
    # Extrai os nomes das classes detectadas
    labels = []
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        label_name = model.names[class_id]
        labels.append(label_name)
    
    if labels:
        # Remove duplicados e junta em um texto limpo
        st.session_state.ia_status = " + ".join(sorted(list(set(labels))))
        st.success(f"✅ Detectado: {st.session_state.ia_status}")
    else:
        st.session_state.ia_status = "Nenhuma marcação encontrada"
        st.warning("⚠️ A IA não leu a marcação. Tente aproximar mais a câmera.")

# --- PASSO 2: CÓDIGO DE BARRAS (RASTREIO) ---
if st.session_state.ia_status:
    st.divider()
    st.subheader("2. Escanear Código do Pacote")
    foto_bar = st.camera_input("Tire foto do código de barras", key="cam2")

    if foto_bar:
        img_b = Image.open(foto_bar)
        barcodes = decode(img_b)
        
        if barcodes:
            rastreio = barcodes[0].data.decode('utf-8').strip()
            st.info(f"📦 Rastreio: {rastreio}")
            
            if st.button("FINALIZAR E ENVIAR PARA PLANILHA"):
                # Criamos o pacote de dados forçando o formato texto
                dados = {
                    "rastreio": str(rastreio),
                    "classes": str(st.session_state.ia_status),
                    "origem": "App_Producao"
                }
                
                with st.spinner('Enviando...'):
                    try:
                        # Enviamos como JSON para o Google
                        res = requests.post(URL_GOOGLE, json=dados, timeout=20)
                        
                        if res.status_code in [200, 302]:
                            st.balloons()
                            st.success(f"✅ Enviado: {st.session_state.ia_status}")
                            time.sleep(2)
                            st.session_state.ia_status = None
                            st.rerun()
                        else:
                            st.error(f"Erro no Google: Status {res.status_code}")
                    except Exception as e:
                        st.error(f"Falha de conexão: {e}")
