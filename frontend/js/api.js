/**
 * Cliente API
 * Funções para comunicação com o backend
 */

const API_BASE = 'http://localhost:5000/api';

class API {
    /**
     * Faz requisição GET
     */
    static async get(endpoint) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Erro na requisição GET:', error);
            throw error;
        }
    }

    /**
     * Faz requisição POST
     */
    static async post(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erro na requisição POST:', error);
            throw error;
        }
    }

    /**
     * Faz requisição PUT
     */
    static async put(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erro na requisição PUT:', error);
            throw error;
        }
    }

    /**
     * Upload de arquivo
     */
    static async upload(endpoint, file, additionalData = {}) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            // Adicionar dados extras
            Object.keys(additionalData).forEach(key => {
                formData.append(key, additionalData[key]);
            });
            
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro no upload');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erro no upload:', error);
            throw error;
        }
    }

    // ========================================================================
    // FÊMEAS
    // ========================================================================

    static async getFemales(params = {}) {
        const query = new URLSearchParams(params).toString();
        return await this.get(`/females?${query}`);
    }

    static async getFemale(id) {
        return await this.get(`/females/${id}`);
    }

    static async importFemales(file, user = 'Pedro') {
        return await this.upload('/females/import', file, { user });
    }

    // ========================================================================
    // TOUROS
    // ========================================================================

    static async getBulls(params = {}) {
        const query = new URLSearchParams(params).toString();
        return await this.get(`/bulls?${query}`);
    }

    static async getBull(code) {
        return await this.get(`/bulls/${code}`);
    }

    static async importBulls(file, user = 'Pedro') {
        return await this.upload('/bulls/import', file, { user });
    }

    // ========================================================================
    // ACASALAMENTOS
    // ========================================================================

    static async createManualMating(femaleId, bullId, save = true) {
        return await this.post('/matings/manual', {
            female_id: femaleId,
            bull_id: bullId,
            save: save
        });
    }

    static async createBatchMating(femaleIds, options = {}) {
        return await this.post('/matings/batch', {
            female_ids: femaleIds,
            priorities: options.priorities,
            max_inbreeding: options.max_inbreeding || 6.0,
            top_n: options.top_n || 5,
            filters: options.filters,
            save: options.save || false
        });
    }

    static async getMatings(params = {}) {
        const query = new URLSearchParams(params).toString();
        return await this.get(`/matings?${query}`);
    }

    static async getMating(id) {
        return await this.get(`/matings/${id}`);
    }

    static async updateMating(id, data) {
        return await this.put(`/matings/${id}`, data);
    }

    // ========================================================================
    // ANALYTICS
    // ========================================================================

    static async getDashboard() {
        return await this.get('/analytics/dashboard');
    }

    static async getDistribution(index, entity = 'female', bins = 10) {
        return await this.get(`/analytics/distributions/${index}?entity=${entity}&bins=${bins}`);
    }

    static async getMultipleDistributions(indices) {
        const indicesStr = Array.isArray(indices) ? indices.join(',') : indices;
        return await this.get(`/analytics/distributions?indices=${indicesStr}`);
    }

    static async getEvolution(index, months = 12) {
        return await this.get(`/analytics/evolution/${index}?months=${months}`);
    }

    static async getMatingAnalysis() {
        return await this.get('/analytics/matings');
    }

    static async getBullPerformance(bullId = null) {
        const endpoint = bullId 
            ? `/analytics/bulls/performance?bull_id=${bullId}`
            : '/analytics/bulls/performance';
        return await this.get(endpoint);
    }

    static async getAccuracy() {
        return await this.get('/analytics/accuracy');
    }

    static async getChartData(type, index, params = {}) {
        const query = new URLSearchParams(params).toString();
        return await this.get(`/analytics/charts/${type}/${index}?${query}`);
    }

    static async getImportHistory(page = 1, perPage = 20) {
        return await this.get(`/analytics/imports?page=${page}&per_page=${perPage}`);
    }

    static async getPreferences() {
        return await this.get('/analytics/preferences');
    }

    static async updatePreferences(preferences) {
        return await this.put('/analytics/preferences', preferences);
    }

    // ========================================================================
    // SISTEMA
    // ========================================================================

    static async getHealth() {
        return await this.get('/health');
    }

    static async getStatus() {
        return await this.get('/status');
    }
}

// ============================================================================
// UTILIDADES
// ============================================================================

/**
 * Formata números
 */
function formatNumber(value, decimals = 0) {
    if (value === null || value === undefined) return '-';
    return Number(value).toLocaleString('pt-BR', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Formata datas
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

/**
 * Formata data/hora
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
}

/**
 * Mostra notificação de sucesso
 */
function showSuccess(message) {
    // Implementar notificação toast
    console.log('✅ Sucesso:', message);
    alert(message);
}

/**
 * Mostra notificação de erro
 */
function showError(message) {
    console.error('❌ Erro:', message);
    alert('Erro: ' + message);
}

/**
 * Mostra loading
 */
function showLoading(element) {
    if (element) {
        element.innerHTML = '<div class="loading-spinner"></div> Carregando...';
    }
}

/**
 * Esconde loading
 */
function hideLoading(element) {
    if (element) {
        element.innerHTML = '';
    }
}

/**
 * Determina cor baseada em score
 */
function getScoreColor(score) {
    if (score >= 85) return 'success';
    if (score >= 75) return 'primary';
    if (score >= 65) return 'info';
    if (score >= 50) return 'warning';
    return 'danger';
}

/**
 * Determina cor baseada em consanguinidade
 */
function getInbreedingColor(inbreeding) {
    if (inbreeding < 6.0) return 'success';      // Verde: < 6% (Ideal)
    if (inbreeding < 8.0) return 'warning';      // Amarelo: 6-8% (Atenção)
    return 'danger';                              // Vermelho: > 8% (Crítico)
}