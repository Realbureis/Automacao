import streamlit as st
import requests
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from PIL import Image
import io

# 1. CONFIGURAÇÕES E LINKS
# Certifique-se de que esta URL é a da "Nova Versão" do seu Google Script
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Checkout Jumbo CDP", layout="centered")

@st.cache_resource
def load_model():
    # Carrega o seu modelo treinado do Roboflow
    return YOLO('best.pt')

model = load_model()

# Inicializa o estado da sessão para não perder os dados entre as fotos
if "labels_detectados" not in st.session_state:
    st.session_state.labels_detectados = None

st.title("🚀 Sistema de Check-out Jumbo")

# --- PASSO 1: FOTO DA FOLHA DE PEDIDO ---
st.header("1. Escanear Folha de Pedido")
foto_folha = st.camera_input("Tire foto da folha", key="cam_folha")

if foto_folha:
    img_folha = Image.open(foto_folha)
    # Executa a IA do Roboflow
    results = model(img_folha)
    
    # Extrai os nomes das classes (ex: N. Pedido, Nome Comprador, Unidade)
    labels = [model.names[int(box.cls[0])] for box in results[0].boxes]
    
    if labels:
        st.session_state.labels_detectados = ", ".join(set(labels))
        st.success(f"✅ Campos Identificados: {st.session_state.labels_detectados}")
    else:
        st.session_state.labels_detectados = "Nenhum campo detectado"
        st.warning("⚠️ A IA não reconheceu os campos da folha.")

# --- PASSO 2: CÓDIGO DE BARRAS (SÓ APARECE SE O PASSO 1 FOR FEITO) ---
if st.session_state.labels_detectados:
    st.divider()
    st.header("2. Escanear Código de Barras")
    foto_barcode = st.camera_input("Tire foto do código de barras", key="cam_barcode")

    if foto_barcode:
        img_bar = Image.open(foto_barcode)
        deteccoes = decode(img_bar)
        
        if deteccoes:
            codigo_lido = deteccoes[0].data.decode('utf-8')
            st.info(f"📦 Código Detectado: {codigo_lido}")
            
            # --- BOTÃO FINAL DE ENVIO ---
            if st.button("CONFIRMAR E ENVIAR PARA PLANILHA"):
                # O segredo para não dar erro na planilha está nestas chaves:
                payload = {
                    "rastreio": codigo_lido,                 # Coluna B
                    "classes": st.session_state.labels_detectados, # Coluna C
                    "origem": "App_Streamlit_V2"             # Coluna D
                }
                
                try:
                    # Envia os dados para a nuvem
                    response = requests.post(URL_GOOGLE, json=payload)
                    
                    if response.status_code == 200:
                        st.balloons()
                        st.success("✅ Dados registrados com sucesso na planilha!")
                        # Limpa os dados para o próximo pedido
                        st.session_state.labels_detectados = None
                    else:
                        st.error(f"Erro no servidor Google: {response.status_code}")
                except Exception as e:
                    st.error(f"Falha na conexão: {e}")
        else:
            st.warning("Aguardando leitura do código de barras...")

# Rodapé ou Botão de Reset
if st.sidebar.button("Reiniciar Processo"):
    st.session_state.labels_detectados = None
    st.rerun()
