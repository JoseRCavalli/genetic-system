/**
 * Dashboard - JavaScript
 * Carrega e exibe dados do dashboard
 */

// Carregar dados ao iniciar
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

/**
 * Carrega todos os dados do dashboard
 */
async function loadDashboard() {
    try {
        const data = await fetch('/api/dashboard-full').then(r => r.json());
        
        // Atualizar estatísticas
        updateStats(data.summary);
        
        // Atualizar médias do rebanho
        updateHerdAverages(data.herd_averages);
        
        // Atualizar top touros
        updateTopBulls(data.top_bulls);
        
        // Atualizar timestamp
        document.getElementById('last-update').textContent = formatDateTime(data.last_updated);
        
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
        showError('Erro ao carregar dados do dashboard');
    }
}

/**
 * Atualiza cards de estatísticas
 */
function updateStats(summary) {
    // Fêmeas
    document.getElementById('total-females').textContent = formatNumber(summary.total_females);
    document.getElementById('active-females').textContent = `${formatNumber(summary.active_females)} ativas`;
    
    // Touros
    document.getElementById('total-bulls').textContent = formatNumber(summary.total_bulls);
    document.getElementById('available-bulls').textContent = `${formatNumber(summary.available_bulls)} disponíveis`;
    
    // Acasalamentos
    document.getElementById('total-matings').textContent = formatNumber(summary.total_matings);
    document.getElementById('recent-matings').textContent = `${formatNumber(summary.recent_matings)} nos últimos 30 dias`;
    
    // Taxa de sucesso
    document.getElementById('success-rate').textContent = `${formatNumber(summary.success_rate, 1)}%`;
}

/**
 * Atualiza médias genéticas do rebanho
 */
function updateHerdAverages(averages) {
    // MILK
    const milk = averages.milk || 0;
    document.getElementById('avg-milk').textContent = formatNumber(milk, 0);
    
    // Calcular porcentagem para barra (assumindo range -1000 a 2000)
    const milkPercent = Math.max(0, Math.min(100, ((milk + 1000) / 3000) * 100));
    document.getElementById('bar-milk').style.width = `${milkPercent}%`;
    
    // Productive Life
    const pl = averages.productive_life || 0;
    document.getElementById('avg-pl').textContent = formatNumber(pl, 2);
    
    // Calcular porcentagem para barra (assumindo range -3 a 8)
    const plPercent = Math.max(0, Math.min(100, ((pl + 3) / 11) * 100));
    document.getElementById('bar-pl').style.width = `${plPercent}%`;
    
    // Consanguinidade
    const inb = averages.genomic_inbreeding || 0;
    document.getElementById('avg-inb').textContent = formatNumber(inb, 2) + '%';
    
    // Calcular porcentagem para barra (0-10%, menor é melhor - invertido)
    const inbPercent = Math.max(0, Math.min(100, 100 - (inb / 10 * 100)));
    document.getElementById('bar-inb').style.width = `${inbPercent}%`;
}

/**
 * Atualiza tabela de top touros
 */
function updateTopBulls(bulls) {
    const tbody = document.getElementById('top-bulls-table');
    
    if (!bulls || bulls.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-state">Nenhum touro utilizado ainda</td></tr>';
        return;
    }
    
    tbody.innerHTML = bulls.map((bull, index) => {
        const ranking = index + 1;
        let medal = '';
        
        if (ranking === 1) medal = '🥇';
        else if (ranking === 2) medal = '🥈';
        else if (ranking === 3) medal = '🥉';
        
        return `
            <tr>
                <td>
                    <span class="ranking-medal">${medal}</span>
                    ${ranking}º
                </td>
                <td><strong>${bull.code || '-'}</strong></td>
                <td>${bull.name || '-'}</td>
                <td>
                    <span class="badge badge-info">${formatNumber(bull.count)} vezes</span>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Recarrega dashboard (para botão de refresh)
 */
function refreshDashboard() {
    loadDashboard();
}
