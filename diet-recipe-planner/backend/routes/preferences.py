"""
User preferences API route.
GET /api/preferences - get current preferences
PUT /api/preferences - create or update preferences
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserPreferenceCreate, UserPreferenceResponse
import crud

router = APIRouter(prefix="/api", tags=["preferences"])


@router.get("/preferences", response_model=UserPreferenceResponse)
def get_preferences(db: Session = Depends(get_db)):
    """Get the user's dietary preferences."""
    prefs = crud.get_user_preference(db)
    if not prefs:
        # Return defaults if not set
        return UserPreferenceResponse(
            id=0,
            daily_calorie_target=2000,
            diet_type="none",
            allergies=[],
            protein_target=0,
            excluded_ingredients=[],
        )
    return prefs


@router.put("/preferences", response_model=UserPreferenceResponse)
def update_preferences(data: UserPreferenceCreate, db: Session = Depends(get_db)):
    """Create or update the user's dietary preferences."""
    return crud.create_or_update_preference(db, data)
