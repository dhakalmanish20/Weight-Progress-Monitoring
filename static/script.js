// Setup empty dataset initially
const predictedWeights = new Array(6).fill(currentWeight || 70);
// Later, populate predictedWeights with actual values once user logs data

function fetchMeal() {
  // TheMealDB random meal endpoint
  fetch("https://www.themealdb.com/api/json/v1/1/random.php")
    .then((response) => response.json())
    .then((data) => {
      const mealData = data.meals[0];
      const mealContainer = document.getElementById("meal-container");

      const mealHTML = `
          <h5>${mealData.strMeal}</h5>
          <p><strong>Category:</strong> ${mealData.strCategory}</p>
          <p><strong>Cuisine:</strong> ${mealData.strArea}</p>
          <img src="${mealData.strMealThumb}" alt="${mealData.strMeal}" class="img-fluid rounded mb-3" />
          <p><strong>Instructions:</strong> ${mealData.strInstructions}</p>
        `;

      mealContainer.innerHTML = mealHTML;
    })
    .catch((error) => {
      console.error("[ERROR] Fetching meal data:", error);
    });
}

// If there's a chart area on the page:
if (
  typeof predictedWeights !== "undefined" &&
  document.getElementById("weightChart")
) {
  const ctx = document.getElementById("weightChart").getContext("2d");

  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"],
      datasets: [
        {
          label: "Predicted Weight (kg)",
          data: predictedWeights,
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          borderColor: "rgba(54, 162, 235, 1)",
          borderWidth: 2,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        yAxes: [
          {
            ticks: {
              beginAtZero: false,
            },
          },
        ],
      },
    },
  });
}
