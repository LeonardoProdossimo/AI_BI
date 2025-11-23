# nlq_engine.py
# Engine NLQ → SQL profissional para uso com API Flask

import os
import re
import json
import duckdb
import pandas as pd

# Desabilitar CUDA antes de importar GPT4All
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Força uso de CPU

try:
    from gpt4all import GPT4All
except ImportError as e:
    raise ImportError(f"Erro ao importar GPT4All: {e}. Certifique-se de que está instalado: pip install gpt4all")

# ============================================================
# 1. CONFIGURAÇÕES DINÂMICAS DE CAMINHOS
# ============================================================

# Caminho absoluto da pasta onde este arquivo está
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho para a BASE DE DADOS (Excel, CSV ou Parquet)
ARQUIVO_DADOS = os.path.join(BASE_DIR, "basedados", "dados_anonimizados3.xlsx")

# Caminho para o modelo
PASTA_MODELOS = os.path.join(BASE_DIR, "models")
MODELO_NOME = "Meta-Llama-3.1-8B-Instruct.Q8_0.gguf"

# Nome da tabela que será registrada no DuckDB
NOME_TABELA = "tabela"


# ============================================================
# 2. CARREGAR DADOS (xlsx, csv ou parquet)
# ============================================================

def carregar_dados():
    print(f">>> Carregando arquivo: {ARQUIVO_DADOS}")

    if not os.path.exists(ARQUIVO_DADOS):
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_DADOS}")

    extensao = ARQUIVO_DADOS.lower()

    try:
        if extensao.endswith(".xlsx"):
            df = pd.read_excel(ARQUIVO_DADOS)
        elif extensao.endswith(".csv"):
            df = pd.read_csv(ARQUIVO_DADOS)
        elif extensao.endswith(".parquet"):
            df = pd.read_parquet(ARQUIVO_DADOS)
        else:
            raise ValueError("Formato não suportado. Use XLSX, CSV ou Parquet.")
    except Exception as e:
        raise RuntimeError(f"Erro ao ler arquivo: {e}")

    print(">>> Dados carregados com sucesso!\n")
    print(df.head())

    return df


# ============================================================
# 3. ANALISAR SCHEMA
# ============================================================

def analisar_schema(df):
    schema = []
    for col in df.columns:
        exemplo = None
        try:
            exemplo = df[col].dropna().iloc[0]
        except:
            pass

        schema.append({
            "coluna": col,
            "tipo": str(df[col].dtype),
            "nulos": int(df[col].isna().sum()),
            "exemplo": exemplo
        })
    return schema


# ============================================================
# 4. INICIAR DUCKDB
# ============================================================

def iniciar_duckdb(df):
    con = duckdb.connect(database=":memory:")
    con.register(NOME_TABELA, df)
    con.execute(f"CREATE VIEW {NOME_TABELA} AS SELECT * FROM {NOME_TABELA}")
    print(">>> DuckDB iniciado e tabela registrada!\n")
    return con


# ============================================================
# 5. CARREGAR MODELO LLM LOCAL
# ============================================================

def carregar_llm():
    print(">>> Carregando modelo LLM (GPT4All)...")

    modelo_path = os.path.join(PASTA_MODELOS, MODELO_NOME)

    if not os.path.exists(modelo_path):
        raise FileNotFoundError(
            f"Arquivo do modelo não encontrado:\n{modelo_path}\n"
            f"Certifique-se de que está dentro da pasta /models/"
        )

    try:
        print(f">>> Caminho do modelo: {modelo_path}")
        print(">>> Configurando para usar CPU (evitando problemas com CUDA)...")
        
        # Forçar uso de CPU desabilitando CUDA
        os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Desabilita CUDA
        os.environ['GPT4ALL_MODEL_TYPE'] = 'cpu'
        
        # Tentar carregar o modelo
        try:
            llm = GPT4All(
                model_name=MODELO_NOME,
                model_path=PASTA_MODELOS,
                allow_download=False
            )
        except Exception as load_error:
            print(f">>> Erro ao carregar com configuração padrão: {load_error}")
            print(">>> Tentando carregar sem especificar device...")
            # Tentar novamente sem parâmetros adicionais
            llm = GPT4All(
                model_name=MODELO_NOME,
                model_path=PASTA_MODELOS,
                allow_download=False
            )
        
        print(">>> Modelo carregado, testando resposta...")
        # Teste rápido para verificar se o modelo está funcionando
        try:
            print(">>> Executando teste rápido do modelo...")
            teste = llm.generate("Say hello", max_tokens=10, temp=0.1, streaming=False)
            print(f">>> Teste do modelo OK (resposta: {teste[:30] if teste else 'vazia'}...)")
        except KeyboardInterrupt:
            print(">>> AVISO: Teste interrompido pelo usuário")
            print(">>> Continuando mesmo assim...")
        except Exception as teste_error:
            print(f">>> AVISO: Erro ao testar modelo: {teste_error}")
            print(">>> Continuando mesmo assim...")
        
        print(">>> Modelo carregado com sucesso!\n")
        return llm
    except Exception as e:
        print(f">>> ERRO ao carregar modelo: {str(e)}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"Erro ao carregar modelo GPT4All: {e}")


# ============================================================
# 6. EXTRAIR SQL DA RESPOSTA
# ============================================================

def extrair_sql(texto):
    padrao = r"(SELECT[\s\S]*?)(;|$)"
    m = re.search(padrao, texto, re.IGNORECASE)
    return m.group(1).strip() if m else None


# ============================================================
# 7. VALIDAR SQL (segurança)
# ============================================================

def sql_valido(sql):
    if not sql:
        return False

    proibidos = ["update", "delete", "insert", "drop", "alter", "create", "truncate"]

    for p in proibidos:
        if re.search(rf"\b{p}\b", sql, re.IGNORECASE):
            return False

    return sql.lower().startswith("select")


# ============================================================
# 8. PROMPT PARA NLQ → SQL
# ============================================================

def montar_prompt(pergunta, schema):
    return f"""
Você é um gerador SQL para DuckDB.

REGRAS:
- Retorne APENAS um SELECT.
- Não invente colunas.
- Não use UPDATE, DELETE, INSERT, DROP, ALTER ou CREATE.
- Não use crases.
- Não explique nada, apenas retorne SQL puro.

Tabela disponível: {NOME_TABELA}
Schema:
{json.dumps(schema, indent=2)}

Pergunta:
{pergunta}

Retorne SOMENTE o SQL.
"""


# ============================================================
# 9. GERAR SQL COM IA (com fallback de correção)
# ============================================================

def gerar_sql(modelo, pergunta, schema):
    print(">>> Montando prompt para o LLM...")
    prompt = montar_prompt(pergunta, schema)
    
    print(">>> Enviando prompt para o modelo LLM (isso pode demorar alguns minutos)...")
    print(">>> AVISO: O processamento pode levar 2-5 minutos na primeira execução...")
    
    try:
        # Usar streaming=False para evitar problemas com callbacks
        resposta = modelo.generate(
            prompt, 
            max_tokens=300, 
            temp=0.1,
            streaming=False,
            top_k=40,
            top_p=0.9,
            repeat_penalty=1.1
        )
        
        if not resposta:
            print(">>> ERRO: Resposta vazia do modelo")
            return None
            
        print(f">>> Resposta do LLM recebida (tamanho: {len(resposta)} caracteres)")
        sql = extrair_sql(resposta)
        print(f">>> SQL extraído: {sql}")

        if sql_valido(sql):
            print(">>> SQL válido gerado na primeira tentativa")
            return sql

        print(">>> SQL inválido, tentando correção...")
        # Tentativa de correção
        prompt_fix = f"""
Corrija o SQL abaixo para um SELECT válido de DuckDB:

{sql}

Retorne apenas o SELECT corrigido.
"""
        print(">>> Enviando prompt de correção para o LLM...")
        resposta2 = modelo.generate(
            prompt_fix, 
            max_tokens=200, 
            temp=0.1,
            streaming=False
        )
        
        if not resposta2:
            print(">>> ERRO: Resposta de correção vazia")
            return sql  # Retornar o SQL original mesmo que inválido
        
        print(f">>> Resposta de correção recebida")
        sql2 = extrair_sql(resposta2)

        if sql_valido(sql2):
            print(">>> SQL válido gerado após correção")
            return sql2

        print(">>> Não foi possível gerar SQL válido após correção")
        return sql if sql else None
        
    except KeyboardInterrupt:
        print(">>> ERRO: Processamento interrompido pelo usuário")
        raise RuntimeError("Processamento interrompido. Tente novamente.")
    except Exception as e:
        print(f">>> Erro ao gerar SQL: {str(e)}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"Erro ao gerar SQL: {str(e)}")


# ============================================================
# 10. EXECUTAR SQL
# ============================================================

def executar_sql(con, sql):
    try:
        df = con.execute(sql).fetchdf()
        return df.to_dict(orient="records")
    except Exception as e:
        return {"erro": str(e)}


# ============================================================
# 11. ENGINE PRINCIPAL
# ============================================================

class NLQEngine:

    def __init__(self):
        self.df = carregar_dados()
        self.schema = analisar_schema(self.df)
        self.con = iniciar_duckdb(self.df)
        self.llm = carregar_llm()

    def perguntar(self, pergunta):
        print(f">>> Iniciando processamento da pergunta: {pergunta}")
        
        try:
            print(">>> Gerando SQL com o modelo LLM...")
            sql = gerar_sql(self.llm, pergunta, self.schema)
            print(f">>> SQL gerado: {sql}")

            if not sql:
                print(">>> Erro: Não foi possível gerar SQL válido")
                return {"erro": "Não foi possível gerar SQL válido."}

            print(">>> Executando SQL no DuckDB...")
            dados = executar_sql(self.con, sql)
            print(f">>> SQL executado. Resultados: {len(dados) if isinstance(dados, list) else 'erro'}")

            if isinstance(dados, dict) and "erro" in dados:
                print(f">>> Erro ao executar SQL: {dados['erro']}")
                return {"erro": f"Erro ao executar SQL: {dados['erro']}", "sql": sql}

            return {
                "sql": sql,
                "dados": dados
            }
        except Exception as e:
            print(f">>> Erro no processamento: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"erro": f"Erro ao processar pergunta: {str(e)}"}

    def executar(self, sql):
        return executar_sql(self.con, sql)

    def get_schema(self):
        return self.schema
