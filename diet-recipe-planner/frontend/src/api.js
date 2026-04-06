/**
 * API client wrapper for the Diet Recipe Planner backend.
 * All fetch calls go through this module for consistent error handling.
 */

// Use the same host as the page is served from.
// This works whether accessed via localhost, 10.x.x.x, or any other address.
const API_BASE = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL
  : `${window.location.protocol}//${window.location.hostname}:8000`;

/**
 * Generic fetch wrapper with JSON parsing and error handling.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  // 204 No Content has no body to parse
  if (response.status === 204) {
    return null;
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// ─── Recipes ─────────────────────────────────────────────────

export const api = {
  /** Fetch all recipes with optional filters. */
  getRecipes: (params = {}) => {
    const query = new URLSearchParams();
    if (params.max_calories) query.set("max_calories", params.max_calories);
    if (params.max_prep_time) query.set("max_prep_time", params.max_prep_time);
    if (params.diet_type) query.set("diet_type", params.diet_type);
    if (params.tags) query.set("tags", params.tags);
    if (params.search) query.set("search", params.search);
    if (params.limit) query.set("limit", params.limit);
    return request(`/api/recipes?${query.toString()}`);
  },

  /** Create a new recipe. */
  createRecipe: (data) => request("/api/recipes", { method: "POST", body: JSON.stringify(data) }),

  /** Get a single recipe by ID. */
  getRecipe: (id) => request(`/api/recipes/${id}`),

  /** Suggest recipes based on ingredients and filters. */
  suggestRecipes: (data) => request("/api/suggest", { method: "POST", body: JSON.stringify(data) }),

  // ─── Ingredients ───────────────────────────────────────────

  /** Get user's available ingredients. */
  getIngredients: () => request("/api/ingredients"),

  /** Add an ingredient to user's pantry. */
  addIngredient: (name, quantity = "") =>
    request("/api/ingredients", { method: "POST", body: JSON.stringify({ name, quantity }) }),

  /** Remove an ingredient from user's pantry. */
  removeIngredient: (id) => request(`/api/ingredients/${id}`, { method: "DELETE" }),

  // ─── Meal Plans ────────────────────────────────────────────

  /** Get all meal plans. */
  getMealPlans: () => request("/api/meal-plans"),

  /** Create a new meal plan. */
  createMealPlan: (name = "Weekly Plan") =>
    request("/api/meal-plans", { method: "POST", body: JSON.stringify({ name }) }),

  /** Get a meal plan with entries. */
  getMealPlan: (id) => request(`/api/meal-plans/${id}`),

  /** Add a recipe to a meal plan slot. */
  addMealPlanEntry: (planId, recipeId, day, mealType) =>
    request(`/api/meal-plans/${planId}/entries?recipe_id=${recipeId}&day=${day}&meal_type=${mealType}`, {
      method: "POST",
    }),

  /** Remove a meal plan entry. */
  removeMealPlanEntry: (entryId) => request(`/api/meal-plans/entries/${entryId}`, { method: "DELETE" }),

  /** Auto-generate a weekly meal plan. */
  generateMealPlan: (planName = "Auto-Generated Weekly Plan") =>
    request(`/api/meal-plans/generate?plan_name=${encodeURIComponent(planName)}`, { method: "POST" }),

  /** Get weekly nutrition summary. */
  getNutrition: (planId) => request(`/api/meal-plans/${planId}/nutrition`),

  // ─── Shopping List ─────────────────────────────────────────

  /** Get the shopping list. */
  getShoppingList: () => request("/api/shopping-list"),

  /** Add an item to the shopping list. */
  addShoppingItem: (name, quantity = "", category = "") =>
    request("/api/shopping-list", {
      method: "POST",
      body: JSON.stringify({ name, quantity, category }),
    }),

  /** Update a shopping list item. */
  updateShoppingItem: (id, data) =>
    request(`/api/shopping-list/${id}`, { method: "PUT", body: JSON.stringify(data) }),

  /** Delete a shopping list item. */
  deleteShoppingItem: (id) => request(`/api/shopping-list/${id}`, { method: "DELETE" }),

  /** Generate shopping list from a meal plan. */
  generateShoppingList: (planId) =>
    request(`/api/shopping-list/generate/${planId}`, { method: "POST" }),

  // ─── Preferences ───────────────────────────────────────────

  /** Get user preferences. */
  getPreferences: () => request("/api/preferences"),

  /** Update user preferences. */
  updatePreferences: (data) => request("/api/preferences", { method: "PUT", body: JSON.stringify(data) }),

  // ─── Agent ─────────────────────────────────────────────────

  /** Send a natural language query to the AI agent. */
  agentQuery: (query) =>
    request("/api/agent/query", { method: "POST", body: JSON.stringify({ query }) }),
};

export default api;
