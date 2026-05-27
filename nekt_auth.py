"""
Fluxo OAuth PKCE para autenticar com o Nekt MCP Server.
Execute: python nekt_auth.py
Depois abra a URL no browser, autorize, e o token será salvo em nekt_token.json
"""
import http.server
import threading
import webbrowser
import json
import hashlib
import base64
import os
import secrets
import urllib.parse
import urllib.request
import ssl
import warnings
import sys

NEKT_BASE_URL = "https://nekt-app-mcp.seazone.com.br"
REDIRECT_PORT = 9731
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
TOKEN_FILE = "nekt_token.json"

# Tentar registrar um client dinamicamente
def register_client():
    url = f"{NEKT_BASE_URL}/register"
    payload = json.dumps({
        "client_name": "Claude Code - SZI Painel Terrenos",
        "redirect_uris": [REDIRECT_URI],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_post"
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read())
            print(f"[OK] Client registrado: client_id={data.get('client_id')}")
            return data.get("client_id"), data.get("client_secret", "")
    except Exception as e:
        print(f"[WARN] Registro dinamico falhou ({e}), usando client_id padrao")
        return "claude-code", ""

def generate_pkce():
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge

def build_auth_url(client_id, code_challenge, state):
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
        "scope": "mcp"
    }
    return f"{NEKT_BASE_URL}/authorize?" + urllib.parse.urlencode(params)

def exchange_code(code, client_id, client_secret, code_verifier):
    url = f"{NEKT_BASE_URL}/token"
    payload = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret,
        "code_verifier": code_verifier
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        return json.loads(resp.read())

# Estado compartilhado
auth_result = {"code": None, "error": None, "done": False}

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            auth_result["code"] = params["code"][0]
            body = b"<h2>Autorizado! Pode fechar esta aba.</h2><p>Voltando ao Claude...</p>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        elif "error" in params:
            auth_result["error"] = params.get("error_description", ["Erro desconhecido"])[0]
            body = f"<h2>Erro: {auth_result['error']}</h2>".encode()
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        auth_result["done"] = True

    def log_message(self, *args):
        pass  # silenciar logs HTTP

def main():
    print("=" * 60)
    print("  Autenticação Nekt MCP - OAuth PKCE")
    print("=" * 60)

    # 1. Registrar client
    client_id, client_secret = register_client()

    # 2. Gerar PKCE
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(16)

    # 3. URL de autorização
    auth_url = build_auth_url(client_id, code_challenge, state)

    # 4. Iniciar servidor de callback
    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.daemon = True
    thread.start()

    print(f"\n[→] Abrindo browser para autorizacao...")
    print(f"\nURL: {auth_url}\n")
    webbrowser.open(auth_url)

    print("[⏳] Aguardando callback do browser...")
    thread.join(timeout=120)

    if not auth_result["done"]:
        print("[✗] Timeout - nenhuma resposta recebida em 2 minutos")
        sys.exit(1)

    if auth_result["error"]:
        print(f"[✗] Erro na autorização: {auth_result['error']}")
        sys.exit(1)

    code = auth_result["code"]
    print(f"[OK] Código recebido: {code[:20]}...")

    # 5. Trocar código por token
    print("[→] Trocando código por token...")
    try:
        token_data = exchange_code(code, client_id, client_secret, code_verifier)
        token_data["client_id"] = client_id
        token_data["client_secret"] = client_secret
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f, indent=2)
        print(f"[✓] Token salvo em {TOKEN_FILE}")
        print(f"    access_token: {token_data.get('access_token', '')[:30]}...")
        print(f"    token_type: {token_data.get('token_type')}")
        print(f"    expires_in: {token_data.get('expires_in')}s")
    except Exception as e:
        print(f"[✗] Falha ao trocar código: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
