/**
 * Biblioteca de Ícones
 * Lordicon (animados) + FontAwesome (estáticos)
 */

// Configuração dos ícones Lordicon
const LORDICONS = {
    // Animais
    cow: {
        src: 'https://cdn.lordicon.com/uqpazftn.json', // 523-farm-cow
        trigger: 'hover',
        colors: 'primary:#121331,secondary:#08a88a'
    },
    bull: {
        src: 'https://cdn.lordicon.com/hrjifpbq.json', // 1199-bull
        trigger: 'hover',
        colors: 'primary:#121331,secondary:#e83a30'
    },
    
    // Gráficos e Analytics
    chart: {
        src: 'https://cdn.lordicon.com/fhtaantg.json', // 153-bar-chart
        trigger: 'hover',
        colors: 'primary:#121331,secondary:#08a88a'
    },
    pieChart: {
        src: 'https://cdn.lordicon.com/fhtaantg.json',
        trigger: 'hover',
        colors: 'primary:#121331,secondary:#4bb3fd'
    },
    
    // Ações
    upload: {
        src: 'https://cdn.lordicon.com/rcjwbphf.json',
        trigger: 'hover',
        colors: 'primary:#121331,secondary:#08a88a'
    },
    download: {
        src: 'https://cdn.lordicon.com/rcjwbphf.json',
        trigger: 'hover',
        colors: 'primary:#121331,secondary:#4bb3fd'
    },
    
    // Sistema
    checkmark: {
        src: 'https://cdn.lordicon.com/lomfljuq.json',
        trigger: 'hover',
        colors: 'primary:#121331,secondary:#08a88a'
    },
    warning: {
        src: 'https://cdn.lordicon.com/keaiyjcx.json',
        trigger: 'hover',
        colors: 'primary:#121331,secondary:#f4c430'
    }
};

// Ícones FontAwesome (fallback)
const FONTAWESOME_ICONS = {
    // Animais
    cow: 'fa-solid fa-cow',
    bull: 'fa-solid fa-horse',
    
    // Gráficos
    chart: 'fa-solid fa-chart-bar',
    pieChart: 'fa-solid fa-chart-pie',
    lineChart: 'fa-solid fa-chart-line',
    
    // Ações
    search: 'fa-solid fa-search',
    filter: 'fa-solid fa-filter',
    save: 'fa-solid fa-save',
    edit: 'fa-solid fa-edit',
    delete: 'fa-solid fa-trash',
    upload: 'fa-solid fa-upload',
    download: 'fa-solid fa-download',
    refresh: 'fa-solid fa-sync',
    
    // Sistema
    checkmark: 'fa-solid fa-check',
    close: 'fa-solid fa-times',
    warning: 'fa-solid fa-exclamation-triangle',
    info: 'fa-solid fa-info-circle',
    settings: 'fa-solid fa-cog',
    
    // Navegação
    home: 'fa-solid fa-home',
    history: 'fa-solid fa-history',
    analytics: 'fa-solid fa-chart-line',
    
    // Outros
    calendar: 'fa-solid fa-calendar',
    user: 'fa-solid fa-user',
    heart: 'fa-solid fa-heart',
    star: 'fa-solid fa-star'
};

/**
 * Cria ícone Lordicon
 */
function createLordicon(type, size = 'medium') {
    const config = LORDICONS[type];
    if (!config) {
        console.warn(`Ícone Lordicon '${type}' não encontrado`);
        return createFontAwesomeIcon(type, size);
    }
    
    const sizeMap = {
        small: 32,
        medium: 48,
        large: 64,
        xl: 96
    };
    
    const lordicon = document.createElement('lord-icon');
    lordicon.setAttribute('src', config.src);
    lordicon.setAttribute('trigger', config.trigger);
    lordicon.setAttribute('colors', config.colors);
    lordicon.style.width = `${sizeMap[size]}px`;
    lordicon.style.height = `${sizeMap[size]}px`;
    
    return lordicon;
}

/**
 * Cria ícone FontAwesome
 */
function createFontAwesomeIcon(type, size = 'medium') {
    const iconClass = FONTAWESOME_ICONS[type];
    if (!iconClass) {
        console.warn(`Ícone FontAwesome '${type}' não encontrado`);
        return document.createTextNode('?');
    }
    
    const i = document.createElement('i');
    i.className = `${iconClass} fa-icon ${size}`;
    
    return i;
}

/**
 * Substitui emoji por ícone
 * Uso: <span class="icon" data-icon="cow" data-size="medium"></span>
 */
function replaceIconsInPage() {
    const iconElements = document.querySelectorAll('[data-icon]');
    
    iconElements.forEach(element => {
        const iconType = element.getAttribute('data-icon');
        const size = element.getAttribute('data-size') || 'medium';
        const useLordicon = element.getAttribute('data-lordicon') !== 'false';
        
        // Limpar conteúdo existente
        element.innerHTML = '';
        
        // Criar ícone
        const icon = useLordicon && LORDICONS[iconType]
            ? createLordicon(iconType, size)
            : createFontAwesomeIcon(iconType, size);
        
        element.appendChild(icon);
    });
}

/**
 * Helper: Retorna HTML do ícone
 */
function getIconHTML(type, size = 'medium', useLordicon = true) {
    if (useLordicon && LORDICONS[type]) {
        const config = LORDICONS[type];
        const sizeMap = { small: 32, medium: 48, large: 64, xl: 96 };
        
        return `<lord-icon
            src="${config.src}"
            trigger="${config.trigger}"
            colors="${config.colors}"
            style="width:${sizeMap[size]}px;height:${sizeMap[size]}px">
        </lord-icon>`;
    }
    
    const iconClass = FONTAWESOME_ICONS[type] || 'fa-solid fa-question';
    return `<i class="${iconClass} fa-icon ${size}"></i>`;
}

// Inicializar quando página carregar
document.addEventListener('DOMContentLoaded', () => {
    // Carregar script do Lordicon
    if (!document.querySelector('script[src*="lordicon"]')) {
        const script = document.createElement('script');
        script.src = 'https://cdn.lordicon.com/lordicon.js';
        document.head.appendChild(script);
    }
    
    // Substituir ícones após um pequeno delay (esperar Lordicon carregar)
    setTimeout(() => {
        replaceIconsInPage();
    }, 100);
});