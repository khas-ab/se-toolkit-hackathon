import React, { useState, useEffect } from "react";
import { api } from "../api";
import WeeklyCalendar from "./WeeklyCalendar";
import NutritionChart from "./NutritionChart";
import ShoppingListModal from "./ShoppingListModal";

/**
 * Recipe Browser & Planner (Tab 1).
 * Contains:
 *  - Ingredient filter panel
 *  - Recipe search/filter controls
 *  - Recipe cards grid
 *  - Weekly calendar
 *  - Nutrition chart
 *  - Shopping list modal
 */
export default function RecipeBrowser({
  ingredients,
  mealPlans,
  activePlan,
  shoppingList,
  preferences,
  setPreferences,
  onRefresh,
  refreshIngredients,
  refreshMealPlans,
  refreshShoppingList,
}) {
  // Filter state
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [maxCalories, setMaxCalories] = useState(600);
  const [maxPrepTime, setMaxPrepTime] = useState(30);
  const [dietType, setDietType] = useState("none");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIngredients, setSelectedIngredients] = useState([]);

  // Modal state
  const [showShoppingModal, setShowShoppingModal] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [planMessage, setPlanMessage] = useState("");

  // Ingredient input
  const [newIngredient, setNewIngredient] = useState("");
  const [addingIngredient, setAddingIngredient] = useState(false);
  const [ingredientError, setIngredientError] = useState("");
  const [ingredientSuccess, setIngredientSuccess] = useState("");

  // Load recipes on mount and when filters change
  useEffect(() => {
    loadRecipes();
  }, [maxCalories, maxPrepTime, dietType, searchQuery]);

  async function loadRecipes() {
    setLoading(true);
    try {
      const params = {
        max_calories: maxCalories || undefined,
        max_prep_time: maxPrepTime || undefined,
        diet_type: dietType !== "none" ? dietType : undefined,
        search: searchQuery || undefined,
        limit: 50,
      };
      const data = await api.getRecipes(params);
      setRecipes(data);
    } catch (err) {
      console.error("Failed to load recipes:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddIngredient() {
    if (!newIngredient.trim()) return;
    setAddingIngredient(true);
    setIngredientError("");
    setIngredientSuccess("");
    try {
      const name = newIngredient.trim();
      console.log("Adding ingredient:", name);
      const result = await api.addIngredient(name);
      console.log("Ingredient added:", result);
      setNewIngredient("");
      setIngredientSuccess(`✅ Added "${result.name}"`);
      // Clear success message after 3 seconds
      setTimeout(() => setIngredientSuccess(""), 3000);
      await refreshIngredients();
    } catch (err) {
      console.error("Failed to add ingredient:", err);
      setIngredientError(`Error: ${err.message}. Is the backend running?`);
    } finally {
      setAddingIngredient(false);
    }
  }

  async function handleRemoveIngredient(id) {
    try {
      await api.removeIngredient(id);
      refreshIngredients();
    } catch (err) {
      console.error(err);
    }
  }

  async function handleSuggest() {
    if (ingredients.length === 0) {
      alert("Add some ingredients first!");
      return;
    }
    setLoading(true);
    try {
      const data = await api.suggestRecipes({
        ingredients: ingredients.map((i) => i.name),
        max_calories: maxCalories || undefined,
        max_prep_time: maxPrepTime || undefined,
        diet_type: dietType !== "none" ? dietType : undefined,
      });
      setRecipes(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddToPlan(recipeId, day, mealType) {
    setPlanMessage("");
    try {
      let plan = activePlan;
      if (!plan) {
        // Create a plan first
        plan = await api.generateMealPlan();
        setPlanMessage(`✅ Created new plan "${plan.name}"`);
        setTimeout(() => setPlanMessage(""), 3000);
      }
      // Add the entry
      await api.addMealPlanEntry(plan.id, recipeId, day, mealType);
      setPlanMessage(`✅ Added to ${day} ${mealType}`);
      setTimeout(() => setPlanMessage(""), 3000);
      await refreshMealPlans();
    } catch (err) {
      console.error("Failed to add to plan:", err);
      setPlanMessage(`❌ Error: ${err.message}`);
      setTimeout(() => setPlanMessage(""), 5000);
    }
  }

  async function handleGeneratePlan() {
    try {
      await api.generateMealPlan();
      refreshMealPlans();
    } catch (err) {
      console.error(err);
    }
  }

  async function handleGenerateShoppingList() {
    if (!activePlan) {
      alert("Generate a meal plan first!");
      return;
    }
    try {
      await api.generateShoppingList(activePlan.id);
      refreshShoppingList();
      setShowShoppingModal(true);
    } catch (err) {
      console.error(err);
    }
  }

  async function handleSavePreferences() {
    try {
      await api.updatePreferences(preferences);
      setShowPreferences(false);
    } catch (err) {
      console.error(err);
    }
  }

  const days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
  const mealTypes = ["breakfast", "lunch", "dinner"];

  return (
    <div className="space-y-6">
      {/* Top Controls Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Ingredient Panel */}
        <div className="bg-white rounded-xl shadow p-4">
          <h3 className="font-semibold text-green-800 mb-2">🥬 My Ingredients</h3>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newIngredient}
              onChange={(e) => { setNewIngredient(e.target.value); setIngredientError(""); setIngredientSuccess(""); }}
              onKeyDown={(e) => e.key === "Enter" && handleAddIngredient()}
              placeholder="Add ingredient..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
            <button
              onClick={handleAddIngredient}
              disabled={addingIngredient || !newIngredient.trim()}
              className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed min-w-[60px]"
            >
              {addingIngredient ? "..." : "Add"}
            </button>
          </div>
          {ingredientError && (
            <div className="mb-2 px-3 py-2 bg-red-50 text-red-700 rounded-lg text-xs border border-red-200">
              ⚠️ {ingredientError}
            </div>
          )}
          {ingredientSuccess && (
            <div className="mb-2 px-3 py-2 bg-green-50 text-green-700 rounded-lg text-xs border border-green-200">
              {ingredientSuccess}
            </div>
          )}
          <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
            {ingredients.map((ing) => (
              <span
                key={ing.id}
                className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs"
              >
                {ing.name}
                <button
                  onClick={() => handleRemoveIngredient(ing.id)}
                  className="text-green-600 hover:text-red-500 ml-1"
                >
                  ×
                </button>
              </span>
            ))}
            {ingredients.length === 0 && (
              <span className="text-xs text-gray-400">No ingredients added yet</span>
            )}
          </div>
          <button
            onClick={handleSuggest}
            className="mt-2 w-full px-3 py-2 bg-emerald-100 text-emerald-700 rounded-lg text-sm hover:bg-emerald-200 font-medium"
          >
            ✨ Suggest Recipes
          </button>
        </div>

        {/* Filter Panel */}
        <div className="bg-white rounded-xl shadow p-4">
          <h3 className="font-semibold text-green-800 mb-2">🔍 Filters</h3>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-600">Search</label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search recipes..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600">
                Max Calories: {maxCalories}
              </label>
              <input
                type="range"
                min="100"
                max="1000"
                step="50"
                value={maxCalories}
                onChange={(e) => setMaxCalories(Number(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600">
                Max Prep Time: {maxPrepTime} min
              </label>
              <input
                type="range"
                min="5"
                max="60"
                step="5"
                value={maxPrepTime}
                onChange={(e) => setMaxPrepTime(Number(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600">Diet Type</label>
              <select
                value={dietType}
                onChange={(e) => setDietType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
              >
                <option value="none">All</option>
                <option value="keto">Keto</option>
                <option value="vegan">Vegan</option>
                <option value="vegetarian">Vegetarian</option>
                <option value="paleo">Paleo</option>
                <option value="low_carb">Low Carb</option>
                <option value="mediterranean">Mediterranean</option>
              </select>
            </div>
          </div>
        </div>

        {/* Actions Panel */}
        <div className="bg-white rounded-xl shadow p-4">
          <h3 className="font-semibold text-green-800 mb-2">⚡ Quick Actions</h3>
          {planMessage && (
            <div className={`mb-2 px-3 py-2 rounded-lg text-xs border ${
              planMessage.startsWith("❌")
                ? "bg-red-50 text-red-700 border-red-200"
                : "bg-green-50 text-green-700 border-green-200"
            }`}>
              {planMessage}
            </div>
          )}
          <div className="space-y-2">
            <button
              onClick={handleGeneratePlan}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 font-medium"
            >
              📅 Generate Weekly Plan
            </button>
            <button
              onClick={() => setShowShoppingModal(true)}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 font-medium"
            >
              🛒 View Shopping List ({shoppingList.length})
            </button>
            <button
              onClick={handleGenerateShoppingList}
              className="w-full px-4 py-2 bg-orange-600 text-white rounded-lg text-sm hover:bg-orange-700 font-medium"
            >
              🔄 Generate from Plan
            </button>
            <button
              onClick={() => setShowPreferences(true)}
              className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg text-sm hover:bg-gray-700 font-medium"
            >
              ⚙️ Preferences
            </button>
          </div>
        </div>
      </div>

      {/* Recipe Cards Grid */}
      <div>
        <h2 className="text-xl font-bold text-green-800 mb-3">
          🍳 Recipes ({recipes.length})
        </h2>
        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading recipes...</div>
        ) : recipes.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No recipes found. Try adjusting your filters or add ingredients.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {recipes.map((recipe) => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                onAddToPlan={handleAddToPlan}
                days={days}
                mealTypes={mealTypes}
              />
            ))}
          </div>
        )}
      </div>

      {/* Weekly Calendar */}
      {activePlan && (
        <WeeklyCalendar
          plan={activePlan}
          onRefresh={refreshMealPlans}
          onAddToPlan={handleAddToPlan}
          recipes={recipes}
        />
      )}

      {/* Nutrition Chart */}
      {activePlan && <NutritionChart planId={activePlan.id} />}

      {/* Shopping List Modal */}
      {showShoppingModal && (
        <ShoppingListModal
          items={shoppingList}
          onClose={() => setShowShoppingModal(false)}
          onUpdate={refreshShoppingList}
        />
      )}

      {/* Preferences Modal */}
      {showPreferences && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-bold text-green-800 mb-4">⚙️ Dietary Preferences</h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-600">Daily Calorie Target</label>
                <input
                  type="number"
                  value={preferences.daily_calorie_target}
                  onChange={(e) =>
                    setPreferences({ ...preferences, daily_calorie_target: Number(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="text-sm text-gray-600">Diet Type</label>
                <select
                  value={preferences.diet_type}
                  onChange={(e) =>
                    setPreferences({ ...preferences, diet_type: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="none">None</option>
                  <option value="keto">Keto</option>
                  <option value="vegan">Vegan</option>
                  <option value="vegetarian">Vegetarian</option>
                  <option value="paleo">Paleo</option>
                  <option value="low_carb">Low Carb</option>
                  <option value="mediterranean">Mediterranean</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-gray-600">Daily Protein Target (g)</label>
                <input
                  type="number"
                  value={preferences.protein_target}
                  onChange={(e) =>
                    setPreferences({ ...preferences, protein_target: Number(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleSavePreferences}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Save
              </button>
              <button
                onClick={() => setShowPreferences(false)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Individual recipe card component.
 * Shows name, macros, tags, and an "Add to Plan" dropdown.
 */
function RecipeCard({ recipe, onAddToPlan, days, mealTypes }) {
  const [showPlanMenu, setShowPlanMenu] = useState(false);

  return (
    <div className="bg-white rounded-xl shadow hover:shadow-lg transition-shadow">
      {/* Image placeholder */}
      <div className="h-32 bg-gradient-to-br from-green-200 to-emerald-300 rounded-t-xl flex items-center justify-center overflow-hidden">
        <span className="text-4xl">🍽️</span>
      </div>

      <div className="p-4">
        <h3 className="font-semibold text-gray-900 truncate">{recipe.name}</h3>
        {recipe.cuisine && (
          <span className="text-xs text-gray-500">{recipe.cuisine}</span>
        )}

        {/* Macros */}
        <div className="grid grid-cols-4 gap-1 mt-2 text-center">
          <div className="bg-red-50 rounded p-1">
            <div className="text-xs font-bold text-red-600">{Math.round(recipe.calories)}</div>
            <div className="text-[10px] text-red-400">cal</div>
          </div>
          <div className="bg-blue-50 rounded p-1">
            <div className="text-xs font-bold text-blue-600">{Math.round(recipe.protein)}g</div>
            <div className="text-[10px] text-blue-400">protein</div>
          </div>
          <div className="bg-yellow-50 rounded p-1">
            <div className="text-xs font-bold text-yellow-600">{Math.round(recipe.fat)}g</div>
            <div className="text-[10px] text-yellow-400">fat</div>
          </div>
          <div className="bg-green-50 rounded p-1">
            <div className="text-xs font-bold text-green-600">{Math.round(recipe.carbs)}g</div>
            <div className="text-[10px] text-green-400">carbs</div>
          </div>
        </div>

        {/* Tags */}
        {recipe.tags && recipe.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {recipe.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-[10px]"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Prep time */}
        <div className="text-xs text-gray-500 mt-2">
          ⏱️ {recipe.prep_time}min prep · {recipe.cook_time}min cook
        </div>

        {/* Add to Plan button with dropdown */}
        <div className="relative mt-2">
          <button
            onClick={() => setShowPlanMenu(!showPlanMenu)}
            className="w-full px-3 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700"
          >
            + Add to Plan
          </button>
          {showPlanMenu && (
            <div className="absolute z-50 right-0 bottom-full mb-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 max-h-48 overflow-y-auto">
              {days.map((day) =>
                mealTypes.map((meal) => (
                  <button
                    key={`${day}-${meal}`}
                    onClick={() => {
                      onAddToPlan(recipe.id, day, meal);
                      setShowPlanMenu(false);
                    }}
                    className="w-full text-left px-3 py-1.5 text-xs hover:bg-green-50 capitalize"
                  >
                    {day} {meal}
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
