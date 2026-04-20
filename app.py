import streamlit as st
from ultralytics import YOLO
from PIL import Image, ImageOps
from pyzbar.pyzbar import decode
import requests

# Configuração de interface para Mobile
st.set_page_config(page_title="Jumbo CDP Scanner", layout="centered")

# Estilo para remover menus desnecessários do Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 1. Carregamento do Modelo com Cache
@st.cache_resource
def load_model():
    return YOLO('best.pt')

model = load_model()

# 2. URL DO GOOGLE (Substitua pela sua URL entre as aspas)
URL_GOOGLE_SHEETS = "SUA_URL_DO_GOOGLE_AQUI"

st.title("📦 Scanner Industrial Jumbo")
st.write("Aponte para o pedido e aguarde a leitura automática.")

# Componente de Câmera (Nativo do Streamlit)
foto = st.camera_input("Scanner de Pedidos")

# Trava de segurança para espelhamento
inverter = st.checkbox("A imagem está invertida? (Inverter)", value=False)

if foto:
    img = Image.open(foto)
    
    # Se o operador marcar, o Python desvira o pixel
    if inverter:
        img = ImageOps.mirror(img)
    
    with st.spinner('Validando pedido com IA...'):
        # --- Lógica de Leitura ---
        barcodes = decode(img)
        rastreio = barcodes[0].data.decode('utf-8') if barcodes else "Não detectado"
        
        # --- Detecção YOLO ---
        results = model(img)
        res_img = results[0].plot()
        
        # --- Envio para Planilha ---
        if rastreio != "Não detectado" and "http" in URL_GOOGLE_SHEETS:
            try:
                payload = {
                    "rastreio": rastreio, 
                    "campos": "Conferido", 
                    "origem": "Streamlit Mobile"
                }
                requests.post(URL_GOOGLE_SHEETS, json=payload, timeout=5)
                st.success(f"✅ Pedido {rastreio} enviado!")
            except:
                st.warning("⚠️ Lido, mas erro ao enviar para o Google.")
        else:
            st.error("❌ Código de barras não detectado.")

        # Exibição do Resultado
        st.image(res_img, caption="Processamento da IA")

st.caption("Jumbo CDP v1.0 - Estratégia e Logística")
