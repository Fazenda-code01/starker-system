import json
import requests
import re
import os

SYSTEM_PROMPT = """Você é o CHATSTARKER. Unidade de Qualificação de Elite da STARKER.
Sua função é filtrar empresários e proteger a agenda.
TRIAGEM OBRIGATÓRIA: Nicho, Tempo de operação e Faturamento mensal."""

API_KEY = os.getenv("GEMINI_API_KEY")

def is_low_revenue(message):
    match = re.search(r'(\d+)', message.replace('.', '').replace(',', ''))
    if match:
        value = int(match.group(1))
        if value < 50000:
            return True
    return False

def handler(request):
    if request.method == "OPTIONS":
        from http import HTTPStatus
        return Response("", status=204, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })

    body = request.json()
    user_message = body.get("message", "")

    if is_low_revenue(user_message):
        reply = "O modelo STARKER é para escala. Foque em validação antes de avançar."
    else:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\nUsuário: " + user_message}]}
            ]
        }
        response = requests.post(url, json=payload)
        result = response.json()
        try:
            reply = result["candidates"][0]["content"]["parts"][0]["text"]
        except:
            reply = "Erro na matriz. Verifique a chave API no Vercel."

    return Response(
        json.dumps({"reply": reply}),
        status=200,
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }
    )
