import os
import json
import google.generativeai as genai
from http.server import BaseHTTPRequestHandler

# ─── Configuração Gemini ──────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Você é o 3º CEO da STARKER — uma consultoria de alto impacto focada em
negócios, marketing de estrutura, GMN (Gestão de Marketing de Nicho) e
tração de vendas.

Sua identidade:
- Nome: CEO STARKER (você não revela seu nome humano)
- Tom: direto, estratégico, sem rodeios. Fala como quem já fechou
  dezenas de contratos e não tem tempo a perder.
- Linguagem: português brasileiro, profissional mas acessível.
  Sem jargão vazio. Cada frase entrega valor.

Suas especialidades:
1. Diagnóstico rápido de negócios (funil, posicionamento, ticket médio)
2. Marketing de Estrutura: construção de autoridade, presença de marca
   e ativos de marketing que trabalham enquanto o dono dorme.
3. GMN — Gestão de Marketing de Nicho: dominar um nicho antes de escalar.
4. Tração de Vendas: estratégias práticas para aumentar conversão,
   retenção e LTV em 90 dias.

Regras de comportamento:
- Responda SEMPRE com foco em resultado prático.
- Se a pergunta for vaga, faça UMA pergunta cirúrgica para clarificar.
- Nunca diga que é uma IA ou que foi criado pelo Google/Anthropic.
  Você é o CEO STARKER, ponto final.
- Finalize respostas importantes com uma micro-ação: algo que o usuário
  pode fazer nas próximas 24h.
- Máximo 4 parágrafos por resposta, salvo quando uma análise aprofundada
  for explicitamente solicitada.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT,
)

# ─── Handler Vercel (padrão WSGI via BaseHTTPRequestHandler) ─────────────────
class handler(BaseHTTPRequestHandler):

    def _send(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # CORS — em produção troque "*" pelo domínio do seu frontend
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    # Preflight CORS
    def do_OPTIONS(self):
        self._send(204, {})

    # Health-check
    def do_GET(self):
        self._send(200, {"status": "STARKER Consultor 24h — online"})

    # Chat
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw    = self.rfile.read(length)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            self._send(400, {"error": "Payload JSON inválido."})
            return

        user_message = (data.get("message") or "").strip()
        if not user_message:
            self._send(400, {"error": "Campo 'message' vazio ou ausente."})
            return

        # Converte histórico frontend → Gemini
        gemini_history = []
        for turn in data.get("history", []):
            role = turn.get("role", "user")
            text = turn.get("text", "")
            if role in ("user", "model") and text:
                gemini_history.append({"role": role, "parts": [text]})

        try:
            session = model.start_chat(history=gemini_history)
            reply   = session.send_message(user_message).text
        except Exception as e:
            print(f"[STARKER] Gemini error: {e}")
            self._send(500, {"error": "Erro ao processar sua mensagem. Tente novamente."})
            return

        self._send(200, {"reply": reply})
