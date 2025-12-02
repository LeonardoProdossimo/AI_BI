# nlq_engine.py
# Engine NLQ -> SQL Otimizada para Performance

import os
import re
import json
import duckdb
import pandas as pd
import unidecode

try:
    from gpt4all import GPT4All
except ImportError as e:
    raise ImportError(f"Erro ao importar GPT4All: {e}")

# ============================================================
# 1. CONFIGURAÇÕES
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DADOS = os.path.join(BASE_DIR, "basedados", "dados_anonimizados3.xlsx")
PASTA_MODELOS = os.path.join(BASE_DIR, "models")

# SUGESTÃO: Use modelos Q4_K_M para velocidade (ex: Llama 3 8B Q4)
# Se estiver muito lento, tente o modelo: "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"
MODELO_NOME = "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"

NOME_TABELA = "tabela"

# ============================================================
# 2. CARREGAMENTO E LIMPEZA DE DADOS
# ============================================================

def limpar_nome_coluna(nome):
    novo_nome = unidecode.unidecode(str(nome)).lower().strip()
    novo_nome = re.sub(r'[^a-z0-9_]', '_', novo_nome) # Substitui tudo que não for letra/num por _
    novo_nome = re.sub(r'_+', '_', novo_nome) # Remove _ duplicados
    if novo_nome and novo_nome[0].isdigit():
        novo_nome = "col_" + novo_nome
    return novo_nome if novo_nome else "coluna_sem_nome"

def carregar_dados():
    print(f">>> [DATA] Carregando: {os.path.basename(ARQUIVO_DADOS)}...")
    
    if not os.path.exists(ARQUIVO_DADOS):
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_DADOS}")

    ext = ARQUIVO_DADOS.lower()
    try:
        if ext.endswith(".xlsx"):
            df = pd.read_excel(ARQUIVO_DADOS)
        elif ext.endswith(".csv"):
            df = pd.read_csv(ARQUIVO_DADOS)
        elif ext.endswith(".parquet"):
            df = pd.read_parquet(ARQUIVO_DADOS)
        else:
            raise ValueError("Formato não suportado.")

        # Limpeza de colunas
        df.columns = [limpar_nome_coluna(c) for c in df.columns]
        
        # Remove colunas vazias ou 'unnamed'
        cols_uteis = [c for c in df.columns if "unnamed" not in c]
        df = df[cols_uteis]
        
        print(f">>> [DATA] Sucesso! {len(df)} linhas, {len(df.columns)} colunas.")
        return df
    except Exception as e:
        raise RuntimeError(f"Erro ao ler arquivo: {e}")

def analisar_schema(df):
    schema = []
    for col in df.columns:
        exemplo = ""
        try:
            val = df[col].dropna().iloc[0]
            exemplo = str(val)[:50] # Limita tamanho do exemplo para não confundir a IA
        except:
            pass
            
        schema.append({
            "coluna": col,
            "tipo": str(df[col].dtype),
            "exemplo": exemplo
        })
    return schema

# ============================================================
# 3. ENGINE IA & SQL
# ============================================================

def carregar_llm():
    print(f">>> [LLM] Carregando modelo na GPU (RTX 3050): {MODELO_NOME}")
    modelo_path = os.path.join(PASTA_MODELOS, MODELO_NOME)
    
    if not os.path.exists(modelo_path):
        raise FileNotFoundError(f"Modelo não encontrado: {modelo_path}")

    try:
        # A MÁGICA ACONTECE AQUI: device='gpu'
        # Isso diz para o GPT4All procurar o CUDA que você instalou
        llm = GPT4All(
            model_name=MODELO_NOME, 
            model_path=PASTA_MODELOS, 
            allow_download=False, 
            device='gpu' 
        )
        print(">>> [LLM] Modelo carregado na PLACA DE VÍDEO!")
        return llm
    except Exception as e:
        print(f">>> ERRO GPU: {e}")
        print(">>> Tentando fallback para CPU (vai ser lento)...")
        # Fallback se der erro no driver
        return GPT4All(model_name=MODELO_NOME, model_path=PASTA_MODELOS, device='cpu')
def extrair_sql(texto):
    # Regex melhorado para pegar blocos de código markdown ou texto solto
    texto = texto.replace("```sql", "").replace("```", "").strip()
    
    padrao = r"(SELECT\s+[\s\S]+?)(;|$)"
    match = re.search(padrao, texto, re.IGNORECASE)
    
    if match:
        sql_limpo = match.group(1).strip()
        return sql_limpo
    return None

def gerar_sql(modelo, pergunta, schema):
    schema_str = json.dumps(schema, indent=None) # Compacto para economizar tokens
    
    prompt = f"""
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert SQL Data Analyst for DuckDB.
Refuse to explain. Output ONLY the SQL query. 
Table name: {NOME_TABELA}
Schema: {schema_str}
<|eot_id|><|start_header_id|>user<|end_header_id|>
Create a SQL query for: {pergunta}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
    print(f">>> [IA] Gerando resposta para: '{pergunta}'...")
    
    # Streaming para o usuário ver que não travou
    resposta_completa = ""
    with modelo.chat_session():
        tokens = modelo.generate(prompt, max_tokens=250, temp=0.1, streaming=True)
        print(">>> [IA Stream]: ", end="", flush=True)
        for token in tokens:
            print(token, end="", flush=True)
            resposta_completa += token
    print("\n")
            
    return extrair_sql(resposta_completa)

# ============================================================
# 4. CLASSE PRINCIPAL
# ============================================================

class NLQEngine:
    def __init__(self):
        self.df = carregar_dados()
        self.schema = analisar_schema(self.df)
        self.llm = carregar_llm()
        
        # DuckDB em memória
        self.con = duckdb.connect(database=":memory:")
        self.con.register(NOME_TABELA, self.df)

    def perguntar(self, pergunta):
        try:
            sql = gerar_sql(self.llm, pergunta, self.schema)
            
            if not sql:
                return {"erro": "A IA não gerou um SQL válido.", "sql_raw": "N/A"}
                
            print(f">>> [SQL] Executando: {sql}")
            
            # Executa
            df_result = self.con.execute(sql).fetchdf()
            resultado = df_result.to_dict(orient="records")
            
            return {
                "sql": sql,
                "dados": resultado,
                "total_linhas": len(resultado)
            }
            
        except Exception as e:
            print(f">>> [ERRO] {e}")
            return {"erro": str(e)}

# Teste rápido se rodar direto o arquivo
if __name__ == "__main__":
    engine = NLQEngine()
    res = engine.perguntar("Quais são as colunas?")
    print(res)