# api.py
import os
from flask import Flask, request, jsonify, send_from_directory, send_file
from nlq_engine import NLQEngine

# Tentar importar flask-cors (opcional)
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False

# Configurar caminho dos arquivos estáticos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(os.path.dirname(BASE_DIR), 'static')

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/static')

# Permitir CORS para desenvolvimento (se disponível)
if CORS_AVAILABLE:
    CORS(app)

engine = NLQEngine()


# ============================================================
# ROTA PRINCIPAL - SERVE O FRONT-END
# ============================================================

@app.route("/")
def index():
    return send_file(os.path.join(STATIC_DIR, 'index.html'))


# ============================================================
# API CHECK
# ============================================================

@app.route("/api", methods=["GET"])
def api():
    return jsonify({"status": "ok", "mensagem": "API funcionando"})


# ============================================================
# NLQ → SQL → RESULTADO
# ============================================================

@app.route("/nlq", methods=["POST"])
def nlq():
    try:
        import time
        inicio = time.time()
        
        dados = request.get_json()

        if not dados or "pergunta" not in dados:
            return jsonify({"erro": "Campo 'pergunta' é obrigatório"}), 400

        pergunta = dados["pergunta"].strip()
        
        if not pergunta:
            return jsonify({"erro": "A pergunta não pode estar vazia"}), 400

        print(f"\n{'='*60}")
        print(f">>> NOVA REQUISIÇÃO - {time.strftime('%H:%M:%S')}")
        print(f">>> Pergunta: {pergunta}")
        print(f"{'='*60}\n")
        
        resposta = engine.perguntar(pergunta)
        
        tempo_total = time.time() - inicio
        print(f"\n{'='*60}")
        print(f">>> Processamento concluído em {tempo_total:.2f} segundos")
        print(f">>> Resposta: {resposta.get('sql', 'N/A')[:100]}...")
        print(f"{'='*60}\n")
        
        return jsonify(resposta)
    
    except Exception as e:
        print(f">>> ERRO CRÍTICO ao processar pergunta: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": f"Erro ao processar pergunta: {str(e)}"}), 500


# ============================================================
# EXECUTAR SQL DIRETO
# ============================================================

@app.route("/sql", methods=["POST"])
def sql():
    dados = request.get_json()

    if not dados or "sql" not in dados:
        return jsonify({"erro": "Campo 'sql' é obrigatório"}), 400

    resposta = engine.executar(dados["sql"])
    return jsonify(resposta)


# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
