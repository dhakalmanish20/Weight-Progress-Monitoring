function initializeDashboardCharts(dates, weights, calories, foodData) {
    // Weight Chart
    const ctxWeight = document.getElementById('weightChart').getContext('2d');
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
                tension: 0.4
            }]
        },
        options: {
            responsive: true
        }
    });

    // Calorie Chart
    const ctxCalorie = document.getElementById('calorieChart').getContext('2d');
    new Chart(ctxCalorie, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Calories Consumed',
                data: calories.reverse(),
                backgroundColor: '#FFD700',
                borderColor: '#FFD700',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true
        }
    });

    // Food Consumption Chart
    const ctxFood = document.getElementById('foodChart').getContext('2d');
    new Chart(ctxFood, {
        type: 'doughnut',
        data: {
            labels: foodData.labels,
            datasets: [{
                data: foodData.values,
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56',
                    '#8A2BE2', '#FF4500', '#008080',
                    '#FFD700', '#7CFC00', '#FF69B4', '#CD853F'
                ]
            }]
        },
        options: {
            responsive: true
        }
    });
}