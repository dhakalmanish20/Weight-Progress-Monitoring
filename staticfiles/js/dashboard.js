function initializeDashboardCharts(dates, weights, calories, foodData) {
    // Validate input data
    if (!Array.isArray(dates)) {
      console.error('Invalid dates array');
      return;
    }
    if (!Array.isArray(weights) || !Array.isArray(calories)) {
      console.error('Invalid weights or calories array');
      return;
    }
    if (!foodData || !Array.isArray(foodData.labels) || !Array.isArray(foodData.values)) {
      console.error('Invalid foodData object');
      return;
    }
  
    // Weight Chart
    const ctxWeight = document.getElementById('weightChart');
    if (ctxWeight) {
      try {
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
              tooltip: {
                enabled: true,
                mode: 'index',
                intersect: false,
              },
              legend: {
                display: true,
                position: 'bottom',
              },
            },
            scales: {
              x: {
                grid: {
                  display: false,
                },
              },
              y: {
                grid: {
                  color: '#e0e0e0',
                },
              },
            },
          },
        });
      } catch (error) {
        console.error('Weight Chart initialization failed:', error);
      }
    }
  
    // Calorie Chart
    const ctxCalorie = document.getElementById('calorieChart');
    if (ctxCalorie) {
      try {
        new Chart(ctxCalorie, {
          type: 'bar',
          data: {
            labels: dates,
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
              tooltip: {
                enabled: true,
                mode: 'index',
                intersect: false,
              },
              legend: {
                display: true,
                position: 'bottom',
              },
            },
            scales: {
              x: {
                grid: {
                  display: false,
                },
              },
              y: {
                grid: {
                  color: '#e0e0e0',
                },
              },
            },
          },
        });
      } catch (error) {
        console.error('Calorie Chart initialization failed:', error);
      }
    }
  
    // Food Consumption Chart
    const ctxFood = document.getElementById('foodChart');
    if (ctxFood) {
      try {
        new Chart(ctxFood, {
          type: 'doughnut',
          data: {
            labels: foodData.labels,
            datasets: [{
              data: foodData.values,
              backgroundColor: [
                '#FF6384', '#36A2EB', '#FFCE56',
                '#8A2BE2', '#FF4500', '#008080',
                '#FFD700', '#7CFC00', '#FF69B4', '#CD853F',
              ],
              borderWidth: 1,
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              tooltip: {
                enabled: true,
                callbacks: {
                  label: (context) => {
                    const label = context.label || '';
                    const value = context.raw || 0;
                    return `${label}: ${value}%`;
                  },
                },
              },
              legend: {
                display: true,
                position: 'bottom',
              },
            },
          },
        });
      } catch (error) {
        console.error('Food Chart initialization failed:', error);
      }
    }
  }