import streamlit as st
import requests
from ultralytics import YOLO
from pyzbar.pyzbar import decode
from PIL import Image
import os
import time

# 1. CONFIGURAÇÃO DO ENDPOINT GOOGLE (ATUALIZADO)
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.set_page_config(page_title="Checkout Jumbo v3", layout="centered")

@st.cache_resource
def load_model():
    model_path = 'best.pt'
    # Verifica se o arquivo existe e se não está corrompido (mínimo 1MB)
    if os.path.exists(model_path) and os.path.getsize(model_path) > 1000000:
        try:
            return YOLO(model_path)
        except Exception as e:
            st.error(f"Erro ao carregar neurônios da IA: {e}")
            return None
    return None

model = load_model()

# Controle de estado para o fluxo de duas fotos
if "ia_processada" not in st.session_state:
    st.session_state.ia_processada = None

st.title("🚀 Sistema de Checkout Jumbo")
st.info("Fluxo: 1º Folha de Pedido -> 2º Código de Barras")

# Trava visual caso o modelo ainda esteja subindo para o servidor
if model is None:
    st.warning("⏳ O servidor está processando o modelo 'best.pt'. Aguarde 15 segundos e atualize a página.")
    st.stop()

# --- PASSO 1: IA ROBOFLOW (FOLHA DE PEDIDO) ---
st.subheader("1. Escanear Folha de Pedido")
foto_folha = st.camera_input("Capture a folha", key="scan_folha")

if foto_folha:
    img_f = Image.open(foto_folha)
    results = model(img_f)
    
    # Mapeia as classes treinadas (N. Pedido, Nome Detento, etc.)
    labels = [model.names[int(box.cls[0])] for box in results[0].boxes]
    
    if labels:
        st.session_state.ia_processada = ", ".join(set(labels))
        st.success(f"✅ Campos Detectados: {st.session_state.ia_processada}")
    else:
        st.session_state.ia_processada = "Nenhum campo detectado"
        st.warning("⚠️ A IA não reconheceu os campos da folha.")

# --- PASSO 2: CÓDIGO DE BARRAS (PACOTE) ---
if st.session_state.ia_processada:
    st.divider()
    st.subheader("2. Escanear Código do Pacote")
    foto_bar = st.camera_input("Capture o código de barras", key="scan_barcode")

    if foto_bar:
        img_b = Image.open(foto_bar)
        barcodes = decode(img_b)
        
        if barcodes:
            codigo_limpo = barcodes[0].data.decode('utf-8').strip()
            st.info(f"📦 Código Lido: {codigo_limpo}")
            
            # --- ENVIO FINAL PARA A PLANILHA ---
            if st.button("CONFIRMAR E ENVIAR DADOS"):
                payload = {
                    "rastreio": str(codigo_limpo),
                    "classes": str(st.session_state.ia_processada),
                    "origem": "Sistema_Producao_Jumbo"
                }
                
                # Headers necessários para comunicação WebApp Google
                headers = {"Content-Type": "application/json"}
                
                with st.spinner('Gravando na nuvem...'):
                    try:
                        # Timeout estendido para redes de galpão
                        res = requests.post(
                            URL_GOOGLE, 
                            json=payload, 
                            headers=headers,
                            timeout=30,
                            allow_redirects=True
                        )
                        
                        # O Google Apps Script pode retornar 200 (OK) ou 302 (Redirecionamento)
                        if res.status_code in [200, 201, 302]:
                            st.balloons()
                            st.success("✅ Sucesso! Pedido arquivado na planilha.")
                            time.sleep(2)
                            # Reseta para o próximo operador
                            st.session_state.ia_processada = None
                            st.rerun()
                        else:
                            st.error(f"Erro no Google Script: Status {res.status_code}")
                            st.info("Verifique se o script está publicado como 'Anyone'.")
                    except Exception as e:
                        st.error(f"Erro de Conexão: {e}")
        else:
            st.warning("Centralize o código de barras na câmera.")

# Botão de Reset na Sidebar
if st.sidebar.button("Limpar e Reiniciar"):
    st.session_state.ia_processada = None
    st.rerun()
