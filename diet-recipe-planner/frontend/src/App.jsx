import React, { useState, useEffect } from "react";
import RecipeBrowser from "./components/RecipeBrowser";
import AgentChat from "./components/AgentChat";
import { api } from "./api";

/**
 * Main application component with tab-based navigation.
 * Tab 1: Recipe Browser & Planner (Version 1)
 * Tab 2: AI Agent Chat (Version 2)
 *
 * Shared state (ingredients, meal plans) is lifted here
 * so both tabs stay in sync.
 */
export default function App() {
  const [activeTab, setActiveTab] = useState("planner");
  const [ingredients, setIngredients] = useState([]);
  const [mealPlans, setMealPlans] = useState([]);
  const [activePlan, setActivePlan] = useState(null);
  const [shoppingList, setShoppingList] = useState([]);
  const [preferences, setPreferences] = useState({
    daily_calorie_target: 2000,
    diet_type: "none",
    allergies: [],
    protein_target: 0,
    excluded_ingredients: [],
  });

  // Load initial data on mount
  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [ings, plans, shopping, prefs] = await Promise.all([
        api.getIngredients().catch(() => []),
        api.getMealPlans().catch(() => []),
        api.getShoppingList().catch(() => []),
        api.getPreferences().catch(() => ({})),
      ]);
      setIngredients(ings);
      setMealPlans(plans);
      setShoppingList(shopping);
      if (prefs && prefs.id) setPreferences(prefs);
      // Set the most recent plan as active
      if (plans.length > 0) {
        const fullPlan = await api.getMealPlan(plans[0].id).catch(() => null);
        setActivePlan(fullPlan);
      }
    } catch (err) {
      console.error("Failed to load data:", err);
    }
  }

  // Refresh helpers — passed down to child components
  const refreshIngredients = async () => {
    try {
      const ings = await api.getIngredients();
      setIngredients(ings);
    } catch (err) {
      console.error(err);
    }
  };

  const refreshMealPlans = async () => {
    try {
      const plans = await api.getMealPlans();
      setMealPlans(plans);
      if (plans.length > 0) {
        // Always refresh the most recent plan to get latest entries
        const fullPlan = await api.getMealPlan(plans[0].id);
        setActivePlan(fullPlan);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const refreshShoppingList = async () => {
    try {
      const list = await api.getShoppingList();
      setShoppingList(list);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-green-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🍽️</span>
              <div>
                <h1 className="text-2xl font-bold text-green-800">Diet Recipe Planner</h1>
                <p className="text-sm text-green-600">Plan meals, discover recipes, chat with AI</p>
              </div>
            </div>
            {/* Quick stats */}
            <div className="hidden md:flex items-center gap-4 text-sm text-gray-600">
              <span>🥘 {ingredients.length} ingredients</span>
              <span>📅 {mealPlans.length} plan(s)</span>
              <span>🛒 {shoppingList.length} items</span>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-white border-b border-green-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1">
            <button
              onClick={() => setActiveTab("planner")}
              className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                activeTab === "planner"
                  ? "border-green-500 text-green-700"
                  : "border-transparent text-gray-500 hover:text-green-600"
              }`}
            >
              📋 Recipe Browser & Planner
            </button>
            <button
              onClick={() => setActiveTab("chat")}
              className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                activeTab === "chat"
                  ? "border-green-500 text-green-700"
                  : "border-transparent text-gray-500 hover:text-green-600"
              }`}
            >
              🤖 AI Agent Chat
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === "planner" ? (
          <RecipeBrowser
            ingredients={ingredients}
            mealPlans={mealPlans}
            activePlan={activePlan}
            shoppingList={shoppingList}
            preferences={preferences}
            setPreferences={setPreferences}
            onRefresh={loadData}
            refreshIngredients={refreshIngredients}
            refreshMealPlans={refreshMealPlans}
            refreshShoppingList={refreshShoppingList}
          />
        ) : (
          <AgentChat
            ingredients={ingredients}
            activePlan={activePlan}
            refreshIngredients={refreshIngredients}
            refreshMealPlans={refreshMealPlans}
            refreshShoppingList={refreshShoppingList}
          />
        )}
      </main>
    </div>
  );
}
