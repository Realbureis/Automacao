import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageOps
import base64
import requests

# ... (suas configurações de API e YOLO permanecem iguais) ...

if foto_bruta:
    # 1. Carregar imagem garantindo a resolução máxima enviada pelo navegador
    file_bytes = np.asarray(bytearray(foto_bruta.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # 2. YOLO localiza os campos
    results = model.predict(img, conf=0.25)
    
    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        classe = model.names[int(box.cls[0])]
        
        # RECORTE com margem generosa
        pad = 20
        crop = img[max(0, y1-pad):min(img.shape[0], y2+pad), 
                   max(0, x1-pad):min(img.shape[1], x2+pad)]
        
        if crop.size > 0:
            # --- TRATAMENTO PARA SALVAR OS PIXELS ---
            
            # A. Aumentar a imagem em 2x (Interpolação Cúbica)
            # Isso "estica" os pixels de forma inteligente antes do OCR
            crop = cv2.resize(crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            
            # B. Converter para Escala de Cinza e aumentar o contraste
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            final_crop = clahe.apply(gray)
            
            # C. Enviar para o Google Vision em formato sem perda (PNG)
            _, buffer = cv2.imencode('.png', final_crop) 
            img_b64 = base64.b64encode(buffer).decode("utf-8")
            
            # ... (Restante do envio para a API Vision) ...
