import streamlit as st
import requests
import base64

# Configuração simples de página
st.set_page_config(page_title="Ambiente de Teste Vision", layout="centered")

# Busca a chave nos Secrets para segurança
if "vision_api_key" in st.secrets:
    API_KEY = st.secrets["vision_api_key"]
else:
    st.error("Erro: Adicione 'vision_api_key' nos Secrets do Streamlit!")
    st.stop()

st.title("🧪 Laboratório de OCR - Jumbo")
st.info("Este é um ambiente de teste isolado para validar o Google Vision.")

# Interface de captura
foto = st.camera_input("Tire uma foto de teste")

if foto:
    # Codificação para o Google
    img_base64 = base64.b64encode(foto.getvalue()).decode("utf-8")
    
    payload = {
        "requests": [{
            "image": {"content": img_base64},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }

    url_vision = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"

    with st.spinner('IA processando...'):
        response = requests.post(url_vision, json=payload)
        res_json = response.json()
        
        try:
            texto = res_json['responses'][0]['textAnnotations'][0]['description']
            st.success("✅ O Google Vision respondeu!")
            st.subheader("Texto detectado:")
            st.text_area("Resultado bruto:", value=texto, height=250)
        except Exception as e:
            st.error(f"❌ Erro na resposta do Google: {res_json}")
            st.write("Verifique se a 'Cloud Vision API' está ativada no seu console do Google Cloud.")
