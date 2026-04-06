"""
Seed script: populates the database with 30+ diverse recipes.
Includes breakfast, lunch, dinner, snacks across various cuisines with full macros.

Run with: python seed_recipes.py
"""
import sys
import os

# Add the backend directory to the path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
from models import Base, Recipe
from schemas import RecipeCreate

# ─── 30+ Recipes ─────────────────────────────────────────────

RECIPES = [
    # ── Breakfast ──
    {
        "name": "Classic Pancakes",
        "description": "Fluffy buttermilk pancakes perfect for a weekend breakfast.",
        "ingredients": ["1 cup flour", "2 tbsp sugar", "1 tsp baking powder", "1 egg", "3/4 cup milk", "2 tbsp melted butter"],
        "steps": ["Mix dry ingredients", "Whisk wet ingredients separately", "Combine wet and dry until just mixed", "Cook on griddle 2-3 min per side"],
        "protein": 8, "fat": 10, "carbs": 45, "calories": 300,
        "prep_time": 10, "cook_time": 15, "servings": 2,
        "tags": ["breakfast", "vegetarian"],
        "cuisine": "American",
    },
    {
        "name": "Avocado Toast with Egg",
        "description": "Trendy and nutritious breakfast with creamy avocado and a fried egg.",
        "ingredients": ["2 slices sourdough bread", "1 ripe avocado", "2 eggs", "salt and pepper", "red pepper flakes", "lemon juice"],
        "steps": ["Toast the bread", "Mash avocado with lemon juice, salt, and pepper", "Fry eggs to your liking", "Spread avocado on toast, top with egg and red pepper flakes"],
        "protein": 14, "fat": 22, "carbs": 30, "calories": 370,
        "prep_time": 5, "cook_time": 5, "servings": 1,
        "tags": ["breakfast", "vegetarian", "high-protein"],
        "cuisine": "American",
    },
    {
        "name": "Greek Yogurt Parfait",
        "description": "Layered yogurt with granola and fresh berries.",
        "ingredients": ["1 cup Greek yogurt", "1/4 cup granola", "1/2 cup mixed berries", "1 tbsp honey", "1 tbsp chia seeds"],
        "steps": ["Layer yogurt in a glass", "Add granola layer", "Add berries", "Drizzle with honey and sprinkle chia seeds"],
        "protein": 18, "fat": 8, "carbs": 35, "calories": 280,
        "prep_time": 5, "cook_time": 0, "servings": 1,
        "tags": ["breakfast", "vegetarian", "high-protein", "quick"],
        "cuisine": "Mediterranean",
    },
    {
        "name": "Veggie Omelette",
        "description": "Fluffy 3-egg omelette loaded with fresh vegetables.",
        "ingredients": ["3 eggs", "1/4 cup bell peppers diced", "1/4 cup mushrooms sliced", "2 tbsp spinach", "2 tbsp cheese shredded", "1 tbsp butter", "salt and pepper"],
        "steps": ["Beat eggs with salt and pepper", "Sauté veggies in butter until soft", "Pour eggs into hot pan", "Add veggies and cheese to one half", "Fold and cook 1 more minute"],
        "protein": 22, "fat": 18, "carbs": 5, "calories": 270,
        "prep_time": 5, "cook_time": 8, "servings": 1,
        "tags": ["breakfast", "keto", "low_carb", "high-protein", "vegetarian"],
        "cuisine": "French",
    },
    {
        "name": "Overnight Oats",
        "description": "No-cook oats soaked overnight with your favorite toppings.",
        "ingredients": ["1/2 cup rolled oats", "1/2 cup milk", "1 tbsp chia seeds", "1 tbsp maple syrup", "1/4 cup berries", "1 tbsp almond butter"],
        "steps": ["Mix oats, milk, chia seeds, and maple syrup in a jar", "Refrigerate overnight", "Top with berries and almond butter in the morning"],
        "protein": 12, "fat": 10, "carbs": 48, "calories": 330,
        "prep_time": 5, "cook_time": 0, "servings": 1,
        "tags": ["breakfast", "vegan", "vegetarian", "quick"],
        "cuisine": "American",
    },
    {
        "name": "Breakfast Burrito",
        "description": "Hearty burrito with scrambled eggs, beans, and salsa.",
        "ingredients": ["2 large tortillas", "3 eggs scrambled", "1/4 cup black beans", "2 tbsp salsa", "2 tbsp cheese", "1/4 avocado sliced", "salt and pepper"],
        "steps": ["Scramble eggs with salt and pepper", "Warm tortillas", "Layer eggs, beans, salsa, cheese, and avocado", "Roll up tightly"],
        "protein": 24, "fat": 20, "carbs": 38, "calories": 430,
        "prep_time": 5, "cook_time": 10, "servings": 1,
        "tags": ["breakfast", "high-protein"],
        "cuisine": "Mexican",
    },
    {
        "name": "Smoothie Bowl",
        "description": "Thick blended smoothie topped with fresh fruits and seeds.",
        "ingredients": ["1 frozen banana", "1/2 cup frozen berries", "1/4 cup almond milk", "1 tbsp granola", "1 tbsp coconut flakes", "1 tsp honey"],
        "steps": ["Blend banana, berries, and almond milk until thick", "Pour into a bowl", "Top with granola, coconut flakes, and honey"],
        "protein": 6, "fat": 8, "carbs": 52, "calories": 290,
        "prep_time": 5, "cook_time": 0, "servings": 1,
        "tags": ["breakfast", "vegan", "vegetarian", "quick"],
        "cuisine": "American",
    },

    # ── Lunch ──
    {
        "name": "Grilled Chicken Caesar Salad",
        "description": "Classic Caesar with grilled chicken breast and crisp romaine.",
        "ingredients": ["200g chicken breast", "1 head romaine lettuce", "2 tbsp Caesar dressing", "2 tbsp parmesan shaved", "1/4 cup croutons", "lemon wedge"],
        "steps": ["Season and grill chicken 6 min per side", "Chop romaine", "Toss with dressing and croutons", "Slice chicken on top", "Shave parmesan over"],
        "protein": 38, "fat": 16, "carbs": 18, "calories": 370,
        "prep_time": 10, "cook_time": 15, "servings": 1,
        "tags": ["lunch", "high-protein", "low_carb"],
        "cuisine": "Italian",
    },
    {
        "name": "Tom Yum Soup",
        "description": "Spicy and sour Thai soup with shrimp and mushrooms.",
        "ingredients": ["200g shrimp peeled", "1 cup mushrooms sliced", "2 stalks lemongrass", "3 kaffir lime leaves", "2 tbsp fish sauce", "1 tbsp lime juice", "1 tsp chili paste", "1 cup chicken broth"],
        "steps": ["Boil broth with lemongrass and lime leaves", "Add mushrooms and cook 3 min", "Add shrimp and cook until pink", "Season with fish sauce, lime juice, and chili paste"],
        "protein": 24, "fat": 4, "carbs": 12, "calories": 180,
        "prep_time": 10, "cook_time": 15, "servings": 2,
        "tags": ["lunch", "low_carb", "dairy-free"],
        "cuisine": "Thai",
    },
    {
        "name": "Mediterranean Quinoa Bowl",
        "description": "Protein-packed quinoa with roasted vegetables and feta.",
        "ingredients": ["1 cup cooked quinoa", "1/2 cup cherry tomatoes", "1/4 cup cucumber diced", "2 tbsp kalamata olives", "2 tbsp feta crumbled", "1 tbsp olive oil", "1 tsp oregano"],
        "steps": ["Cook quinoa according to package", "Dice vegetables", "Combine quinoa with vegetables, olives, and feta", "Drizzle with olive oil and oregano"],
        "protein": 14, "fat": 12, "carbs": 42, "calories": 330,
        "prep_time": 10, "cook_time": 20, "servings": 1,
        "tags": ["lunch", "vegetarian", "mediterranean", "high-protein"],
        "cuisine": "Mediterranean",
    },
    {
        "name": "Turkey Club Sandwich",
        "description": "Triple-decker sandwich with turkey, bacon, lettuce, and tomato.",
        "ingredients": ["3 slices bread toasted", "100g turkey breast sliced", "2 strips bacon cooked", "2 lettuce leaves", "3 tomato slices", "1 tbsp mayo", "1 tsp mustard"],
        "steps": ["Toast bread", "Spread mayo and mustard", "Layer turkey, bacon, lettuce, and tomato", "Stack into triple decker", "Secure with toothpicks and cut"],
        "protein": 28, "fat": 18, "carbs": 32, "calories": 400,
        "prep_time": 10, "cook_time": 5, "servings": 1,
        "tags": ["lunch", "high-protein"],
        "cuisine": "American",
    },
    {
        "name": "Chicken Stir-Fry",
        "description": "Quick wok-fried chicken with colorful vegetables in soy-ginger sauce.",
        "ingredients": ["200g chicken breast sliced", "1 cup broccoli florets", "1/2 bell pepper sliced", "1/2 carrot julienned", "2 tbsp soy sauce", "1 tbsp sesame oil", "1 tsp ginger grated", "1 clove garlic minced", "1 cup rice cooked"],
        "steps": ["Heat sesame oil in wok", "Stir-fry chicken until golden", "Add vegetables and cook 3 min", "Add soy sauce, ginger, and garlic", "Serve over rice"],
        "protein": 35, "fat": 12, "carbs": 48, "calories": 440,
        "prep_time": 10, "cook_time": 12, "servings": 1,
        "tags": ["lunch", "dinner", "high-protein", "dairy-free"],
        "cuisine": "Asian",
    },
    {
        "name": "Lentil Soup",
        "description": "Hearty vegan lentil soup with warming spices.",
        "ingredients": ["1 cup red lentils", "1 onion diced", "2 carrots diced", "2 cloves garlic", "1 can diced tomatoes", "4 cups vegetable broth", "1 tsp cumin", "1 tsp turmeric", "2 tbsp olive oil"],
        "steps": ["Sauté onion, carrots, and garlic in olive oil", "Add cumin and turmeric, cook 1 min", "Add lentils, tomatoes, and broth", "Simmer 25 min until lentils are soft", "Season to taste"],
        "protein": 18, "fat": 8, "carbs": 52, "calories": 350,
        "prep_time": 10, "cook_time": 30, "servings": 4,
        "tags": ["lunch", "dinner", "vegan", "vegetarian", "dairy-free"],
        "cuisine": "Middle Eastern",
    },
    {
        "name": "Tuna Poke Bowl",
        "description": "Hawaiian-style raw tuna bowl with rice and fresh toppings.",
        "ingredients": ["200g sushi-grade tuna cubed", "1 cup sushi rice cooked", "1/2 avocado sliced", "1/4 cup edamame", "2 tbsp soy sauce", "1 tsp sesame oil", "1 tbsp sesame seeds", "nori sheets"],
        "steps": ["Marinate tuna in soy sauce and sesame oil for 10 min", "Place rice in bowl", "Arrange tuna, avocado, and edamame on top", "Sprinkle sesame seeds and serve with nori"],
        "protein": 32, "fat": 14, "carbs": 42, "calories": 420,
        "prep_time": 15, "cook_time": 0, "servings": 1,
        "tags": ["lunch", "high-protein", "dairy-free"],
        "cuisine": "Hawaiian",
    },

    # ── Dinner ──
    {
        "name": "Grilled Salmon with Asparagus",
        "description": "Omega-3 rich salmon fillet with roasted asparagus and lemon.",
        "ingredients": ["200g salmon fillet", "1 bunch asparagus", "2 tbsp olive oil", "1 lemon sliced", "2 cloves garlic minced", "salt and pepper", "1 tsp dill"],
        "steps": ["Preheat oven to 400°F", "Place salmon and asparagus on baking sheet", "Drizzle with olive oil, garlic, salt, and pepper", "Top with lemon slices and dill", "Bake 15-18 min"],
        "protein": 34, "fat": 22, "carbs": 8, "calories": 370,
        "prep_time": 10, "cook_time": 18, "servings": 1,
        "tags": ["dinner", "keto", "low_carb", "high-protein", "paleo"],
        "cuisine": "American",
    },
    {
        "name": "Chicken Tikka Masala",
        "description": "Creamy and aromatic Indian curry with tender chicken pieces.",
        "ingredients": ["300g chicken thigh cubed", "1/2 cup yogurt", "1 can coconut milk", "2 tbsp tikka masala paste", "1 onion diced", "2 cloves garlic", "1 tbsp ginger grated", "2 tbsp tomato paste", "fresh cilantro", "1 cup basmati rice"],
        "steps": ["Marinate chicken in yogurt and tikka paste 30 min", "Sauté onion, garlic, and ginger", "Add chicken and cook until browned", "Add coconut milk and tomato paste", "Simmer 20 min", "Serve over rice with cilantro"],
        "protein": 36, "fat": 24, "carbs": 42, "calories": 520,
        "prep_time": 15, "cook_time": 30, "servings": 2,
        "tags": ["dinner", "high-protein"],
        "cuisine": "Indian",
    },
    {
        "name": "Beef Tacos",
        "description": "Seasoned ground beef in crispy shells with fresh toppings.",
        "ingredients": ["200g ground beef", "4 taco shells", "1/4 cup lettuce shredded", "2 tbsp tomato diced", "2 tbsp cheese shredded", "2 tbsp sour cream", "1 tbsp taco seasoning", "salsa"],
        "steps": ["Brown ground beef in a pan", "Add taco seasoning and water per package", "Warm taco shells", "Fill with beef and toppings", "Top with salsa and sour cream"],
        "protein": 28, "fat": 22, "carbs": 28, "calories": 420,
        "prep_time": 10, "cook_time": 15, "servings": 2,
        "tags": ["dinner", "high-protein"],
        "cuisine": "Mexican",
    },
    {
        "name": "Spaghetti Bolognese",
        "description": "Classic Italian meat sauce over al dente spaghetti.",
        "ingredients": ["200g spaghetti", "200g ground beef", "1 can crushed tomatoes", "1 onion diced", "2 cloves garlic", "1 carrot diced", "1 tbsp olive oil", "1 tsp oregano", "1 tsp basil", "parmesan"],
        "steps": ["Cook spaghetti per package directions", "Sauté onion, carrot, and garlic in olive oil", "Add ground beef and brown", "Add tomatoes, oregano, and basil", "Simmer 20 min", "Serve over pasta with parmesan"],
        "protein": 30, "fat": 16, "carbs": 58, "calories": 500,
        "prep_time": 10, "cook_time": 30, "servings": 2,
        "tags": ["dinner", "high-protein"],
        "cuisine": "Italian",
    },
    {
        "name": "Tofu Curry",
        "description": "Creamy coconut curry with crispy tofu and vegetables.",
        "ingredients": ["300g firm tofu cubed", "1 can coconut milk", "2 tbsp red curry paste", "1 bell pepper sliced", "1 cup bamboo shoots", "1 tbsp soy sauce", "1 tsp sugar", "Thai basil", "1 cup jasmine rice"],
        "steps": ["Press and cube tofu, pan-fry until crispy", "Heat curry paste in a pot", "Add coconut milk and bring to simmer", "Add tofu, bell pepper, and bamboo shoots", "Season with soy sauce and sugar", "Serve over rice with Thai basil"],
        "protein": 20, "fat": 22, "carbs": 38, "calories": 430,
        "prep_time": 15, "cook_time": 20, "servings": 2,
        "tags": ["dinner", "vegan", "vegetarian", "dairy-free"],
        "cuisine": "Thai",
    },
    {
        "name": "Mushroom Risotto",
        "description": "Creamy Arborio rice with mixed mushrooms and parmesan.",
        "ingredients": ["1 cup Arborio rice", "200g mixed mushrooms", "4 cups vegetable broth warm", "1/2 cup white wine", "1 onion diced", "2 cloves garlic", "3 tbsp butter", "3 tbsp parmesan", "2 tbsp olive oil", "fresh thyme"],
        "steps": ["Sauté mushrooms in olive oil until golden, set aside", "Cook onion and garlic in butter", "Add rice and toast 2 min", "Add wine and stir until absorbed", "Add broth one ladle at a time, stirring constantly", "Fold in mushrooms, parmesan, and thyme"],
        "protein": 12, "fat": 16, "carbs": 58, "calories": 420,
        "prep_time": 10, "cook_time": 35, "servings": 2,
        "tags": ["dinner", "vegetarian"],
        "cuisine": "Italian",
    },
    {
        "name": "BBQ Pulled Pork",
        "description": "Slow-cooked pork shoulder in smoky BBQ sauce.",
        "ingredients": ["500g pork shoulder", "1/2 cup BBQ sauce", "1 onion sliced", "2 cloves garlic", "1 tbsp smoked paprika", "1 tbsp brown sugar", "1 tsp garlic powder", "4 burger buns", "coleslaw"],
        "steps": ["Rub pork with paprika, brown sugar, garlic powder, salt, and pepper", "Sear in a Dutch oven", "Add onion, garlic, and 1/4 cup BBQ sauce", "Cover and cook at 300°F for 3 hours", "Shred pork with forks", "Mix with remaining BBQ sauce", "Serve on buns with coleslaw"],
        "protein": 34, "fat": 20, "carbs": 36, "calories": 460,
        "prep_time": 15, "cook_time": 180, "servings": 4,
        "tags": ["dinner", "high-protein"],
        "cuisine": "American",
    },
    {
        "name": "Shrimp Pad Thai",
        "description": "Classic Thai stir-fried rice noodles with shrimp and peanuts.",
        "ingredients": ["200g rice noodles", "200g shrimp peeled", "2 eggs", "1/4 cup bean sprouts", "2 green onions sliced", "2 tbsp peanuts crushed", "3 tbsp pad thai sauce", "1 tbsp fish sauce", "1 tbsp lime juice", "1 clove garlic"],
        "steps": ["Soak rice noodles in warm water 30 min", "Make sauce: mix pad thai sauce, fish sauce, and lime juice", "Stir-fry garlic and shrimp", "Push aside, scramble eggs", "Add noodles and sauce, toss", "Top with bean sprouts, green onions, and peanuts"],
        "protein": 26, "fat": 12, "carbs": 48, "calories": 410,
        "prep_time": 15, "cook_time": 10, "servings": 2,
        "tags": ["dinner", "high-protein", "dairy-free"],
        "cuisine": "Thai",
    },
    {
        "name": "Keto Steak with Broccoli",
        "description": "Pan-seared ribeye with buttery roasted broccoli.",
        "ingredients": ["250g ribeye steak", "1 head broccoli cut into florets", "2 tbsp butter", "2 cloves garlic minced", "1 tbsp olive oil", "salt and pepper", "1 tsp rosemary"],
        "steps": ["Season steak generously with salt and pepper", "Heat olive oil in cast iron until smoking", "Sear steak 4 min per side for medium-rare", "Rest steak 5 min", "Roast broccoli with butter, garlic, and rosemary at 400°F for 15 min"],
        "protein": 42, "fat": 32, "carbs": 10, "calories": 500,
        "prep_time": 10, "cook_time": 20, "servings": 1,
        "tags": ["dinner", "keto", "low_carb", "high-protein", "paleo"],
        "cuisine": "American",
    },
    {
        "name": "Vegetable Lasagna",
        "description": "Layered pasta with ricotta, spinach, and marinara sauce.",
        "ingredients": ["9 lasagna noodles", "2 cups ricotta", "2 cups spinach", "2 cups marinara sauce", "1 cup mozzarella shredded", "1/2 cup parmesan", "1 egg", "2 cloves garlic", "1 tbsp olive oil", "Italian seasoning"],
        "steps": ["Cook noodles per package", "Mix ricotta with egg, spinach, garlic, and parmesan", "Spread sauce in baking dish", "Layer noodles, ricotta mixture, and mozzarella", "Repeat layers", "Bake at 375°F for 40 min"],
        "protein": 24, "fat": 18, "carbs": 42, "calories": 420,
        "prep_time": 20, "cook_time": 40, "servings": 6,
        "tags": ["dinner", "vegetarian"],
        "cuisine": "Italian",
    },
    {
        "name": "Chicken Fajitas",
        "description": "Sizzling chicken with peppers and onions in warm tortillas.",
        "ingredients": ["300g chicken breast sliced", "2 bell peppers sliced", "1 onion sliced", "4 flour tortillas", "2 tbsp fajita seasoning", "2 tbsp olive oil", "sour cream", "salsa", "guacamole"],
        "steps": ["Season chicken with fajita seasoning", "Heat oil in a skillet", "Cook chicken until browned, set aside", "Sauté peppers and onions", "Return chicken to pan", "Serve in warm tortillas with toppings"],
        "protein": 36, "fat": 16, "carbs": 32, "calories": 420,
        "prep_time": 10, "cook_time": 15, "servings": 2,
        "tags": ["dinner", "high-protein"],
        "cuisine": "Mexican",
    },
    {
        "name": "Japanese Ramen",
        "description": "Rich tonkotsu-style broth with noodles, egg, and chashu pork.",
        "ingredients": ["2 packs ramen noodles", "4 cups pork broth", "200g chashu pork sliced", "2 soft-boiled eggs", "2 green onions sliced", "1 sheet nori", "1 tbsp soy sauce", "1 tsp sesame oil", "corn kernels", "bean sprouts"],
        "steps": ["Prepare broth with soy sauce and sesame oil", "Cook noodles per package", "Divide noodles into bowls", "Pour hot broth over noodles", "Top with chashu, halved egg, green onions, nori, corn, and bean sprouts"],
        "protein": 28, "fat": 18, "carbs": 48, "calories": 470,
        "prep_time": 15, "cook_time": 20, "servings": 2,
        "tags": ["dinner", "high-protein"],
        "cuisine": "Japanese",
    },

    # ── Snacks / Sides ──
    {
        "name": "Hummus with Veggie Sticks",
        "description": "Creamy homemade hummus with fresh vegetable dippers.",
        "ingredients": ["1 can chickpeas drained", "2 tbsp tahini", "2 tbsp lemon juice", "1 clove garlic", "2 tbsp olive oil", "1 carrot cut into sticks", "1 cucumber cut into sticks", "paprika"],
        "steps": ["Blend chickpeas, tahini, lemon juice, garlic, and olive oil until smooth", "Season with salt and paprika", "Serve with carrot and cucumber sticks"],
        "protein": 8, "fat": 12, "carbs": 28, "calories": 240,
        "prep_time": 10, "cook_time": 0, "servings": 2,
        "tags": ["snack", "vegan", "vegetarian", "quick"],
        "cuisine": "Middle Eastern",
    },
    {
        "name": "Energy Balls",
        "description": "No-bake protein balls with oats, peanut butter, and chocolate chips.",
        "ingredients": ["1 cup rolled oats", "1/2 cup peanut butter", "1/3 cup honey", "1/4 cup mini chocolate chips", "2 tbsp chia seeds", "1 tsp vanilla extract"],
        "steps": ["Mix all ingredients in a bowl", "Refrigerate 30 min", "Roll into 1-inch balls", "Store in the fridge up to 1 week"],
        "protein": 6, "fat": 10, "carbs": 22, "calories": 190,
        "prep_time": 10, "cook_time": 0, "servings": 12,
        "tags": ["snack", "vegetarian", "quick"],
        "cuisine": "American",
    },
    {
        "name": "Guacamole with Chips",
        "description": "Fresh mashed avocado dip with lime and cilantro.",
        "ingredients": ["2 ripe avocados", "1/4 cup red onion diced", "1 jalapeño minced", "2 tbsp cilantro chopped", "1 tbsp lime juice", "salt", "tortilla chips"],
        "steps": ["Halve and mash avocados", "Mix in onion, jalapeño, cilantro, and lime juice", "Season with salt", "Serve with tortilla chips"],
        "protein": 3, "fat": 16, "carbs": 18, "calories": 220,
        "prep_time": 10, "cook_time": 0, "servings": 4,
        "tags": ["snack", "vegan", "vegetarian", "keto", "quick"],
        "cuisine": "Mexican",
    },
    {
        "name": "Caprese Salad",
        "description": "Simple Italian salad with tomato, mozzarella, and basil.",
        "ingredients": ["2 large tomatoes sliced", "200g fresh mozzarella sliced", "fresh basil leaves", "2 tbsp extra virgin olive oil", "1 tbsp balsamic glaze", "salt and pepper"],
        "steps": ["Arrange alternating slices of tomato and mozzarella on a plate", "Tuck basil leaves between slices", "Drizzle with olive oil and balsamic glaze", "Season with salt and pepper"],
        "protein": 14, "fat": 18, "carbs": 8, "calories": 240,
        "prep_time": 10, "cook_time": 0, "servings": 2,
        "tags": ["snack", "vegetarian", "keto", "low_carb", "quick"],
        "cuisine": "Italian",
    },
    {
        "name": "Trail Mix",
        "description": "Custom mix of nuts, seeds, and dried fruit for on-the-go energy.",
        "ingredients": ["1/4 cup almonds", "1/4 cup cashews", "2 tbsp pumpkin seeds", "2 tbsp dried cranberries", "2 tbsp dark chocolate chips", "1 tbsp coconut flakes"],
        "steps": ["Combine all ingredients in a bowl", "Portion into snack bags", "Store in an airtight container"],
        "protein": 8, "fat": 18, "carbs": 20, "calories": 270,
        "prep_time": 5, "cook_time": 0, "servings": 2,
        "tags": ["snack", "vegan", "vegetarian", "quick"],
        "cuisine": "American",
    },
    {
        "name": "Edamame",
        "description": "Steamed soybeans with sea salt — a simple high-protein snack.",
        "ingredients": ["300g frozen edamame in pods", "1 tsp sea salt", "1 tsp sesame oil"],
        "steps": ["Boil edamame for 4-5 min", "Drain and toss with sesame oil and salt", "Serve warm"],
        "protein": 16, "fat": 8, "carbs": 12, "calories": 190,
        "prep_time": 2, "cook_time": 5, "servings": 2,
        "tags": ["snack", "vegan", "vegetarian", "high-protein", "quick"],
        "cuisine": "Japanese",
    },
]


def seed_database():
    """Create all tables and insert recipes if the database is empty."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if recipes already exist
        existing = db.query(Recipe).count()
        if existing > 0:
            print(f"Database already has {existing} recipes. Skipping seed.")
            return

        # Insert all recipes
        for recipe_data in RECIPES:
            recipe = Recipe(**recipe_data)
            db.add(recipe)

        db.commit()
        print(f"✅ Successfully seeded {len(RECIPES)} recipes!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
