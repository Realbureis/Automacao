import streamlit as st
import requests
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from PIL import Image
import easyocr
import numpy as np
import cv2

URL_GOOGLE = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Debug OCR Jumbo", layout="centered")

@st.cache_resource
def load_tools():
    # Carrega os modelos uma única vez
    model = YOLO('best.pt')
    reader = easyocr.Reader(['pt']) 
    return model, reader

model, reader = load_tools()

# Estado da sessão para manter os dados entre as fotos
if "form" not in st.session_state:
    st.session_state.form = {"comprador": "", "telefone": "", "rastreio": ""}

st.title("🔍 Debug de Leitura Inteligente")

# 1. CAPTURA DA FOLHA
foto = st.camera_input("Tire foto da folha de pedido")

if foto:
    img = Image.open(foto)
    img_np = np.array(img)
    
    # Rodar predição
    results = model.predict(img, conf=0.20) # Confiança baixa para teste
    
    st.subheader("Processamento da IA:")
    
    for box in results[0].boxes:
        c = box.xyxy[0].tolist()
        # Pega o nome da classe e coloca em minúsculo para evitar erro de digitação
        classe_original = model.names[int(box.cls[0])]
        classe = classe_original.lower().strip()
        
        # Criar um pequeno padding (margem) para ajudar o OCR a ler melhor
        pad = 10
        x1, y1, x2, y2 = int(c[0])-pad, int(c[1])-pad, int(c[2])+pad, int(c[3])+pad
        
        # Garantir que o recorte está dentro da imagem
        crop = img_np[max(0, y1):min(img_np.shape[0], y2), max(0, x1):min(img_np.shape[1], x2)]
        
        if crop.size > 0:
            # MOSTRA O RECORTE NA TELA PARA VOCÊ VER SE ESTÁ CERTO
            st.image(crop, caption=f"O que a IA identificou como: {classe_original}")
            
            # Tentar ler o texto
            resultado = reader.readtext(crop, detail=0)
            texto = " ".join(resultado).strip()
            
            # ATRIBUIÇÃO (Ajuste aqui conforme os nomes no seu Roboflow)
            # Use termos que aparecem no seu dataset
            if "comprador" in classe:
                st.session_state.form["comprador"] = texto
            elif "telefone" in classe:
                st.session_state.form["telefone"] = texto

# 2. FORMULÁRIO DE CONFERÊNCIA
st.divider()
nome_input = st.text_input("Nome lido:", value=st.session_state.form["comprador"])
tel_input = st.text_input("Telefone lido:", value=st.session_state.form["telefone"])

# 3. RASTREIO E ENVIO
foto_bar = st.camera_input("Escanear Código de Barras", key="bar")
if foto_bar:
    img_b = Image.open(foto_bar)
    d = decode(img_b)
    if d:
        st.session_state.form["rastreio"] = d[0].data.decode('utf-8')
        st.success(f"Rastreio: {st.session_state.form['rastreio']}")

if st.button("ENVIAR PARA PLANILHA"):
    payload = {
        "rastreio": st.session_state.form["rastreio"],
        "classes": f"Nome: {nome_input} | Tel: {tel_input}",
        "origem": "Jumbo_OCR_V2"
    }
    try:
        r = requests.post(URL_GOOGLE, json=payload, timeout=15)
        st.balloons()
        st.success("Enviado!")
        st.session_state.form = {"comprador": "", "telefone": "", "rastreio": ""}
        st.rerun()
    except:
        st.error("Erro ao enviar.")
