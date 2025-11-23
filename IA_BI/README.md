# 💬 NLQ - Natural Language Query System

Sistema avançado de consulta em linguagem natural que converte perguntas em português para consultas SQL, utilizando inteligência artificial local (GPT4All) e processamento de dados com DuckDB.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Como Usar](#-como-usar)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [API Endpoints](#-api-endpoints)
- [Front-end](#-front-end)
- [Troubleshooting](#-troubleshooting)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

## 🎯 Sobre o Projeto

O **NLQ (Natural Language Query)** é uma solução completa que permite realizar consultas em bancos de dados usando linguagem natural. O sistema utiliza um modelo de linguagem local (Meta Llama 3.1) para converter perguntas em português em consultas SQL válidas, executadas através do DuckDB.

### Principais Características

- 🤖 **IA Local**: Processamento totalmente local, sem necessidade de conexão com APIs externas
- 🔒 **Segurança**: Validação de SQL para prevenir comandos maliciosos (apenas SELECT permitido)
- 📊 **Multi-formato**: Suporta arquivos Excel (.xlsx), CSV e Parquet
- 🎨 **Interface Moderna**: Front-end responsivo com design dark mode
- ⚡ **Performance**: Processamento rápido com DuckDB em memória

## ✨ Funcionalidades

### Back-end
- Conversão de perguntas em linguagem natural para SQL
- Execução segura de consultas SQL
- Análise automática do schema dos dados
- Validação e sanitização de SQL
- Suporte a múltiplos formatos de dados

### Front-end
- Interface intuitiva e moderna
- Visualização de resultados em tabelas formatadas
- Exibição do SQL gerado com opção de cópia
- Feedback visual durante processamento
- Tratamento de erros amigável
- Design responsivo (mobile e desktop)

## 🛠 Tecnologias Utilizadas

### Back-end
- **Python 3.8+**: Linguagem principal
- **Flask**: Framework web para API REST
- **GPT4All**: Biblioteca para executar modelos LLM localmente
- **DuckDB**: Banco de dados analítico em memória
- **Pandas**: Manipulação e análise de dados
- **OpenPyXL**: Leitura de arquivos Excel

### Front-end
- **HTML5**: Estrutura da interface
- **CSS3**: Estilização moderna com animações
- **JavaScript (Vanilla)**: Lógica de interação e consumo da API
- **Google Fonts (Inter)**: Tipografia moderna

### Modelo de IA
- **Meta Llama 3.1 8B Instruct**: Modelo de linguagem local para geração de SQL

## 📦 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.8 ou superior**
- **pip** (gerenciador de pacotes Python)
- **Modelo LLM**: Meta-Llama-3.1-8B-Instruct.Q8_0.gguf (deve estar em `src/api/models/`)
- **Arquivo de dados**: Excel, CSV ou Parquet (deve estar em `src/api/basedados/`)

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd IA_BI
```

### 2. Crie um ambiente virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requeriments.txt
```

### 4. Configure os arquivos necessários

#### Modelo LLM
1. Baixe o modelo **Meta-Llama-3.1-8B-Instruct.Q8_0.gguf**
2. Coloque o arquivo em: `src/api/models/`

#### Arquivo de Dados
1. Coloque seu arquivo de dados (Excel, CSV ou Parquet) em: `src/api/basedados/`
2. Por padrão, o sistema procura por: `dados_anonimizados3.xlsx`
3. Para usar outro arquivo, edite a variável `ARQUIVO_DADOS` em `src/api/nlq_engine.py`

## 💻 Como Usar

### 1. Inicie o servidor Flask

```bash
cd src/api
python api.py
```

O servidor será iniciado em `http://localhost:5000`

### 2. Acesse a interface web

Abra seu navegador e acesse:
```
http://localhost:5000
```

### 3. Faça suas perguntas

Digite perguntas em linguagem natural no campo de texto, por exemplo:

- "Quantos registros temos no total?"
- "Mostre os 10 maiores valores"
- "Qual a média dos valores da coluna X?"
- "Liste todos os registros onde Y é maior que 100"

### 4. Visualize os resultados

O sistema irá:
1. Converter sua pergunta em SQL
2. Executar a consulta
3. Exibir o SQL gerado
4. Mostrar os resultados em uma tabela formatada

## 📁 Estrutura do Projeto

```
IA_BI/
│
├── src/
│   ├── api/
│   │   ├── __pycache__/
│   │   ├── api.py                 # API Flask principal
│   │   ├── nlq_engine.py          # Engine de processamento NLQ
│   │   ├── basedados/             # Pasta para arquivos de dados
│   │   │   └── dados_anonimizados3.xlsx
│   │   └── models/                # Pasta para modelos LLM
│   │       └── Meta-Llama-3.1-8B-Instruct.Q8_0.gguf
│   │
│   └── static/                    # Arquivos estáticos do front-end
│       ├── index.html             # Interface principal
│       ├── style.css              # Estilos CSS
│       └── app.js                 # Lógica JavaScript
│
├── requeriments.txt               # Dependências Python
└── README.md                      # Este arquivo
```

## 🔌 API Endpoints

### `GET /`
Retorna a interface web do front-end.

**Resposta**: HTML da página principal

---

### `GET /api`
Verifica o status da API.

**Resposta**:
```json
{
  "status": "ok",
  "mensagem": "API funcionando"
}
```

---

### `POST /nlq`
Converte uma pergunta em linguagem natural para SQL e executa a consulta.

**Request Body**:
```json
{
  "pergunta": "Quantos registros temos no total?"
}
```

**Resposta de Sucesso**:
```json
{
  "sql": "SELECT COUNT(*) FROM tabela",
  "dados": [
    {
      "count_star()": 1000
    }
  ]
}
```

**Resposta de Erro**:
```json
{
  "erro": "Não foi possível gerar SQL válido."
}
```

---

### `POST /sql`
Executa uma consulta SQL diretamente.

**Request Body**:
```json
{
  "sql": "SELECT * FROM tabela LIMIT 10"
}
```

**Resposta**:
```json
[
  {
    "coluna1": "valor1",
    "coluna2": "valor2"
  },
  ...
]
```

## 🎨 Front-end

O front-end foi desenvolvido com foco em:

- **Usabilidade**: Interface intuitiva e fácil de usar
- **Performance**: Carregamento rápido e respostas fluidas
- **Design Moderno**: Dark mode com gradientes e animações suaves
- **Responsividade**: Funciona perfeitamente em desktop, tablet e mobile
- **Acessibilidade**: Feedback visual claro e tratamento de erros amigável

### Recursos do Front-end

- ✅ Campo de texto para perguntas em linguagem natural
- ✅ Indicador de status e loading
- ✅ Exibição do SQL gerado com botão de cópia
- ✅ Tabela de resultados formatada e responsiva
- ✅ Tratamento de erros com mensagens claras
- ✅ Verificação automática de conexão com a API

## 🔧 Troubleshooting

### Erro: "Arquivo não encontrado"
**Solução**: Certifique-se de que o arquivo de dados está em `src/api/basedados/` e que o nome corresponde ao configurado em `nlq_engine.py`.

### Erro: "Modelo não encontrado"
**Solução**: Verifique se o arquivo do modelo está em `src/api/models/` com o nome correto: `Meta-Llama-3.1-8B-Instruct.Q8_0.gguf`.

### Erro: "Não foi possível gerar SQL válido"
**Solução**: 
- Reformule sua pergunta de forma mais clara
- Certifique-se de que as colunas mencionadas existem no schema
- Verifique se a pergunta pode ser convertida em um SELECT válido

### Erro de conexão com a API
**Solução**: 
- Verifique se o servidor Flask está rodando
- Confirme que está acessando `http://localhost:5000`
- Verifique se não há firewall bloqueando a porta 5000

### Performance lenta
**Solução**: 
- O modelo LLM pode ser pesado na primeira execução
- Considere usar um modelo menor se o hardware for limitado
- Para grandes volumes de dados, considere usar formato Parquet

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

Desenvolvido como parte do projeto de Business Intelligence - Período 6.

---

**Nota**: Este projeto utiliza modelos de IA local e não requer conexão com a internet após a instalação inicial dos componentes.

