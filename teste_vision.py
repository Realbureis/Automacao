import streamlit as st
import requests
import base64
import io
from PIL import Image, ImageEnhance, ImageOps

# Configuração da Página
st.set_page_config(page_title="Jumbo Vision - Mobile Fix", layout="centered")

# Busca a chave nos Secrets
if "vision_api_key" in st.secrets:
    API_KEY = st.secrets["vision_api_key"]
else:
    st.error("Erro: Adicione 'vision_api_key' nos Secrets do Streamlit!")
    st.stop()

URL_VISION = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"

st.title("🧪 Teste de Câmera Jumbo")
st.write("Se a câmera não abrir, verifique as permissões do navegador.")

# PASSO 1: CAPTURA
# O camera_input é o que melhor funciona para "abrir a câmera" direto no Streamlit
foto_bruta = st.camera_input("Tire a foto da folha")

if foto_bruta:
    with st.spinner('Processando imagem em alta qualidade...'):
        try:
            # 1. Abre a imagem
            img = Image.open(foto_bruta)
            
            # 2. Corrige a orientação (iPhone costuma girar a foto)
            img = ImageOps.exif_transpose(img)
            
            # 3. TRATAMENTO PARA OCR:
            # Aumentamos o contraste e a nitidez para compensar os "poucos pixels"
            img = ImageEnhance.Contrast(img).enhance(2.0)
            img = ImageEnhance.Sharpness(img).enhance(2.0)
            
            # 4. Converte para Bytes sem compressão agressiva
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=100)
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

            if 'responses' in res_json and res_json[0]:
                texto_lido = res_json['responses'][0]['textAnnotations'][0]['description']
                st.success("✅ Leitura realizada!")
                st.image(img, caption="Imagem processada (Contraste + Nitidez)", use_container_width=True)
                st.text_area("Texto extraído:", value=texto_lido, height=300)
            else:
                st.warning("IA não detectou texto. Tente focar melhor ou limpar a lente.")

        except Exception as e:
            st.error(f"Erro: {e}")
