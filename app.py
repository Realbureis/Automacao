import streamlit as st
import requests
import base64
import json
from PIL import Image
from pyzbar.pyzbar import decode

# 1. PEGA A CHAVE COM SEGURANÇA DOS SECRETS
if "vision_api_key" in st.secrets:
    API_KEY = st.secrets["vision_api_key"]
else:
    st.error("Configure a 'vision_api_key' nos Secrets do Streamlit!")
    st.stop()

URL_VISION = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
URL_GOOGLE_SHEETS = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Checkout Jumbo Vision", layout="centered")

if "temp_texto" not in st.session_state:
    st.session_state.temp_texto = ""

st.title("📦 Jumbo Smart Checkout")
st.write("Leitura automática de Nome e Telefone via Google Vision")

# --- PASSO 1: FOTO DA FOLHA ---
st.subheader("1. Foto da Folha de Pedido")
foto_folha = st.camera_input("Capture a folha", key="cam_folha")

if foto_folha:
    img_b64 = base64.b64encode(foto_folha.getvalue()).decode("utf-8")
    
    payload = {
        "requests": [{
            "image": {"content": img_b64},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }

    with st.spinner('IA lendo dados...'):
        response = requests.post(URL_VISION, json=payload)
        res_json = response.json()
        
        try:
            # Extrai todo o bloco de texto lido
            st.session_state.temp_texto = res_json['responses'][0]['textAnnotations'][0]['description']
            st.success("Dados lidos com sucesso!")
        except:
            st.error("Erro na leitura. Verifique se a API Vision está ATIVA no seu console Google.")

# --- PASSO 2: CONFERÊNCIA ---
if st.session_state.temp_texto:
    st.divider()
    st.subheader("2. Conferência de Dados")
    # O texto lido aparece aqui para você conferir ou editar
    texto_final = st.text_area("Dados extraídos:", value=st.session_state.temp_texto, height=200)

    # --- PASSO 3: RASTREIO ---
    st.subheader("3. Código de Rastreio")
    foto_bar = st.camera_input("Escanear o pacote", key="cam_bar")
    
    if foto_bar:
        img_b = Image.open(foto_bar)
        barcodes = decode(img_b)
        
        if barcodes:
            rastreio = barcodes[0].data.decode('utf-8').strip()
            st.info(f"📦 Rastreio: {rastreio}")
            
            if st.button("CONFIRMAR E ENVIAR PARA PLANILHA", use_container_width=True):
                dados_envio = {
                    "rastreio": str(rastreio),
                    "classes": texto_final,
                    "origem": "Vision_API_Key_Victor"
                }
                
                try:
                    requests.post(URL_GOOGLE_SHEETS, json=dados_envio, timeout=20)
                    st.balloons()
                    st.success("✅ Enviado para a nuvem!")
                    st.session_state.temp_texto = ""
                    st.rerun()
                except:
                    st.error("Erro ao falar com a planilha.")
