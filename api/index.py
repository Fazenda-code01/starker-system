import json
import requests
import re
import os
from http.server import BaseHTTPRequestHandler

# 🔐 CHAVE SEGURA
API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = """Você é o CHATSTARKER. Unidade de Qualificação de Elite da STARKER.
Sua função é filtrar empresários e proteger a agenda.
TRIAGEM OBRIGATÓRIA: Nicho, Tempo de operação e Faturamento mensal."""

def is_low_revenue(message):
    # Remove pontos e vírgulas para validar o número puro
    match = re.search(r'(\d+)', message.replace('.', '').replace(',', ''))
    if match:
        value = int(match.group(1))
        if value < 50000:
            return True
    return False

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        body = json.loads(post_data)
        user_message = body.get("message", "")

        # 🚫 BLOQUEIO DE FATURAMENTO
        if is_low_revenue(user_message):
            reply = "O modelo STARKER é para escala. Foque em validação antes de avançar."
        else:
            # 🚀 CHAMADA PARA O GEMINI
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            payload = {"contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\nUsuário: " + user_message}]}]}
            
            response = requests.post(url, json=payload)
            result = response.json()
            # Garante que a resposta existe antes de entregar
            try:
                reply = result["candidates"][0]["content"]["parts"][0]["text"]
            except:
                reply = "Erro na matriz de inteligência. Verifique a chave API."

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"reply": reply}).encode())
        return
