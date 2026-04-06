import React, { useState } from "react";
import { api } from "../api";

/**
 * Weekly Calendar component.
 * Displays a Mon-Sun grid with breakfast/lunch/dinner slots.
 * Each slot shows the assigned recipe or a placeholder to add one.
 */
export default function WeeklyCalendar({ plan, onRefresh, onAddToPlan, recipes }) {
  const days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
  const mealTypes = ["breakfast", "lunch", "dinner"];
  const mealEmojis = { breakfast: "🌅", lunch: "☀️", dinner: "🌙" };

  // Build a lookup: { day: { mealType: entry } }
  const entriesByDay = {};
  for (const entry of plan.entries || []) {
    const day = entry.day;
    const meal = entry.meal_type;
    if (!entriesByDay[day]) entriesByDay[day] = {};
    entriesByDay[day][meal] = entry;
  }

  return (
    <div className="bg-white rounded-xl shadow p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-green-800">📅 {plan.name}</h2>
        <span className="text-sm text-gray-500">{plan.entries?.length || 0} meals planned</span>
      </div>

      {/* Calendar Grid */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="p-2 text-left text-gray-500 font-medium w-20">Meal</th>
              {days.map((day) => (
                <th key={day} className="p-2 text-center text-gray-600 font-medium capitalize">
                  {day.slice(0, 3)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {mealTypes.map((mealType) => (
              <tr key={mealType} className="border-b border-gray-100">
                <td className="p-2 text-gray-600 font-medium capitalize">
                  {mealEmojis[mealType]} {mealType}
                </td>
                {days.map((day) => {
                  const entry = entriesByDay[day]?.[mealType];
                  return (
                    <td key={`${day}-${mealType}`} className="p-1 text-center">
                      {entry?.recipe ? (
                        <MealSlot
                          entry={entry}
                          recipe={entry.recipe}
                          onRemove={() => api.removeMealPlanEntry(entry.id).then(onRefresh)}
                        />
                      ) : (
                        <EmptySlot
                          day={day}
                          mealType={mealType}
                          planId={plan.id}
                          recipes={recipes}
                          onAdd={onRefresh}
                        />
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * A filled meal slot showing the recipe name and a remove button.
 */
function MealSlot({ entry, recipe, onRemove }) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="relative group">
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="w-full px-2 py-1.5 bg-green-100 text-green-800 rounded text-xs hover:bg-green-200 truncate max-w-[120px]"
        title={recipe.name}
      >
        {recipe.name}
      </button>
      <button
        onClick={onRemove}
        className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-[10px] opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
      >
        ×
      </button>

      {/* Tooltip with recipe details */}
      {showDetails && (
        <div className="absolute z-30 left-0 mt-1 w-56 bg-white rounded-lg shadow-xl border border-gray-200 p-3 text-left">
          <div className="font-medium text-sm text-gray-900">{recipe.name}</div>
          <div className="text-xs text-gray-500 mt-1">
            🔥 {Math.round(recipe.calories)} cal · 🥩 {Math.round(recipe.protein)}g protein
          </div>
          <div className="text-xs text-gray-500">
            ⏱️ {recipe.prep_time}min prep · {recipe.cook_time}min cook
          </div>
          {recipe.tags?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {recipe.tags.slice(0, 4).map((tag) => (
                <span key={tag} className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-[10px]">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * An empty meal slot with a dropdown to pick a recipe.
 */
function EmptySlot({ day, mealType, planId, recipes, onAdd }) {
  const [showPicker, setShowPicker] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setShowPicker(!showPicker)}
        className="w-full px-2 py-1.5 bg-gray-50 text-gray-400 rounded text-xs hover:bg-gray-100 border border-dashed border-gray-300"
      >
        + Add
      </button>

      {showPicker && (
        <div className="absolute z-30 left-0 mt-1 w-56 bg-white rounded-lg shadow-xl border border-gray-200 max-h-48 overflow-y-auto">
          {recipes.length === 0 ? (
            <div className="p-3 text-xs text-gray-500">No recipes loaded</div>
          ) : (
            recipes.map((recipe) => (
              <button
                key={recipe.id}
                onClick={async () => {
                  await api.addMealPlanEntry(planId, recipe.id, day, mealType);
                  onAdd();
                  setShowPicker(false);
                }}
                className="w-full text-left px-3 py-2 text-xs hover:bg-green-50 border-b border-gray-100 last:border-0"
              >
                <div className="font-medium text-gray-900">{recipe.name}</div>
                <div className="text-[10px] text-gray-500">
                  🔥 {Math.round(recipe.calories)} cal · ⏱️ {recipe.prep_time}min
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
