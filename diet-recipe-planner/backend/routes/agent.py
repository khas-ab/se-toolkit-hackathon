"""
Agent (LLM) API route.
POST /api/agent/query - send a natural language query to the AI agent
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import AgentQueryRequest, AgentQueryResponse
from agent import process_query

router = APIRouter(prefix="/api", tags=["agent"])


@router.post("/agent/query", response_model=AgentQueryResponse)
def agent_query(request: AgentQueryRequest, db: Session = Depends(get_db)):
    """
    Send a natural language query to the AI agent.
    The agent uses LLM function calling to decide which tool to use,
    then executes it and returns a natural language response with structured data.

    Example queries:
    - "I have chicken, broccoli, and rice. What can I make?"
    - "High-protein dinner under 500 calories"
    - "Plan my week for keto"
    - "No almond milk, what can I use?"
    - "Add eggs to my shopping list"
    - "What did I plan for Wednesday?"
    """
    result = process_query(db, request.query)
    return AgentQueryResponse(
        response=result["response"],
        data=result.get("data"),
    )
