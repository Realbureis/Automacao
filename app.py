import streamlit as st
import requests
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from PIL import Image
import easyocr
import numpy as np

# Configuração da URL do Google
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Jumbo OCR Smart", layout="centered")

# Carrega a IA de localização e o leitor de texto (OCR)
@st.cache_resource
def load_tools():
    model = YOLO('best.pt')
    reader = easyocr.Reader(['pt']) # Define o idioma para Português
    return model, reader

model, reader = load_tools()

if "dados" not in st.session_state:
    st.session_state.dados = {"comprador": "", "telefone": "", "rastreio": ""}

st.title("📦 Checkout Inteligente Jumbo CDP")

# --- PASSO 1: FOTO E LEITURA AUTOMÁTICA ---
foto = st.camera_input("Tire foto do pedido")

if foto:
    img = Image.open(foto)
    img_array = np.array(img)
    
    # 1. Localiza os campos com YOLO
    results = model.predict(img, conf=0.25)
    
    # 2. Varre as caixas detectadas
    for box in results[0].boxes:
        coords = box.xyxy[0].tolist() # Pega as coordenadas [x1, y1, x2, y2]
        classe = model.names[int(box.cls[0])] # Pega o nome da classe
        
        # Recorta a imagem na área da caixa
        crop = img_array[int(coords[1]):int(coords[3]), int(coords[0]):int(coords[2])]
        
        # 3. Faz o OCR (Lê o texto dentro do recorte)
        resultado_ocr = reader.readtext(crop, detail=0)
        texto_lido = " ".join(resultado_ocr)
        
        # 4. Preenche os campos baseados na classe (Ajuste os nomes se forem diferentes)
        if "Nome Comprador" in classe:
            st.session_state.dados["comprador"] = texto_lido
        elif "Telefone" in classe:
            st.session_state.dados["telefone"] = texto_lido

# --- PASSO 2: FORMULÁRIO (O texto lido aparece aqui) ---
st.subheader("Conferência Automática")
nome_final = st.text_input("Nome do Comprador", value=st.session_state.dados["comprador"])
tel_final = st.text_input("Telefone", value=st.session_state.dados["telefone"])

# --- PASSO 3: CÓDIGO DE BARRAS ---
st.divider()
foto_bar = st.camera_input("Escanear Rastreio", key="barcode")
if foto_bar:
    img_b = Image.open(foto_bar)
    deteccao = decode(img_b)
    if deteccao:
        st.session_state.dados["rastreio"] = deteccao[0].data.decode('utf-8')
        st.success(f"Rastreio Lido: {st.session_state.dados['rastreio']}")

# --- ENVIO ---
if st.button("CONFIRMAR E ENVIAR"):
    payload = {
        "rastreio": st.session_state.dados["rastreio"],
        "classes": f"Comprador: {nome_final} | Tel: {tel_final}",
        "origem": "OCR_Automacao"
    }
    res = requests.post(URL_GOOGLE, json=payload)
    if res.status_code == 200:
        st.balloons()
        st.success("Dados enviados!")
        st.session_state.dados = {"comprador": "", "telefone": "", "rastreio": ""}
        st.rerun()
