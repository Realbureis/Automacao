import streamlit as st
import requests
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from PIL import Image

# Substitua pela sua URL de implantação do Google Script
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

@st.cache_resource
def load_model():
    # Carrega o modelo que contém as classes: N. Pedido, Nome Comprador, etc.
    return YOLO('best.pt')

model = load_model()

st.title("🚀 Checkout Logístico Jumbo")

# --- ETAPA 1: CAPTURA DA FOLHA (ROBOFLOW) ---
st.header("1. Documento de Pedido")
foto_folha = st.camera_input("Tire foto da folha", key="cam_folha")

if "labels_ia" not in st.session_state:
    st.session_state.labels_ia = None

if foto_folha:
    img_folha = Image.open(foto_folha)
    results = model(img_folha)
    
    # Extrai exatamente os nomes que você definiu no Roboflow
    labels = [model.names[int(box.cls[0])] for box in results[0].boxes]
    
    if labels:
        st.session_state.labels_ia = ", ".join(set(labels))
        st.success(f"✅ IA identificou: {st.session_state.labels_ia}")
    else:
        st.session_state.labels_ia = "Nenhum campo detectado"
        st.warning("⚠️ A IA não reconheceu as marcações nesta foto.")

# --- ETAPA 2: CAPTURA DO CÓDIGO DE BARRAS ---
if st.session_state.labels_ia:
    st.divider()
    st.header("2. Código de Barras")
    foto_bar = st.camera_input("Escanear código do pacote", key="cam_bar")

    if foto_bar:
        img_bar = Image.open(foto_bar)
        deteccoes = decode(img_bar)
        
        if deteccoes:
            codigo_texto = deteccoes[0].data.decode('utf-8')
            st.info(f"📦 Código: {codigo_texto}")
            
            # BOTÃO DE ENVIO - Ajustado para bater com o Google Script
            if st.button("SALVAR NA PLANILHA"):
                payload = {
                    "rastreio": codigo_texto,          # Vai para a Coluna B
                    "classes": st.session_state.labels_ia, # Vai para a Coluna C
                    "origem": "App_Mobile_Jumbo"       # Vai para a Coluna D
                }
                
                try:
                    res = requests.post(URL_GOOGLE, json=payload)
                    if res.status_code == 200:
                        st.balloons()
                        st.success("Dados registrados com sucesso!")
                        # Limpa para o próximo processo
                        st.session_state.labels_ia = None
                    else:
                        st.error(f"Erro no servidor: {res.status_code}")
                except Exception as e:
                    st.error(f"Falha de conexão: {e}")
        else:
            st.warning("Aguardando leitura do código de barras...")
