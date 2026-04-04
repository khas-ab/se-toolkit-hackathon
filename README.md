### Implementation plan
#### Version 1:
Pure Web Application (FastAPI + React/Vue/HTML)  
This is the classic approach. All the functionality of the Diet Recipe Planner is moved to the browser.  
- Screen 1: Input form for products and goals (calories, diet).  
- Screen 2: List of generated recipes with cards and nutritional information.   
- Screen 3: Weekly food calendar and "Download shopping list" button.  
Plus: It's easy to visualize nutrient graphs (proteins/fats/carbohydrates) using libraries like Chart.js.  
#### Version 2:
Interactive Agent (via Terminal or Web chat)  
I will use NanoBot as the main interface.  
The user communicates with the AI agent directly through the NanoBot web interface (or a custom chat on the website).  
The agent "goes" to your PostgreSQL database, searches for suitable recipes, and provides a text-based response.  
Plus: This looks modern and technologically advanced, as you showcase how the LLM manages your application's data.  
