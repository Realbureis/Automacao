import streamlit as st
import requests
from pyzbar.pyzbar import decode
from PIL import Image
import io

# URL do seu Web App no Google Apps Script
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbz1482LFPg1cUWoMiY4tGuyi-csoyaaPiUJwuLz5U-CUQ-0wnDTXBgUilKbWJYs-80G/exec"

st.title("Scanner Logístico Jumbo CDP")

# Inicializa variáveis de estado
if 'dados_folha' not in st.session_state:
    st.session_state.dados_folha = None

# --- PASSO 1: LEITURA DA FOLHA DE PEDIDO ---
st.header("1. Documento de Pedido")
foto_folha = st.camera_input("Tire foto da Folha de Pedido", key="camera_folha")

if foto_folha:
    # Aqui você pode adicionar lógica de OCR se precisar extrair texto da folha
    # Por enquanto, vamos confirmar que a imagem foi capturada
    st.session_state.dados_folha = "Capturada"
    st.success("✅ Folha registrada!")

# --- PASSO 2: LEITURA DO CÓDIGO DE BARRAS (SÓ APARECE APÓS O PASSO 1) ---
if st.session_state.dados_folha:
    st.divider()
    st.header("2. Código de Barras")
    foto_barcode = st.camera_input("Escaneie o Código de Barras do Pacote", key="camera_barcode")

    if foto_barcode:
        img_barcode = Image.open(foto_barcode)
        resultados = decode(img_barcode)
        
        if resultados:
            codigo_lido = resultados[0].data.decode('utf-8')
            st.info(f"Conteúdo: {codigo_lido}")
            
            # Botão Final para enviar tudo para a nuvem
            if st.button("Confirmar e Enviar para Nuvem"):
                payload = {
                    "codigo_barras": codigo_lido,
                    "status_folha": "OK",
                    "origem": "Streamlit_App"
                }
                
                try:
                    response = requests.post(WEBAPP_URL, json=payload)
                    if response.status_code == 200:
                        st.balloons()
                        st.success("Dados enviados com sucesso!")
                        # Limpa o estado para o próximo pedido
                        st.session_state.dados_folha = None
                    else:
                        st.error("Erro ao enviar.")
                except Exception as e:
                    st.error(f"Conexão falhou: {e}")
        else:
            st.warning("Código de barras não detectado na imagem. Tente novamente.")

# Botão para resetar o processo se necessário
if st.sidebar.button("Resetar Scanner"):
    st.session_state.dados_folha = None
    st.rerun()
