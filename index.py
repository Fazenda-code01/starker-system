import json
import requests
import re
import os

# 🔐 CHAVE SEGURA (vem da Vercel depois)
API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = """Você é o CHATSTARKER. Unidade de Qualificação de Elite da STARKER.

Sua função é filtrar empresários e proteger a agenda.

TRIAGEM OBRIGATÓRIA:
- Nicho
- Tempo de operação
- Faturamento mensal

REGRAS:

1. Faturamento < 50.000:
"O modelo STARKER é projetado para escala. No seu estágio atual, foque em validação antes de aplicar engenharia."
Encerrar.

2. Sem empresa real:
"Não trabalhamos com hipóteses. Retorne quando houver operação real."
Encerrar.

3. Aprovado:
Tom frio e direto.

Encaminhar:

"Acesse agora:
https://wa.me/5592981660856

Sem estrutura, não há escala."
"""

# 🔎 Detecta faturamento
def is_low_revenue(message):
    match = re.search(r'(\d+)', message.replace('.', '').replace(',', ''))
    if match:
        value = int(match.group(1))
        if value < 50000:
            return True
    return False

# 🔎 Detecta "não tenho empresa"
def no_business(message):
    keywords = ["ideia", "começar", "vou abrir", "pretendo", "planejando"]
    return any(k in message.lower() for k in keywords)

def handler(request):
    try:
        body_raw = request.body if hasattr(request, 'body') else request.rfile.read(int(request.headers['Content-Length']))
        body = json.loads(body_raw)
        user_message = body.get("message", "")

        # 🚫 BLOQUEIOS
        if is_low_revenue(user_message):
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "reply": "O modelo STARKER é para escala. Foque em validação antes de avançar."
                })
            }

        if no_business(user_message):
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "reply": "Não trabalhamos com hipóteses. Retorne quando houver operação real."
                })
            }

        # 🚀 GEMINI ATUALIZADO
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": SYSTEM_PROMPT + "\n\nUsuário: " + user_message}
                    ]
                }
            ]
        }

        response = requests.post(url, json=payload)
        result = response.json()

        reply = result["candidates"][0]["content"]["parts"][0]["text"]

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"reply": reply})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }