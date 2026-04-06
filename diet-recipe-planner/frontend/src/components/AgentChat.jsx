import React, { useState, useRef, useEffect } from "react";
import { api } from "../api";

/**
 * AI Agent Chat (Tab 2).
 * A ChatGPT-like interface where users can ask natural language questions
 * about recipes, meal planning, substitutions, and shopping lists.
 *
 * The backend uses LLM function calling to interpret queries and execute tools.
 */
export default function AgentChat({
  ingredients,
  activePlan,
  refreshIngredients,
  refreshMealPlans,
  refreshShoppingList,
}) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi! 👋 I'm your recipe planning assistant. I can help you find recipes, plan meals, suggest substitutions, and manage your shopping list. What would you like to do?",
      data: null,
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Suggested prompts for quick access
  const suggestedPrompts = [
    "What can I cook with " + (ingredients.length > 0 ? ingredients.slice(0, 3).map((i) => i.name).join(", ") : "eggs and tomatoes") + "?",
    "Plan my week for weight loss",
    "High-protein dinner under 500 cal",
    "No coconut milk, what can I use?",
    "Add eggs to my shopping list",
    "What did I plan for Wednesday?",
  ];

  async function handleSend(query) {
    const userMessage = query || input.trim();
    if (!userMessage || isLoading) return;

    // Add user message to chat
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await api.agentQuery(userMessage);

      // Add assistant response with any structured data
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.response,
          data: response.data,
        },
      ]);

      // Refresh data if the agent modified something
      if (response.data) {
        if (
          response.data.type === "ingredient_added" ||
          response.data.type === "shopping_list"
        ) {
          refreshIngredients();
        }
        if (response.data.type === "meal_plan" || response.data.type === "meal_plan_info") {
          refreshMealPlans();
        }
        if (response.data.type === "shopping_list") {
          refreshShoppingList();
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Sorry, I encountered an error: ${err.message}. Please try again.`,
          data: null,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] min-h-[500px] bg-white rounded-xl shadow-lg overflow-hidden">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🤖</span>
          <div>
            <h2 className="font-bold">AI Recipe Assistant</h2>
            <p className="text-xs text-green-100">
              Powered by LLM function calling
            </p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`message-animate flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-green-600 text-white rounded-br-md"
                  : "bg-white text-gray-800 shadow rounded-bl-md border border-gray-100"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

              {/* Render structured data from agent */}
              {msg.data && <AgentDataRenderer data={msg.data} />}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="message-animate flex justify-start">
            <div className="bg-white rounded-2xl px-4 py-3 shadow rounded-bl-md border border-gray-100">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                </div>
                <span className="text-xs text-gray-500">Thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts */}
      <div className="px-4 py-2 bg-white border-t border-gray-100">
        <div className="flex gap-2 overflow-x-auto pb-1">
          {suggestedPrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              className="flex-shrink-0 px-3 py-1.5 bg-green-50 text-green-700 rounded-full text-xs hover:bg-green-100 transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="px-4 py-3 bg-white border-t border-gray-200">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about recipes, meal plans, or ingredients..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-6 py-3 bg-green-600 text-white rounded-xl text-sm font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

/**
 * Renders structured data from the agent response.
 * Handles recipe cards, substitution lists, shopping items, etc.
 */
function AgentDataRenderer({ data }) {
  if (!data) return null;

  // Recipe cards (single or multiple)
  if (data.type === "recipes" && data.recipes) {
    return (
      <div className="mt-3 space-y-2">
        {data.recipes.slice(0, 3).map((recipe) => (
          <div
            key={recipe.id}
            className="bg-green-50 rounded-lg p-3 border border-green-200"
          >
            <div className="font-medium text-green-900 text-sm">{recipe.name}</div>
            <div className="text-xs text-green-700 mt-1">
              🔥 {Math.round(recipe.calories)} cal · 🥩 {Math.round(recipe.protein)}g protein · ⏱️ {recipe.prep_time}min
            </div>
            <div className="flex flex-wrap gap-1 mt-1">
              {recipe.tags?.slice(0, 3).map((tag) => (
                <span key={tag} className="px-1.5 py-0.5 bg-green-200 text-green-800 rounded text-[10px]">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Single recipe
  if (data.type === "recipe" && data.recipe) {
    const r = data.recipe;
    return (
      <div className="mt-3 bg-green-50 rounded-lg p-3 border border-green-200">
        <div className="font-medium text-green-900 text-sm">{r.name}</div>
        <div className="text-xs text-green-700 mt-1">
          🔥 {Math.round(r.calories)} cal · 🥩 {Math.round(r.protein)}g protein · 🧈 {Math.round(r.fat)}g fat · 🌾 {Math.round(r.carbs)}g carbs
        </div>
        <details className="mt-2">
          <summary className="text-xs text-green-600 cursor-pointer">View ingredients</summary>
          <ul className="text-xs text-green-800 mt-1 list-disc list-inside">
            {r.ingredients?.map((ing, i) => (
              <li key={i}>{ing}</li>
            ))}
          </ul>
        </details>
      </div>
    );
  }

  // Substitutions
  if (data.type === "substitutions") {
    return (
      <div className="mt-3 bg-yellow-50 rounded-lg p-3 border border-yellow-200">
        <div className="text-xs font-medium text-yellow-800">
          Alternatives for {data.missing_ingredient}:
        </div>
        <div className="flex flex-wrap gap-1 mt-1">
          {data.substitutions?.map((sub, i) => (
            <span key={i} className="px-2 py-1 bg-yellow-200 text-yellow-800 rounded text-xs">
              {sub}
            </span>
          ))}
        </div>
      </div>
    );
  }

  // Shopping list items added
  if (data.type === "shopping_list" && data.items) {
    return (
      <div className="mt-3 bg-purple-50 rounded-lg p-3 border border-purple-200">
        <div className="text-xs font-medium text-purple-800">Added to shopping list:</div>
        <ul className="text-xs text-purple-700 mt-1 list-disc list-inside">
          {data.items.map((item) => (
            <li key={item.id}>
              {item.name} {item.quantity ? `(${item.quantity})` : ""}
            </li>
          ))}
        </ul>
      </div>
    );
  }

  // Ingredient added
  if (data.type === "ingredient_added") {
    return (
      <div className="mt-3 bg-blue-50 rounded-lg p-3 border border-blue-200">
        <div className="text-xs text-blue-800">
          ✅ Added "{data.name}" to your pantry
          {data.quantity ? ` (${data.quantity})` : ""}
        </div>
      </div>
    );
  }

  // Meal plan info
  if (data.type === "meal_plan_info" && data.entries) {
    const entries = data.entries;
    const keys = Object.keys(entries);
    if (keys.length === 0) {
      return (
        <div className="mt-3 text-xs text-gray-500 italic">
          {data.message || "No entries found."}
        </div>
      );
    }

    // Detect structure: day-filtered = {meal_type: recipe}, full = {day: {meal_type: recipe}}
    const firstVal = entries[keys[0]];
    const isDayFiltered = firstVal && typeof firstVal === "object" && "name" in firstVal;

    return (
      <div className="mt-3 bg-indigo-50 rounded-lg p-3 border border-indigo-200">
        <div className="text-xs font-medium text-indigo-800">📅 {data.plan_name || "Your Plan"}</div>
        {isDayFiltered ? (
          // Day-filtered: {meal_type: recipe}
          Object.entries(entries).map(([meal, recipe]) => (
            <div key={meal} className="text-xs text-indigo-600 mt-1 ml-2">
              • {meal}: {recipe.name} ({recipe.calories} cal)
            </div>
          ))
        ) : (
          // Full plan: {day: {meal_type: recipe}}
          keys.map((day) => (
            <div key={day} className="mt-1">
              <div className="text-xs font-medium text-indigo-700 capitalize">{day}</div>
              {Object.entries(entries[day]).map(([meal, recipe]) => (
                <div key={meal} className="text-xs text-indigo-600 ml-2">
                  • {meal}: {recipe.name}
                </div>
              ))}
            </div>
          ))
        )}
      </div>
    );
  }

  return null;
}
