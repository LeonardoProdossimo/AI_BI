// Configuração da API
const API_BASE_URL = window.location.origin; // Usar origem atual para evitar problemas de CORS
const API_ENDPOINTS = {
    check: `${API_BASE_URL}/api`,
    nlq: `${API_BASE_URL}/nlq`,
    sql: `${API_BASE_URL}/sql`
};

// Elementos do DOM
const elements = {
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

// Estado da aplicação
let isLoading = false;

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
});

// Inicializar aplicação
async function initializeApp() {
    updateStatusBadge('Verificando conexão...', 'warning');
    
    try {
        const response = await fetch(API_ENDPOINTS.check);
        const data = await response.json();
        
        if (data.status === 'ok') {
            updateStatusBadge('API Conectada', 'success');
            console.log('✅ API conectada com sucesso');
        } else {
            throw new Error('API não está respondendo corretamente');
        }
    } catch (error) {
        updateStatusBadge('API Desconectada', 'danger');
        console.error('Erro ao conectar com API:', error);
        // Não mostrar erro inicial, apenas atualizar badge
    }
}

// Atualizar badge de status
function updateStatusBadge(text, type) {
    if (!elements.statusBadge) return;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'warning' ? 'hourglass-split' : 
                 'x-circle';
    
    elements.statusBadge.innerHTML = `
        <span class="badge bg-${type}">
            <i class="bi bi-${icon} me-1"></i>
            ${text}
        </span>
    `;
}

// Configurar event listeners
function setupEventListeners() {
    // Enviar pergunta
    elements.btnEnviar.addEventListener('click', handleSubmit);
    
    // Enviar com Enter (Ctrl/Cmd + Enter)
    elements.pergunta.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            handleSubmit();
        }
    });
    
    // Copiar SQL
    if (elements.btnCopySql) {
        elements.btnCopySql.addEventListener('click', copySqlToClipboard);
    }
}

// Manipular envio da pergunta
async function handleSubmit() {
    const pergunta = elements.pergunta.value.trim();
    
    if (!pergunta) {
        showError('Por favor, digite uma pergunta.');
        return;
    }
    
    if (isLoading) {
        return;
    }
    
    isLoading = true;
    setLoadingState(true);
    hideError();
    hideResults();
    
    try {
        // Mostrar apenas uma mensagem de processamento
        showStatusIndicator('Processando sua pergunta... (Isso pode levar alguns minutos)');
        
        console.log('Enviando pergunta:', pergunta);
        
        // Criar AbortController para timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutos de timeout
        
        let response;
        try {
            response = await fetch(API_ENDPOINTS.nlq, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ pergunta }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);
        } catch (fetchError) {
            clearTimeout(timeoutId);
            if (fetchError.name === 'AbortError') {
                throw new Error('Tempo de espera esgotado. O processamento está demorando muito. Tente uma pergunta mais simples.');
            }
            throw fetchError;
        }
        
        console.log('Resposta recebida, status:', response.status);
        
        // Verificar se a resposta é JSON válido
        let data;
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            console.error('Resposta não é JSON:', text);
            throw new Error('Resposta inválida do servidor');
        }
        
        console.log('Dados recebidos:', data);
        
        // Verificar erros na resposta
        if (!response.ok) {
            throw new Error(data.erro || `Erro HTTP ${response.status}: ${response.statusText}`);
        }
        
        if (data.erro) {
            throw new Error(data.erro);
        }
        
        // Verificar se há dados válidos
        if (!data.sql && !data.dados) {
            throw new Error('Resposta inválida: nenhum SQL ou dados retornados');
        }
        
        hideStatusIndicator();
        displayResults(data);
        
    } catch (error) {
        console.error('Erro completo:', error);
        hideStatusIndicator();
        
        // Mensagem de erro mais amigável
        let errorMessage = 'Erro ao processar sua pergunta.';
        
        if (error.message) {
            errorMessage = error.message;
        } else if (error instanceof TypeError && error.message.includes('fetch')) {
            errorMessage = 'Não foi possível conectar ao servidor. Verifique se a API está rodando.';
        } else if (error.name === 'AbortError') {
            errorMessage = 'Tempo de espera esgotado. O processamento está demorando muito. Tente uma pergunta mais simples ou verifique o console do servidor.';
        }
        
        showError(errorMessage);
    } finally {
        isLoading = false;
        setLoadingState(false);
    }
}

// Exibir resultados
function displayResults(data) {
    console.log('Exibindo resultados:', data);
    
    // Exibir SQL
    if (data.sql && elements.sqlOutput) {
        elements.sqlOutput.textContent = data.sql;
    } else if (elements.sqlOutput) {
        elements.sqlOutput.textContent = 'SQL não disponível';
    }
    
    // Exibir dados
    if (data.dados) {
        // Verificar se dados é um objeto de erro
        if (typeof data.dados === 'object' && !Array.isArray(data.dados) && data.dados.erro) {
            showError(data.dados.erro);
            return;
        }
        
        // Verificar se é um array válido
        if (Array.isArray(data.dados)) {
            if (data.dados.length > 0) {
                displayTable(data.dados);
            } else {
                showError('Nenhum resultado encontrado para sua consulta.');
                return;
            }
        } else {
            // Se dados não é array, tentar converter
            console.warn('Dados não é um array:', data.dados);
            showError('Formato de dados inválido retornado pelo servidor.');
            return;
        }
    } else {
        showError('Nenhum dado retornado pelo servidor.');
        return;
    }
    
    showResults();
}

// Exibir tabela de resultados
function displayTable(dados) {
    // Limpar tabela
    elements.tableHead.innerHTML = '';
    elements.tableBody.innerHTML = '';
    
    // Obter colunas
    const colunas = Object.keys(dados[0]);
    
    // Criar cabeçalho
    const headerRow = document.createElement('tr');
    colunas.forEach(coluna => {
        const th = document.createElement('th');
        th.textContent = coluna;
        th.style.textTransform = 'capitalize';
        headerRow.appendChild(th);
    });
    elements.tableHead.appendChild(headerRow);
    
    // Criar linhas de dados
    dados.forEach(linha => {
        const tr = document.createElement('tr');
        colunas.forEach(coluna => {
            const td = document.createElement('td');
            const valor = linha[coluna];
            
            // Formatar valores
            if (valor === null || valor === undefined) {
                td.textContent = '-';
                td.classList.add('text-muted');
            } else if (typeof valor === 'number') {
                td.textContent = formatNumber(valor);
                td.style.fontWeight = '500';
            } else {
                td.textContent = String(valor);
            }
            
            tr.appendChild(td);
        });
        elements.tableBody.appendChild(tr);
    });
    
    // Atualizar estatísticas
    if (elements.resultStats) {
        const count = dados.length;
        elements.resultStats.textContent = `${count} ${count === 1 ? 'registro' : 'registros'} encontrado${count === 1 ? '' : 's'}`;
    }
}

// Formatar números
function formatNumber(num) {
    if (Number.isInteger(num)) {
        return num.toLocaleString('pt-BR');
    }
    return num.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Copiar SQL para clipboard
async function copySqlToClipboard() {
    const sql = elements.sqlOutput?.textContent;
    
    if (!sql) {
        return;
    }
    
    try {
        await navigator.clipboard.writeText(sql);
        
        // Feedback visual com Bootstrap
        const originalHTML = elements.btnCopySql.innerHTML;
        elements.btnCopySql.innerHTML = '<i class="bi bi-check me-1"></i>Copiado!';
        elements.btnCopySql.classList.add('btn-copy-success');
        
        setTimeout(() => {
            elements.btnCopySql.innerHTML = originalHTML;
            elements.btnCopySql.classList.remove('btn-copy-success');
        }, 2000);
        
        // Mostrar toast (opcional - pode adicionar Bootstrap Toast se quiser)
        console.log('✅ SQL copiado para a área de transferência');
        
    } catch (error) {
        console.error('Erro ao copiar:', error);
        showError('Não foi possível copiar o SQL.');
    }
}

// Controlar estado de loading
function setLoadingState(loading) {
    if (!elements.btnEnviar) return;
    
    elements.btnEnviar.disabled = loading;
    const btnText = elements.btnEnviar.querySelector('.btn-text');
    const btnLoader = elements.btnEnviar.querySelector('.btn-loader');
    
    if (loading) {
        if (btnText) btnText.classList.add('d-none');
        if (btnLoader) btnLoader.classList.remove('d-none');
    } else {
        if (btnText) btnText.classList.remove('d-none');
        if (btnLoader) btnLoader.classList.add('d-none');
    }
}

// Mostrar indicador de status (apenas uma mensagem)
function showStatusIndicator(message) {
    if (elements.statusIndicator) {
        elements.statusIndicator.style.display = 'block';
        const statusTextElement = elements.statusIndicator.querySelector('#status-text');
        if (statusTextElement) {
            statusTextElement.textContent = message;
        }
    }
}

// Ocultar indicador de status
function hideStatusIndicator() {
    if (elements.statusIndicator) {
        elements.statusIndicator.style.display = 'none';
    }
}

// Mostrar resultados
function showResults() {
    if (elements.resultsSection) {
        elements.resultsSection.style.display = 'block';
        // Scroll suave para os resultados
        setTimeout(() => {
            elements.resultsSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest' 
            });
        }, 100);
    }
}

// Ocultar resultados
function hideResults() {
    if (elements.resultsSection) {
        elements.resultsSection.style.display = 'none';
    }
}

// Mostrar erro
function showError(message) {
    if (elements.errorMessage) {
        elements.errorMessage.textContent = message;
    }
    if (elements.errorSection) {
        elements.errorSection.style.display = 'block';
        // Scroll suave para o erro
        setTimeout(() => {
            elements.errorSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest' 
            });
        }, 100);
    }
}

// Ocultar erro
function hideError() {
    if (elements.errorSection) {
        elements.errorSection.style.display = 'none';
    }
}
