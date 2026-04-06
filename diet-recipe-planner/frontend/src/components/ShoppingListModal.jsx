import React, { useState } from "react";
import { api } from "../api";

/**
 * Shopping List Modal.
 * Shows the current shopping list with checkboxes, categories, and actions.
 * Supports marking items as purchased, deleting items, and copying to clipboard.
 */
export default function ShoppingListModal({ items, onClose, onUpdate }) {
  const [newItemName, setNewItemName] = useState("");
  const [newItemQty, setNewItemQty] = useState("");

  // Group items by category
  const byCategory = {};
  for (const item of items) {
    const cat = item.category || "Other";
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push(item);
  }

  async function togglePurchased(item) {
    try {
      await api.updateShoppingItem(item.id, {
        purchased: item.purchased ? 0 : 1,
      });
      onUpdate();
    } catch (err) {
      console.error(err);
    }
  }

  async function deleteItem(id) {
    try {
      await api.deleteShoppingItem(id);
      onUpdate();
    } catch (err) {
      console.error(err);
    }
  }

  async function addNewItem() {
    if (!newItemName.trim()) return;
    try {
      await api.addShoppingItem(newItemName.trim(), newItemQty.trim());
      setNewItemName("");
      setNewItemQty("");
      onUpdate();
    } catch (err) {
      console.error(err);
    }
  }

  function copyToClipboard() {
    const text = items
      .map((item) => {
        const check = item.purchased ? "✅" : "⬜";
        const qty = item.quantity ? ` (${item.quantity})` : "";
        return `${check} ${item.name}${qty}`;
      })
      .join("\n");

    navigator.clipboard.writeText(text).then(() => {
      alert("Shopping list copied to clipboard!");
    });
  }

  function downloadAsText() {
    const text = items
      .map((item) => {
        const check = item.purchased ? "[x]" : "[ ]";
        const qty = item.quantity ? ` (${item.quantity})` : "";
        return `${check} ${item.name}${qty}`;
      })
      .join("\n");

    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "shopping-list.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-bold text-green-800">🛒 Shopping List</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={copyToClipboard}
              className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              📋 Copy
            </button>
            <button
              onClick={downloadAsText}
              className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              💾 Download
            </button>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-700 rounded-full hover:bg-gray-100"
            >
              ×
            </button>
          </div>
        </div>

        {/* Add new item */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex gap-2">
            <input
              type="text"
              value={newItemName}
              onChange={(e) => setNewItemName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addNewItem()}
              placeholder="Add item..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
            />
            <input
              type="text"
              value={newItemQty}
              onChange={(e) => setNewItemQty(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addNewItem()}
              placeholder="Qty (e.g. 500g)"
              className="w-32 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
            />
            <button
              onClick={addNewItem}
              className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700"
            >
              Add
            </button>
          </div>
        </div>

        {/* Items List */}
        <div className="flex-1 overflow-y-auto p-4">
          {items.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              Shopping list is empty. Generate one from your meal plan!
            </div>
          ) : (
            Object.entries(byCategory).map(([category, categoryItems]) => (
              <div key={category} className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2 capitalize">{category}</h3>
                <div className="space-y-1">
                  {categoryItems.map((item) => (
                    <div
                      key={item.id}
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg group ${
                        item.purchased ? "bg-gray-50" : "bg-white hover:bg-gray-50"
                      }`}
                    >
                      <button
                        onClick={() => togglePurchased(item)}
                        className={`w-5 h-5 rounded border-2 flex items-center justify-center text-xs ${
                          item.purchased
                            ? "bg-green-500 border-green-500 text-white"
                            : "border-gray-300 hover:border-green-500"
                        }`}
                      >
                        {item.purchased ? "✓" : ""}
                      </button>
                      <div className="flex-1">
                        <span
                          className={`text-sm ${
                            item.purchased ? "line-through text-gray-400" : "text-gray-800"
                          }`}
                        >
                          {item.name}
                        </span>
                        {item.quantity && (
                          <span className="text-xs text-gray-500 ml-2">({item.quantity})</span>
                        )}
                      </div>
                      <button
                        onClick={() => deleteItem(item.id)}
                        className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-opacity"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 text-sm text-gray-500">
          {items.filter((i) => i.purchased).length} / {items.length} items purchased
        </div>
      </div>
    </div>
  );
}
