import os
import sys
from flask import Flask, request, jsonify, send_file

# ============================================================
# 1. CONFIGURAÇÃO INTELIGENTE DE CAMINHOS
# ============================================================

# Caminho do arquivo atual (api.py)
CURRENT_FILE = os.path.abspath(__file__)
CURRENT_DIR = os.path.dirname(CURRENT_FILE)

# 1.1 Tentar encontrar a pasta 'static' subindo níveis
# (Procura em ./static, ../static, ../../static)
root_dir = CURRENT_DIR
static_dir = None

for _ in range(3): # Tenta subir até 3 níveis
    check_path = os.path.join(root_dir, 'static')
    if os.path.exists(check_path):
        static_dir = check_path
        break
    root_dir = os.path.dirname(root_dir)

if not static_dir:
    # Fallback: cria um caminho padrão na raiz do projeto assumida
    static_dir = os.path.join(os.path.dirname(os.path.dirname(CURRENT_DIR)), 'static')
    print(f">>> AVISO: Pasta 'static' não encontrada automaticamente. Usando fallback: {static_dir}")
else:
    print(f">>> Pasta 'static' encontrada em: {static_dir}")

# 1.2 Configurar Python Path para achar o nlq_engine.py
# Se o api.py está em src/api/, e o engine em src/, precisamos adicionar o pai ao path
sys.path.append(CURRENT_DIR) # Adiciona pasta atual
sys.path.append(os.path.dirname(CURRENT_DIR)) # Adiciona pasta pai (src)

try:
    from nlq_engine import NLQEngine
except ImportError:
    # Tenta subir mais um nível caso a estrutura seja diferente
    sys.path.append(os.path.dirname(os.path.dirname(CURRENT_DIR)))
    try:
        from nlq_engine import NLQEngine
    except ImportError as e:
        print(">>> ERRO CRÍTICO: Não foi possível encontrar 'nlq_engine.py'.")
        print(f">>> Verifique se o arquivo está na pasta 'src'. Erro: {e}")
        sys.exit(1)

# ============================================================
# 2. INICIALIZAÇÃO FLASK
# ============================================================

app = Flask(__name__, static_folder=static_dir, static_url_path='/static')

print(f">>> Inicializando Engine IA (Isso pode demorar alguns segundos)...")

# Carrega o modelo apenas uma vez na inicialização
try:
    engine = NLQEngine()
except Exception as e:
    print(f">>> ERRO ao carregar Engine: {e}")
    sys.exit(1)

# ============================================================
# 3. ROTAS
# ============================================================

@app.route("/")
def index():
    # Serve o arquivo HTML principal
    return send_file(os.path.join(static_dir, 'index.html'))

@app.route("/nlq", methods=["POST"])
def nlq():
    try:
        dados = request.get_json()
        pergunta = dados.get("pergunta", "").strip()
        
        if not pergunta:
            return jsonify({"erro": "Pergunta vazia"}), 400

        print(f"\n>>> [API] Nova pergunta: {pergunta}")
        
        # Chama a engine para processar
        # O engine já cuida do Prompt -> SQL -> Pandas -> JSON
        resposta = engine.perguntar(pergunta)
        
        return jsonify(resposta)
    
    except Exception as e:
        print(f">>> Erro API: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

@app.route("/sql", methods=["POST"])
def sql():
    # Rota extra caso queira executar SQL direto (opcional)
    try:
        dados = request.get_json()
        query = dados.get("sql", "").strip()
        if not query:
            return jsonify({"erro": "SQL vazio"}), 400
            
        resultado = engine.con.execute(query).fetchdf().to_dict(orient="records")
        return jsonify({"sql": query, "dados": resultado})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# No app.py, adicione esta rota:
@app.route('/api', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'API Online'})

# ============================================================
# 4. START
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*50)
    print(f">>> SERVIDOR ONLINE!")
    print(f">>> Acesse: http://localhost:5000")
    print("="*50 + "\n")
    
    # use_reloader=False é CRITICO para não carregar o modelo de IA duas vezes
    # host='0.0.0.0' permite acesso via rede local
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)