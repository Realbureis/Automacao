import streamlit as st
import requests
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from PIL import Image

# 1. CONFIGURAÇÕES
# Use a sua URL de implantação do Google (sempre a "Nova Versão")
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Checkout Jumbo CDP", layout="centered")

@st.cache_resource
def load_model():
    # Carrega o modelo com suas classes (N. Pedido, Nome Comprador, etc)
    return YOLO('best.pt')

model = load_model()

# Inicializa o estado para não perder a informação entre as fotos
if "dados_ia" not in st.session_state:
    st.session_state.dados_ia = None

st.title("🚀 Sistema de Checkout Jumbo")
st.write("Conferência automática via IA e Rastreio.")

# --- PASSO 1: IA (ROBOFLOW) ---
st.subheader("1. Escanear Folha de Pedido")
foto_folha = st.camera_input("Tire foto da folha", key="cam1")

if foto_folha:
    img_f = Image.open(foto_folha)
    results = model(img_f)
    
    # Extrai os nomes das classes que você treinou
    labels = [model.names[int(box.cls[0])] for box in results[0].boxes]
    
    if labels:
        st.session_state.dados_ia = ", ".join(set(labels))
        st.success(f"✅ IA Detectou: {st.session_state.dados_ia}")
    else:
        st.session_state.dados_ia = "Nenhum campo detectado"
        st.warning("⚠️ A IA não reconheceu os campos. Tente focar melhor.")

# --- PASSO 2: CÓDIGO DE BARRAS ---
if st.session_state.dados_ia:
    st.divider()
    st.subheader("2. Escanear Código de Barras")
    foto_b = st.camera_input("Tire foto do código do pacote", key="cam2")

    if foto_b:
        img_b = Image.open(foto_b)
        barcodes = decode(img_b)
        
        if barcodes:
            rastreio_lido = barcodes[0].data.decode('utf-8').strip()
            st.info(f"📦 Código: {rastreio_lido}")
            
            # --- ENVIO FINAL ---
            # Removido 'variant' para evitar o TypeError do seu print
            if st.button("CONFIRMAR E ENVIAR PARA NUVEM"):
                payload = {
                    "rastreio": str(rastreio_lido),      # Coluna B
                    "classes": str(st.session_state.dados_ia), # Coluna C
                    "origem": "Jumbo_Mobile_Final"       # Coluna D
                }
                
                try:
                    res = requests.post(URL_GOOGLE, json=payload, timeout=10)
                    if res.status_code == 200:
                        st.balloons()
                        st.success("✅ Pedido arquivado com sucesso!")
                        # Limpa o estado e reinicia para o próximo pedido
                        st.session_state.dados_ia = None
                        st.rerun()
                    else:
                        st.error(f"Erro no servidor Google: {res.status_code}")
                except Exception as e:
                    st.error(f"Erro de conexão: {e}")
        else:
            st.warning("Aguardando leitura do código de barras...")

# Barra lateral para resetar se algo der errado
if st.sidebar.button("Reiniciar Processo"):
    st.session_state.dados_ia = None
    st.rerun()
