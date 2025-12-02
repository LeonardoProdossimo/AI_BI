// Configuração da API
const API_BASE_URL = window.location.origin;
const API_ENDPOINTS = {
    check: `${API_BASE_URL}/api`,
    nlq: `${API_BASE_URL}/nlq`,
    sql: `${API_BASE_URL}/sql`
};

// Variável global para guardar os elementos DEPOIS
let elements = {};
let isLoading = false;

// Inicialização: Só roda quando o HTML estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    // 1. CORREÇÃO: Pegar elementos aqui dentro, não no topo
    elements = {
        pergunta: document.getElementById('pergunta'),
        btnEnviar: document.getElementById('btn-enviar'),
        btnCopySql: document.getElementById('btn-copy-sql'),
        statusIndicator: document.getElementById('status-indicator'),
        statusBadge: document.getElementById('status-badge'),
        statusText: document.getElementById('status-text'),
        resultsSection: document.getElementById('results-section'),
        errorSection: document.getElementById('error-section'),
        errorMessage: document.getElementById('error-message'),
        sqlOutput: document.getElementById('sql-output'),
        resultStats: document.getElementById('result-stats'),
        tableHead: document.getElementById('table-head'),
        tableBody: document.getElementById('table-body')
    };

    // Verificar se achou o botão antes de continuar
    if (elements.btnEnviar) {
        initializeApp();
        setupEventListeners();
    } else {
        console.error("Erro: Elementos HTML não encontrados. Verifique os IDs no index.html");
    }
});

// Inicializar aplicação
async function initializeApp() {
    if(elements.statusBadge) updateStatusBadge('Verificando conexão...', 'warning');
    
    try {
        const response = await fetch(API_ENDPOINTS.check);
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'ok') {
                updateStatusBadge('API Conectada', 'success');
                console.log('✅ API conectada');
            }
        } else {
            throw new Error('404 ou Erro no Servidor');
        }
    } catch (error) {
        updateStatusBadge('API Offline', 'danger');
        console.warn('Backend não respondendo na rota /api. Verifique o app.py');
    }
}

// Atualizar badge de status
function updateStatusBadge(text, type) {
    if (!elements.statusBadge) return;
    const icon = type === 'success' ? 'check-circle' : type === 'warning' ? 'hourglass-split' : 'x-circle';
    elements.statusBadge.innerHTML = `<span class="badge bg-${type}"><i class="bi bi-${icon} me-1"></i> ${text}</span>`;
}

// Configurar event listeners
function setupEventListeners() {
    // 2. CORREÇÃO: Removido os () do handleSubmit
    elements.btnEnviar.addEventListener('click', handleSubmit);
    
    elements.pergunta.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            handleSubmit();
        }
    });
    
    if (elements.btnCopySql) {
        elements.btnCopySql.addEventListener('click', copySqlToClipboard);
    }
}

// Manipular envio da pergunta
async function handleSubmit() {
    const pergunta = elements.pergunta.value.trim();
    
    if (!pergunta) return showError('Por favor, digite uma pergunta.');
    if (isLoading) return;
    
    isLoading = true;
    setLoadingState(true);
    hideError();
    hideResults();
    
    try {
        showStatusIndicator('Processando...');
        
        const response = await fetch(API_ENDPOINTS.nlq, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pergunta })
        });
        
        const data = await response.json();
        
        if (!response.ok) throw new Error(data.erro || 'Erro no servidor');
        
        hideStatusIndicator();
        displayResults(data);
        
    } catch (error) {
        hideStatusIndicator();
        showError(error.message || 'Erro de conexão');
    } finally {
        isLoading = false;
        setLoadingState(false);
    }
}

// Funções de UI (Display/Hide/Format)
function displayResults(data) {
    if (elements.resultsSection) {
        elements.resultsSection.style.display = 'block';
        elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    if (elements.sqlOutput) elements.sqlOutput.textContent = data.sql || '-- Sem SQL';

    if (data.dados && Array.isArray(data.dados)) {
        displayTable(data.dados);
    } else {
        showError('Nenhum dado retornado.');
    }
}

function displayTable(dados) {
    elements.tableHead.innerHTML = '';
    elements.tableBody.innerHTML = '';
    
    if (dados.length === 0) {
        elements.tableBody.innerHTML = '<tr><td colspan="5" class="text-center">Sem resultados</td></tr>';
        return;
    }

    const colunas = Object.keys(dados[0]);
    
    // Cabeçalho
    const trHead = document.createElement('tr');
    colunas.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        trHead.appendChild(th);
    });
    elements.tableHead.appendChild(trHead);
    
    // Linhas
    dados.forEach(linha => {
        const tr = document.createElement('tr');
        colunas.forEach(col => {
            const td = document.createElement('td');
            td.textContent = linha[col];
            tr.appendChild(td);
        });
        elements.tableBody.appendChild(tr);
    });

    if (elements.resultStats) elements.resultStats.textContent = `${dados.length} registros`;
}

function copySqlToClipboard() {
    if (!elements.sqlOutput) return;
    navigator.clipboard.writeText(elements.sqlOutput.textContent);
    const original = elements.btnCopySql.innerHTML;
    elements.btnCopySql.innerHTML = '<i class="bi bi-check"></i> Copiado!';
    setTimeout(() => elements.btnCopySql.innerHTML = original, 2000);
}

function setLoadingState(loading) {
    if (!elements.btnEnviar) return;
    elements.btnEnviar.disabled = loading;
    const loader = elements.btnEnviar.querySelector('.btn-loader');
    const text = elements.btnEnviar.querySelector('.btn-text');
    if(loader) loader.classList.toggle('d-none', !loading);
    if(text) text.classList.toggle('d-none', loading);
}

function showStatusIndicator(msg) {
    if (elements.statusIndicator) {
        elements.statusIndicator.style.display = 'block';
        if(elements.statusText) elements.statusText.textContent = msg;
    }
}

function hideStatusIndicator() {
    if (elements.statusIndicator) elements.statusIndicator.style.display = 'none';
}

function showError(msg) {
    if (elements.errorSection) {
        elements.errorSection.style.display = 'block';
        if(elements.errorMessage) elements.errorMessage.textContent = msg;
    }
}

function hideError() {
    if (elements.errorSection) elements.errorSection.style.display = 'none';
}

function hideResults() {
    if (elements.resultsSection) elements.resultsSection.style.display = 'none';
}