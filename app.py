import streamlit as st
import requests
from pyzbar.pyzbar import decode
from PIL import Image

# URL do seu Google Script
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.title("Scanner Logístico Jumbo CDP")

# Slot para a segunda imagem (Código de Barras)
img_file = st.camera_input("Escaneie o Código de Barras")

if img_file:
    # Processar a imagem
    image = Image.open(img_file)
    barcodes = decode(image)
    
    if barcodes:
        codigo_lido = barcodes[0].data.decode('utf-8')
        st.success(f"Código detectado: {codigo_lido}")
        
        # Botão para enviar para a planilha
        if st.button("Enviar para Planilha"):
            payload = {"codigo": codigo_lido, "timestamp": "now"}
            
            try:
                # Envia o dado para o seu Google Apps Script
                response = requests.post(WEBAPP_URL, json=payload)
                
                if response.status_code == 200:
                    st.balloons()
                    st.success("Dados enviados com sucesso para a nuvem!")
                else:
                    st.error(f"Erro no servidor: {response.status_code}")
            except Exception as e:
                st.error(f"Erro de conexão: {e}")
    else:
        st.warning("Nenhum código de barras encontrado. Tente alinhar melhor a imagem.")
