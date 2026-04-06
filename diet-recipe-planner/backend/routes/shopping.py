"""
Shopping list API routes.
GET /api/shopping-list - get all items
POST /api/shopping-list - add an item
PUT /api/shopping-list/{id} - update an item (e.g. mark purchased)
DELETE /api/shopping-list/{id} - remove an item
POST /api/shopping-list/generate/{plan_id} - generate from meal plan
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import (
    ShoppingListItemCreate, ShoppingListItemUpdate, ShoppingListItemResponse,
)
import crud

router = APIRouter(prefix="/api", tags=["shopping-list"])


@router.get("/shopping-list", response_model=List[ShoppingListItemResponse])
def get_shopping_list(db: Session = Depends(get_db)):
    """Get the current shopping list."""
    return crud.get_shopping_list(db)


@router.post("/shopping-list", response_model=ShoppingListItemResponse, status_code=201)
def add_item(data: ShoppingListItemCreate, db: Session = Depends(get_db)):
    """
    Add an item to the shopping list.
    If the item already exists, quantities are aggregated.
    """
    return crud.add_shopping_item(db, data)


@router.put("/shopping-list/{item_id}", response_model=ShoppingListItemResponse)
def update_item(item_id: int, data: ShoppingListItemUpdate, db: Session = Depends(get_db)):
    """Update a shopping list item (e.g. mark as purchased)."""
    item = crud.update_shopping_item(db, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/shopping-list/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """Remove an item from the shopping list."""
    if not crud.delete_shopping_item(db, item_id):
        raise HTTPException(status_code=404, detail="Item not found")


@router.post("/shopping-list/generate/{plan_id}", response_model=List[ShoppingListItemResponse])
def generate_from_plan(plan_id: int, db: Session = Depends(get_db)):
    """
    Generate a shopping list from a meal plan.
    Compares recipe ingredients against user's available ingredients
    and adds only missing items with aggregated quantities.
    """
    plan = crud.get_meal_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return crud.generate_shopping_list_from_plan(db, plan_id)
