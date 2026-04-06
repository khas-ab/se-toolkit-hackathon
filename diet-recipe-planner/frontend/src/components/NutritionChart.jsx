import React, { useState, useEffect } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";
import { api } from "../api";

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

/**
 * Nutrition Chart component.
 * Shows weekly nutrition breakdown as bar and doughnut charts.
 * Updates when the meal plan changes.
 */
export default function NutritionChart({ planId }) {
  const [nutrition, setNutrition] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (planId) {
      api.getNutrition(planId).then((data) => {
        setNutrition(data);
        setLoading(false);
      }).catch(() => setLoading(false));
    }
  }, [planId]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow p-4">
        <div className="text-center py-8 text-gray-500">Loading nutrition data...</div>
      </div>
    );
  }

  if (!nutrition || !nutrition.daily_breakdown || nutrition.daily_breakdown.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow p-4">
        <div className="text-center py-8 text-gray-500">
          No nutrition data available. Add meals to your plan first.
        </div>
      </div>
    );
  }

  const days = nutrition.daily_breakdown.map((d) => d.day.charAt(0).toUpperCase() + d.day.slice(1, 3));

  // Bar chart data: daily macros
  const barData = {
    labels: days,
    datasets: [
      {
        label: "Calories",
        data: nutrition.daily_breakdown.map((d) => Math.round(d.calories)),
        backgroundColor: "rgba(239, 68, 68, 0.7)",
        borderColor: "rgba(239, 68, 68, 1)",
        borderWidth: 1,
      },
      {
        label: "Protein (g)",
        data: nutrition.daily_breakdown.map((d) => Math.round(d.protein)),
        backgroundColor: "rgba(59, 130, 246, 0.7)",
        borderColor: "rgba(59, 130, 246, 1)",
        borderWidth: 1,
      },
      {
        label: "Fat (g)",
        data: nutrition.daily_breakdown.map((d) => Math.round(d.fat)),
        backgroundColor: "rgba(234, 179, 8, 0.7)",
        borderColor: "rgba(234, 179, 8, 1)",
        borderWidth: 1,
      },
      {
        label: "Carbs (g)",
        data: nutrition.daily_breakdown.map((d) => Math.round(d.carbs)),
        backgroundColor: "rgba(34, 197, 94, 0.7)",
        borderColor: "rgba(34, 197, 94, 1)",
        borderWidth: 1,
      },
    ],
  };

  const barOptions = {
    responsive: true,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Daily Nutrition Breakdown" },
    },
    scales: {
      y: { beginAtZero: true },
    },
  };

  // Doughnut chart data: macro distribution (totals)
  const doughnutData = {
    labels: ["Protein", "Fat", "Carbs"],
    datasets: [
      {
        data: [
          Math.round(nutrition.total_protein),
          Math.round(nutrition.total_fat),
          Math.round(nutrition.total_carbs),
        ],
        backgroundColor: [
          "rgba(59, 130, 246, 0.8)",
          "rgba(234, 179, 8, 0.8)",
          "rgba(34, 197, 94, 0.8)",
        ],
        borderColor: "#fff",
        borderWidth: 2,
      },
    ],
  };

  const doughnutOptions = {
    responsive: true,
    plugins: {
      legend: { position: "bottom" },
      title: { display: true, text: "Weekly Macro Distribution (grams)" },
    },
  };

  return (
    <div className="bg-white rounded-xl shadow p-4">
      <h2 className="text-xl font-bold text-green-800 mb-4">📊 Nutrition Summary</h2>

      {/* Totals Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <div className="bg-red-50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-red-600">{Math.round(nutrition.total_calories)}</div>
          <div className="text-xs text-red-500">Total Calories</div>
        </div>
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-600">{Math.round(nutrition.total_protein)}g</div>
          <div className="text-xs text-blue-500">Total Protein</div>
        </div>
        <div className="bg-yellow-50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-yellow-600">{Math.round(nutrition.total_fat)}g</div>
          <div className="text-xs text-yellow-500">Total Fat</div>
        </div>
        <div className="bg-green-50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-600">{Math.round(nutrition.total_carbs)}g</div>
          <div className="text-xs text-green-500">Total Carbs</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="max-h-72">
          <Bar data={barData} options={barOptions} />
        </div>
        <div className="max-h-72 flex items-center justify-center">
          <div className="w-64">
            <Doughnut data={doughnutData} options={doughnutOptions} />
          </div>
        </div>
      </div>
    </div>
  );
}
