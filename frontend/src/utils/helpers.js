// Get MDI score color class
export function getMDIColor(score) {
    if (score >= 90) return 'text-mdi-excellent';
    if (score >= 70) return 'text-mdi-good';
    if (score >= 50) return 'text-mdi-fair';
    if (score >= 30) return 'text-mdi-poor';
    return 'text-mdi-critical';
}

// Get MDI background color class
export function getMDIBgColor(score) {
    if (score >= 90) return 'bg-mdi-excellent';
    if (score >= 70) return 'bg-mdi-good';
    if (score >= 50) return 'bg-mdi-fair';
    if (score >= 30) return 'bg-mdi-poor';
    return 'bg-mdi-critical';
}

// Get MDI hex color for maps
export function getMDIHexColor(score) {
    if (score >= 90) return '#10b981';
    if (score >= 70) return '#22c55e';
    if (score >= 50) return '#eab308';
    if (score >= 30) return '#f97316';
    return '#ef4444';
}

// Get MDI category name
export function getMDICategory(score) {
    if (score >= 90) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Fair';
    if (score >= 30) return 'Poor';
    return 'Critical';
}

// Format currency
export function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(amount);
}

// Format number with commas
export function formatNumber(num) {
    return new Intl.NumberFormat('en-IN').format(num);
}

// Format percentage
export function formatPercent(value, decimals = 1) {
    return `${value.toFixed(decimals)}%`;
}

// Format multiplier
export function formatMultiplier(value) {
    return `${value.toFixed(2)}×`;
}

// Format date
export function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

// Format relative time
export function formatRelativeTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
}

// Calculate debt percentage increase
export function calculateDebtIncrease(baseCost, currentCost) {
    if (baseCost <= 0) return 0;
    return ((currentCost - baseCost) / baseCost) * 100;
}

// Get asset type icon name
export function getAssetTypeIcon(type) {
    const icons = {
        road: '🛣️',
        drain: '🌊',
        streetlight: '💡',
        bridge: '🌉',
        sidewalk: '🚶',
        water_pipe: '🚰',
        sewer: '🕳️',
        traffic_signal: '🚦',
        park: '🌳',
        other: '📍',
    };
    return icons[type?.toLowerCase()] || icons.other;
}

// Get severity color
export function getSeverityColor(severity) {
    const colors = {
        low: 'text-green-400',
        medium: 'text-yellow-400',
        high: 'text-orange-400',
        critical: 'text-red-400',
    };
    return colors[severity?.toLowerCase()] || colors.medium;
}

// Truncate text
export function truncate(text, maxLength = 50) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
}
