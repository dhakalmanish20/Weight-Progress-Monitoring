function initializeDashboardCharts(dates, weights, calories, foodData) {
    if (!Array.isArray(dates) || !Array.isArray(weights) || !Array.isArray(calories) || !foodData) {
        console.error('Invalid chart data');
        return;
    }

    // Weight Chart
    const ctxWeight = document.getElementById('weightChart')?.getContext('2d');
    if (ctxWeight) {
        new Chart(ctxWeight, {
            type: 'line',
            data: {
                labels: dates.reverse(),
                datasets: [{
                    label: 'Weight (kg)',
                    data: weights.reverse(),
                    borderColor: '#00468B',
                    backgroundColor: 'rgba(0,70,139,0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    tooltip: { mode: 'index', intersect: false },
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#e0e0e0' } },
                    x: { grid: { display: false } },
                },
            },
        });
    }

    // Calorie Chart
    const ctxCalorie = document.getElementById('calorieChart')?.getContext('2d');
    if (ctxCalorie) {
        new Chart(ctxCalorie, {
            type: 'bar',
            data: {
                labels: dates.reverse(),
                datasets: [{
                    label: 'Calories Consumed',
                    data: calories.reverse(),
                    backgroundColor: '#FFD700',
                    borderColor: '#FFD700',
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    tooltip: { mode: 'index', intersect: false },
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#e0e0e0' } },
                    x: { grid: { display: false } },
                },
            },
        });
    }

    // Food Consumption Chart
    const ctxFood = document.getElementById('foodChart')?.getContext('2d');
    if (ctxFood) {
        new Chart(ctxFood, {
            type: 'doughnut',
            data: {
                labels: foodData.labels,
                datasets: [{
                    data: foodData.values,
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#8A2BE2', '#FF4500'],
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    tooltip: { callbacks: { label: (context) => `${context.label}: ${context.raw}%` } },
                },
            },
        });
    }
}

// Auto-initialize charts on page load
document.addEventListener('DOMContentLoaded', () => {
    const dates = JSON.parse(document.getElementById('dates-data')?.textContent || '[]');
    const weights = JSON.parse(document.getElementById('weights-data')?.textContent || '[]');
    const calories = JSON.parse(document.getElementById('calories-data')?.textContent || '[]');
    const foodData = JSON.parse(document.getElementById('food-consumption-data')?.textContent || '{}');

    initializeDashboardCharts(dates, weights, calories, foodData);
});