import streamlit as st
import requests
import base64
import io
from PIL import Image, ImageEnhance

# Configuração da Página
st.set_page_config(page_title="Jumbo Vision - Teste de Alta Resolução", layout="centered")

# Busca a chave nos Secrets
if "vision_api_key" in st.secrets:
    API_KEY = st.secrets["vision_api_key"]
else:
    st.error("Erro: Adicione 'vision_api_key' nos Secrets do Streamlit!")
    st.stop()

URL_VISION = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"

st.title("🧪 Laboratório OCR Jumbo")
st.write("Versão de Alta Qualidade para Captura de Nomes e Telefones")

# PASSO 1: CAPTURA (Usando File Uploader para garantir nitidez)
st.subheader("1. Capturar Imagem")
# No iPhone, este botão permite "Tirar Foto" com a câmara oficial
foto_bruta = st.file_uploader("Clique para tirar foto ou carregar imagem", type=['jpg', 'jpeg', 'png'])

if foto_bruta:
    with st.spinner('A otimizar imagem e a ler dados...'):
        try:
            # --- TRATAMENTO DA IMAGEM PARA MELHORAR O OCR ---
            img = Image.open(foto_bruta)
            
            # 1. Ajuste de Contraste (ajuda a separar o texto do fundo)
            enhancer = ImageEnhance.Contrast(img)
            img_editada = enhancer.enhance(1.8)
            
            # 2. Converte para Bytes em Alta Qualidade (JPEG 100)
            buffer = io.BytesIO()
            img_editada.save(buffer, format="JPEG", quality=100)
            img_bytes = buffer.getvalue()
            
            # --- ENVIO PARA O GOOGLE VISION ---
            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
            
            payload = {
                "requests": [{
                    "image": {"content": img_base64},
                    "features": [{"type": "TEXT_DETECTION"}]
                }]
            }

            response = requests.post(URL_VISION, json=payload)
            res_json = response.json()

            # --- EXTRAÇÃO E EXIBIÇÃO ---
            if 'responses' in res_json and res_json['responses'][0]:
                texto_lido = res_json['responses'][0]['textAnnotations'][0]['description']
                
                st.success("✅ Leitura realizada com sucesso!")
                
                # Preview da imagem que foi enviada (para veres se está nítida)
                st.image(img_editada, caption="Imagem processada pela IA", use_container_width=True)
                
                st.subheader("Dados Identificados:")
                resultado = st.text_area("Podes editar o texto abaixo se necessário:", 
                                       value=texto_lido, 
                                       height=300)
                
                if st.button("Tudo correto? Confirmar Teste"):
                    st.balloons()
                    st.info("Teste validado. Agora podemos levar este fluxo para o app oficial.")
            else:
                st.error("O Google não conseguiu detetar texto. Tenta focar melhor no papel.")
                
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
            st.write("Detalhes do erro do Google:", res_json)

st.divider()
st.caption("Dica: Se a imagem estiver 'lavada', o contraste automático (1.8x) ajudará o Google a ler o telefone corretamente.")
