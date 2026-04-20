import streamlit as st
import requests
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from PIL import Image
import time

# URL do seu Google Script
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Checkout Inteligente Jumbo", layout="centered")

@st.cache_resource
def load_model():
    return YOLO('best.pt')

model = load_model()

# Inicializa as variáveis no estado da sessão para os campos do formulário
if "form_dados" not in st.session_state:
    st.session_state.form_dados = {"pedido": "", "detento": "", "unidade": "", "rastreio": ""}

st.title("🚀 Checkout com Autopreenchimento")
st.write("A IA detecta os campos e preenche o formulário abaixo.")

# --- PASSO 1: FOTO E DETECÇÃO ---
st.subheader("1. Escanear Folha de Pedido")
foto_folha = st.camera_input("Tire foto da folha", key="cam_ia")

if foto_folha:
    img_f = Image.open(foto_folha)
    results = model.predict(img_f, conf=0.25)
    
    # Preview visual (as caixas coloridas que você pediu)
    res_plotted = results[0].plot()
    img_preview = Image.fromarray(res_plotted[:, :, ::-1])
    st.image(img_preview, caption="Preview da Detecção", use_column_width=True)
    
    # Lógica de preenchimento dos campos baseada nas classes detectadas
    detectados = [model.names[int(box.cls[0])] for box in results[0].boxes]
    
    # Atualiza o formulário se encontrar as classes específicas
    # Exemplo: se a IA ler a classe 'N. Pedido', marcamos como 'Detectado' no campo
    if detectados:
        if "N. Pedido" in detectados: st.session_state.form_dados["pedido"] = "✅ Detectado"
        if "Nome Detento" in detectados: st.session_state.form_dados["detento"] = "✅ Detectado"
        if "Unidade Prisional" in detectados: st.session_state.form_dados["unidade"] = "✅ Detectado"
        st.success("Campos identificados e preenchidos abaixo!")
    else:
        st.error("Nenhum campo reconhecido pela IA.")

# --- PASSO 2: FORMULÁRIO DE CONFERÊNCIA ---
st.divider()
st.subheader("2. Conferência de Dados")

# Os campos abaixo são preenchidos pela IA, mas você pode editar
campo_pedido = st.text_input("Número do Pedido", value=st.session_state.form_dados["pedido"])
campo_detento = st.text_input("Nome do Detento", value=st.session_state.form_dados["detento"])
campo_unidade = st.text_input("Unidade Prisional", value=st.session_state.form_dados["unidade"])

# --- PASSO 3: CÓDIGO DE BARRAS ---
st.subheader("3. Escanear Rastreio")
foto_bar = st.camera_input("Capture o código do pacote", key="cam_bar")

if foto_bar:
    img_b = Image.open(foto_bar)
    barcodes = decode(img_b)
    if barcodes:
        st.session_state.form_dados["rastreio"] = barcodes[0].data.decode('utf-8').strip()
        st.info(f"📦 Código: {st.session_state.form_dados['rastreio']}")

# --- BOTÃO FINAL ---
if st.button("CONFIRMAR E ENVIAR TUDO", use_container_width=True):
    # Montamos o texto final combinando o que foi editado no formulário
    info_ia = f"Pedido: {campo_pedido} | Detento: {campo_detento} | Unidade: {campo_unidade}"
    
    payload = {
        "rastreio": st.session_state.form_dados["rastreio"],
        "classes": info_ia,
        "origem": "App_Smart_Form"
    }
    
    try:
        res = requests.post(URL_GOOGLE, json=payload, timeout=20)
        if res.status_code in [200, 302]:
            st.balloons()
            st.success("Dados enviados para a planilha!")
            # Limpa o formulário para o próximo
            st.session_state.form_dados = {"pedido": "", "detento": "", "unidade": "", "rastreio": ""}
            time.sleep(2)
            st.rerun()
    except:
        st.error("Erro ao enviar. Verifique sua conexão.")
