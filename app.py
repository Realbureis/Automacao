import streamlit as st
import requests
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from PIL import Image
import easyocr
import numpy as np

# URL DO SEU GOOGLE SCRIPT
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Jumbo OCR Smart", layout="centered")

@st.cache_resource
def load_tools():
    # 1. Carrega a YOLO (Localizador)
    model = YOLO('best.pt')
    # 2. Carrega o EasyOCR (Leitor) forçando CPU
    # Isso evita o erro 'Neither CUDA nor MPS are available'
    reader = easyocr.Reader(['pt'], gpu=False) 
    return model, reader

model, reader = load_tools()

# --- ESTADO DA SESSÃO ---
if "dados" not in st.session_state:
    st.session_state.dados = {"comprador": "", "telefone": "", "rastreio": ""}

st.title("📦 Scanner Inteligente Jumbo")

# --- FLUXO DE CAPTURA ---
foto = st.camera_input("Tire foto da folha de pedido")

if foto:
    img = Image.open(foto)
    img_np = np.array(img)
    
    # YOLO detecta onde estão os campos
    with st.spinner('IA localizando campos...'):
        results = model.predict(img, conf=0.25)
    
    # Processa cada caixa detectada
    for box in results[0].boxes:
        c = box.xyxy[0].tolist()
        classe_nome = model.names[int(box.cls[0])].lower()
        
        # Margem de segurança (padding) para não cortar as letras
        pad = 10
        x1, y1, x2, y2 = int(c[0])-pad, int(c[1])-pad, int(c[2])+pad, int(c[3])+pad
        crop = img_np[max(0, y1):min(img_np.shape[0], y2), max(0, x1):min(img_np.shape[1], x2)]
        
        if crop.size > 0:
            # OCR lê o texto dentro da caixa
            with st.spinner(f'Lendo texto em {classe_nome}...'):
                result_ocr = reader.readtext(crop, detail=0)
                texto_extraido = " ".join(result_ocr).strip()
            
            # Preenche o formulário (Verifique se os nomes das classes no Roboflow batem aqui)
            if "comprador" in classe_nome:
                st.session_state.dados["comprador"] = texto_extraido
            elif "telefone" in classe_nome:
                st.session_state.dados["telefone"] = texto_extraido

# --- FORMULÁRIO DE CONFERÊNCIA ---
st.divider()
nome_val = st.text_input("Nome do Comprador extraído:", value=st.session_state.dados["comprador"])
tel_val = st.text_input("Telefone extraído:", value=st.session_state.dados["telefone"])

# --- RASTREIO ---
foto_bar = st.camera_input("Escanear Rastreio", key="barcode")
if foto_bar:
    img_b = Image.open(foto_bar)
    d = decode(img_b)
    if d:
        st.session_state.dados["rastreio"] = d[0].data.decode('utf-8')
        st.success(f"Rastreio: {st.session_state.dados['rastreio']}")

# --- ENVIO FINAL ---
if st.button("ENVIAR PARA PLANILHA", use_container_width=True):
    payload = {
        "rastreio": st.session_state.dados["rastreio"],
        "classes": f"Comprador: {nome_val} | Tel: {tel_val}",
        "origem": "EasyOCR_Producao"
    }
    try:
        res = requests.post(URL_GOOGLE, json=payload, timeout=20)
        st.balloons()
        st.success("Dados enviados com sucesso!")
        # Limpa para o próximo
        st.session_state.dados = {"comprador": "", "telefone": "", "rastreio": ""}
        st.rerun()
    except:
        st.error("Erro ao enviar.")
