function changeTimeRange(timeRange, type) {
    window.location.href = `/${type}?time=${timeRange}`;
}

document.addEventListener('DOMContentLoaded', (event) => {
    const urlParams = new URLSearchParams(window.location.search);
    const timeRange = urlParams.get('time') || 'short_term';
    document.getElementById('timerange').value = timeRange;
}) 