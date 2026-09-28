"""
One-off generator for the seed dataset used by the app. Run manually with
`python generate_seed.py` if you want to regenerate recipes.json,
shelf_life.json or substitutions.json. The output files are committed, so
this script does not need to run in production.
"""
import json
import os

SHELF_LIFE_DAYS = {
    "produce_leafy": 5,
    "produce_root": 21,
    "produce_fruit": 7,
    "produce_other": 10,
    "dairy": 10,
    "meat": 3,
    "seafood": 2,
    "grain": 365,
    "legume": 365,
    "spice": 730,
    "condiment": 180,
    "bakery": 5,
    "pantry": 270,
    "frozen": 120,
    "egg": 21,
}

SUBSTITUTIONS = {
    "buttermilk": [{"substitute": "milk", "note": "add 1 tbsp lemon juice or vinegar per cup", "compatibility": 0.85}],
    "sour cream": [{"substitute": "greek yogurt", "note": "1:1 swap", "compatibility": 0.9}],
    "greek yogurt": [{"substitute": "sour cream", "note": "1:1 swap", "compatibility": 0.9}],
    "baking powder": [{"substitute": "baking soda", "note": "use 1/3 amount plus an acid like lemon juice", "compatibility": 0.6}],
    "brown sugar": [{"substitute": "white sugar", "note": "add 1 tbsp molasses per cup if available", "compatibility": 0.75}],
    "white sugar": [{"substitute": "brown sugar", "note": "1:1 swap, slightly moister result", "compatibility": 0.85}],
    "heavy cream": [{"substitute": "milk", "note": "add 2 tbsp butter per cup", "compatibility": 0.7}],
    "milk": [{"substitute": "water", "note": "use in savory dishes only, thinner result", "compatibility": 0.4}],
    "butter": [{"substitute": "olive oil", "note": "use 3/4 the amount", "compatibility": 0.7}],
    "olive oil": [{"substitute": "butter", "note": "melt first, use slightly more", "compatibility": 0.7}],
    "white rice": [{"substitute": "brown rice", "note": "longer cook time", "compatibility": 0.85}],
    "brown rice": [{"substitute": "white rice", "note": "shorter cook time", "compatibility": 0.85}],
    "chicken breast": [{"substitute": "chicken thigh", "note": "adjust cook time up slightly", "compatibility": 0.9}],
    "chicken thigh": [{"substitute": "chicken breast", "note": "adjust cook time down slightly", "compatibility": 0.9}],
    "vegetable broth": [{"substitute": "water", "note": "add extra salt and herbs", "compatibility": 0.5}],
    "chicken broth": [{"substitute": "vegetable broth", "note": "1:1 swap", "compatibility": 0.85}],
    "parmesan": [{"substitute": "pecorino romano", "note": "slightly saltier", "compatibility": 0.8}],
    "soy sauce": [{"substitute": "tamari", "note": "1:1 swap, gluten free", "compatibility": 0.95}],
    "lime juice": [{"substitute": "lemon juice", "note": "1:1 swap", "compatibility": 0.85}],
    "lemon juice": [{"substitute": "lime juice", "note": "1:1 swap", "compatibility": 0.85}],
    "cilantro": [{"substitute": "parsley", "note": "milder flavor, no strong swap", "compatibility": 0.5}],
    "white wine": [{"substitute": "chicken broth", "note": "add a splash of vinegar", "compatibility": 0.5}],
    "penne": [{"substitute": "fusilli", "note": "any short pasta works", "compatibility": 0.9}],
    "fusilli": [{"substitute": "penne", "note": "any short pasta works", "compatibility": 0.9}],
    "spaghetti": [{"substitute": "linguine", "note": "any long pasta works", "compatibility": 0.9}],
    "cream cheese": [{"substitute": "greek yogurt", "note": "thinner texture", "compatibility": 0.6}],
    "coconut milk": [{"substitute": "heavy cream", "note": "loses coconut flavor", "compatibility": 0.5}],
    "red onion": [{"substitute": "yellow onion", "note": "milder, less sharp", "compatibility": 0.85}],
    "yellow onion": [{"substitute": "red onion", "note": "slightly sharper flavor", "compatibility": 0.85}],
    "beef broth": [{"substitute": "chicken broth", "note": "lighter flavor", "compatibility": 0.7}],
}

# category assigned per ingredient name, used to assign default shelf life
INGREDIENT_CATEGORY = {
    "chicken breast": "meat", "chicken thigh": "meat", "ground beef": "meat", "beef sirloin": "meat",
    "pork chop": "meat", "bacon": "meat", "shrimp": "seafood", "salmon fillet": "seafood",
    "white fish fillet": "seafood", "tofu": "produce_other", "egg": "egg", "eggs": "egg",
    "milk": "dairy", "butter": "dairy", "heavy cream": "dairy", "sour cream": "dairy",
    "greek yogurt": "dairy", "cream cheese": "dairy", "parmesan": "dairy", "mozzarella": "dairy",
    "cheddar": "dairy", "feta": "dairy", "buttermilk": "dairy",
    "spinach": "produce_leafy", "kale": "produce_leafy", "lettuce": "produce_leafy",
    "cilantro": "produce_leafy", "parsley": "produce_leafy", "basil": "produce_leafy",
    "carrot": "produce_root", "potato": "produce_root", "sweet potato": "produce_root",
    "onion": "produce_root", "red onion": "produce_root", "yellow onion": "produce_root",
    "garlic": "produce_root", "ginger": "produce_root",
    "tomato": "produce_fruit", "cherry tomatoes": "produce_fruit", "lemon": "produce_fruit",
    "lime": "produce_fruit", "avocado": "produce_fruit", "apple": "produce_fruit", "banana": "produce_fruit",
    "bell pepper": "produce_other", "zucchini": "produce_other", "broccoli": "produce_other",
    "cauliflower": "produce_other", "mushroom": "produce_other", "cucumber": "produce_other",
    "green beans": "produce_other", "corn": "produce_other", "cabbage": "produce_other",
    "white rice": "grain", "brown rice": "grain", "spaghetti": "grain", "penne": "grain",
    "fusilli": "grain", "quinoa": "grain", "bread": "bakery", "tortilla": "bakery",
    "flour": "pantry", "sugar": "pantry", "white sugar": "pantry", "brown sugar": "pantry",
    "baking powder": "pantry", "baking soda": "pantry", "black beans": "legume", "chickpeas": "legume",
    "lentils": "legume", "kidney beans": "legume", "olive oil": "pantry", "vegetable oil": "pantry",
    "soy sauce": "condiment", "tamari": "condiment", "vinegar": "condiment", "honey": "pantry",
    "salt": "spice", "black pepper": "spice", "cumin": "spice", "paprika": "spice",
    "chili powder": "spice", "cinnamon": "spice", "oregano": "spice", "thyme": "spice",
    "curry powder": "spice", "red pepper flakes": "spice",
    "vegetable broth": "condiment", "chicken broth": "condiment", "beef broth": "condiment",
    "coconut milk": "pantry", "peanut butter": "pantry", "white wine": "condiment",
}

RECIPES = [
    {
        "title": "Garlic Butter Spaghetti",
        "cuisine": "italian", "tags": "quick,vegetarian,pantry-staple",
        "prep_time_minutes": 20,
        "steps": "1. Boil spaghetti until al dente, reserve 1 cup pasta water.\n2. Melt butter with garlic over low heat until fragrant.\n3. Toss pasta with garlic butter, parmesan, and a splash of pasta water.\n4. Season with salt, pepper, and parsley.",
        "calories": 520, "protein_g": 15, "carbs_g": 70, "fat_g": 18,
        "ingredients": [
            ("spaghetti", 200, "g", False), ("butter", 40, "g", False), ("garlic", 3, "clove", False),
            ("parmesan", 30, "g", False), ("parsley", 5, "g", True), ("salt", 1, "tsp", False),
            ("black pepper", 1, "tsp", False),
        ],
    },
    {
        "title": "Tomato Basil Penne",
        "cuisine": "italian", "tags": "quick,vegetarian",
        "prep_time_minutes": 25,
        "steps": "1. Cook penne until al dente.\n2. Saute garlic and onion, add chopped tomatoes and simmer 10 minutes.\n3. Stir in basil and toss with pasta.\n4. Top with parmesan.",
        "calories": 480, "protein_g": 14, "carbs_g": 78, "fat_g": 10,
        "ingredients": [
            ("penne", 200, "g", False), ("tomato", 3, "unit", False), ("garlic", 2, "clove", False),
            ("yellow onion", 0.5, "unit", False), ("basil", 10, "g", False), ("parmesan", 20, "g", True),
            ("olive oil", 2, "tbsp", False),
        ],
    },
    {
        "title": "Chicken Stir Fry",
        "cuisine": "asian", "tags": "quick,high-protein",
        "prep_time_minutes": 25,
        "steps": "1. Slice chicken thin and stir fry in oil until browned.\n2. Add bell pepper, broccoli, and carrot, stir fry 5 minutes.\n3. Add soy sauce, garlic, and ginger, cook 2 more minutes.\n4. Serve over rice.",
        "calories": 460, "protein_g": 38, "carbs_g": 40, "fat_g": 14,
        "ingredients": [
            ("chicken breast", 300, "g", False), ("bell pepper", 1, "unit", False), ("broccoli", 150, "g", False),
            ("carrot", 1, "unit", True), ("soy sauce", 3, "tbsp", False), ("garlic", 2, "clove", False),
            ("ginger", 1, "tsp", True), ("vegetable oil", 2, "tbsp", False), ("white rice", 150, "g", False),
        ],
    },
    {
        "title": "Beef and Broccoli",
        "cuisine": "asian", "tags": "high-protein",
        "prep_time_minutes": 30,
        "steps": "1. Slice beef thin, marinate in soy sauce for 10 minutes.\n2. Sear beef in a hot pan, set aside.\n3. Stir fry broccoli and garlic, return beef to pan.\n4. Add soy sauce and a splash of broth, toss and serve over rice.",
        "calories": 520, "protein_g": 36, "carbs_g": 42, "fat_g": 20,
        "ingredients": [
            ("beef sirloin", 300, "g", False), ("broccoli", 200, "g", False), ("garlic", 2, "clove", False),
            ("soy sauce", 3, "tbsp", False), ("beef broth", 60, "ml", True), ("white rice", 150, "g", False),
            ("vegetable oil", 2, "tbsp", False),
        ],
    },
    {
        "title": "Vegetable Fried Rice",
        "cuisine": "asian", "tags": "quick,vegetarian,leftover-friendly",
        "prep_time_minutes": 20,
        "steps": "1. Scramble eggs in a hot wok, set aside.\n2. Stir fry carrot, onion, and corn.\n3. Add cold rice, breaking up clumps, stir fry 3 minutes.\n4. Add soy sauce and eggs back in, toss to combine.",
        "calories": 410, "protein_g": 13, "carbs_g": 60, "fat_g": 12,
        "ingredients": [
            ("white rice", 300, "g", False), ("egg", 2, "unit", False), ("carrot", 1, "unit", False),
            ("yellow onion", 0.5, "unit", False), ("corn", 80, "g", True), ("soy sauce", 3, "tbsp", False),
            ("vegetable oil", 2, "tbsp", False),
        ],
    },
    {
        "title": "Shrimp Tacos",
        "cuisine": "mexican", "tags": "quick,seafood",
        "prep_time_minutes": 20,
        "steps": "1. Season shrimp with cumin, chili powder, and salt.\n2. Saute shrimp in oil until pink, about 4 minutes.\n3. Warm tortillas.\n4. Fill tortillas with shrimp, cabbage, and a squeeze of lime.",
        "calories": 390, "protein_g": 28, "carbs_g": 38, "fat_g": 12,
        "ingredients": [
            ("shrimp", 300, "g", False), ("tortilla", 6, "unit", False), ("cabbage", 100, "g", True),
            ("lime", 1, "unit", False), ("cumin", 1, "tsp", False), ("chili powder", 1, "tsp", False),
            ("olive oil", 1, "tbsp", False),
        ],
    },
    {
        "title": "Black Bean Tacos",
        "cuisine": "mexican", "tags": "vegetarian,quick,budget",
        "prep_time_minutes": 15,
        "steps": "1. Warm black beans with cumin and chili powder.\n2. Mash lightly and season with salt.\n3. Warm tortillas.\n4. Fill with beans, avocado, and cilantro.",
        "calories": 360, "protein_g": 14, "carbs_g": 55, "fat_g": 10,
        "ingredients": [
            ("black beans", 300, "g", False), ("tortilla", 6, "unit", False), ("avocado", 1, "unit", True),
            ("cilantro", 5, "g", True), ("cumin", 1, "tsp", False), ("chili powder", 1, "tsp", False),
        ],
    },
    {
        "title": "Chicken Fajitas",
        "cuisine": "mexican", "tags": "high-protein",
        "prep_time_minutes": 30,
        "steps": "1. Slice chicken and bell pepper into strips.\n2. Saute chicken until browned, add pepper and onion.\n3. Season with cumin, chili powder, and paprika.\n4. Serve in tortillas with lime.",
        "calories": 430, "protein_g": 34, "carbs_g": 36, "fat_g": 14,
        "ingredients": [
            ("chicken breast", 300, "g", False), ("bell pepper", 2, "unit", False), ("yellow onion", 1, "unit", False),
            ("tortilla", 6, "unit", False), ("cumin", 1, "tsp", False), ("chili powder", 1, "tsp", False),
            ("paprika", 1, "tsp", True), ("lime", 1, "unit", True), ("olive oil", 2, "tbsp", False),
        ],
    },
    {
        "title": "Classic Beef Chili",
        "cuisine": "american", "tags": "high-protein,batch-cook",
        "prep_time_minutes": 45,
        "steps": "1. Brown ground beef with onion and garlic.\n2. Add kidney beans, tomato, and spices.\n3. Simmer 30 minutes, stirring occasionally.\n4. Season to taste and serve.",
        "calories": 490, "protein_g": 32, "carbs_g": 34, "fat_g": 22,
        "ingredients": [
            ("ground beef", 400, "g", False), ("kidney beans", 300, "g", False), ("tomato", 3, "unit", False),
            ("yellow onion", 1, "unit", False), ("garlic", 2, "clove", False), ("chili powder", 2, "tsp", False),
            ("cumin", 1, "tsp", False),
        ],
    },
    {
        "title": "Lentil Soup",
        "cuisine": "mediterranean", "tags": "vegetarian,budget,batch-cook",
        "prep_time_minutes": 40,
        "steps": "1. Saute onion, carrot, and garlic in oil.\n2. Add lentils, broth, and cumin, bring to a boil.\n3. Simmer 25 minutes until lentils are soft.\n4. Blend partially if a thicker soup is preferred.",
        "calories": 320, "protein_g": 18, "carbs_g": 48, "fat_g": 6,
        "ingredients": [
            ("lentils", 250, "g", False), ("carrot", 2, "unit", False), ("yellow onion", 1, "unit", False),
            ("garlic", 2, "clove", False), ("vegetable broth", 800, "ml", False), ("cumin", 1, "tsp", True),
            ("olive oil", 1, "tbsp", False),
        ],
    },
    {
        "title": "Creamy Tomato Soup",
        "cuisine": "american", "tags": "vegetarian,comfort-food",
        "prep_time_minutes": 30,
        "steps": "1. Saute onion and garlic in butter.\n2. Add tomato and broth, simmer 15 minutes.\n3. Blend until smooth.\n4. Stir in heavy cream and season to taste.",
        "calories": 280, "protein_g": 6, "carbs_g": 22, "fat_g": 18,
        "ingredients": [
            ("tomato", 6, "unit", False), ("yellow onion", 0.5, "unit", False), ("garlic", 1, "clove", False),
            ("vegetable broth", 500, "ml", False), ("heavy cream", 100, "ml", False), ("butter", 20, "g", False),
        ],
    },
    {
        "title": "Chickpea Curry",
        "cuisine": "indian", "tags": "vegetarian,budget,batch-cook",
        "prep_time_minutes": 35,
        "steps": "1. Saute onion, garlic, and ginger in oil.\n2. Add curry powder and cook 1 minute until fragrant.\n3. Add chickpeas, tomato, and coconut milk, simmer 15 minutes.\n4. Serve over rice.",
        "calories": 460, "protein_g": 16, "carbs_g": 55, "fat_g": 18,
        "ingredients": [
            ("chickpeas", 300, "g", False), ("yellow onion", 1, "unit", False), ("garlic", 2, "clove", False),
            ("ginger", 1, "tsp", True), ("curry powder", 2, "tsp", False), ("tomato", 2, "unit", False),
            ("coconut milk", 200, "ml", False), ("white rice", 150, "g", False),
        ],
    },
    {
        "title": "Butter Chicken",
        "cuisine": "indian", "tags": "high-protein,comfort-food",
        "prep_time_minutes": 40,
        "steps": "1. Marinate chicken in yogurt and spices for 10 minutes.\n2. Sear chicken, set aside.\n3. Saute onion, garlic, ginger, add tomato and simmer.\n4. Blend sauce, stir in cream and chicken, simmer 10 minutes.",
        "calories": 540, "protein_g": 36, "carbs_g": 28, "fat_g": 30,
        "ingredients": [
            ("chicken thigh", 400, "g", False), ("greek yogurt", 60, "g", False), ("yellow onion", 1, "unit", False),
            ("garlic", 2, "clove", False), ("ginger", 1, "tsp", False), ("tomato", 3, "unit", False),
            ("heavy cream", 100, "ml", False), ("curry powder", 2, "tsp", False), ("white rice", 150, "g", True),
        ],
    },
    {
        "title": "Baked Salmon with Vegetables",
        "cuisine": "mediterranean", "tags": "high-protein,healthy,quick",
        "prep_time_minutes": 30,
        "steps": "1. Preheat oven to 400F (200C).\n2. Toss zucchini and cherry tomatoes with olive oil and salt.\n3. Place salmon and vegetables on a sheet pan.\n4. Bake 15-18 minutes until salmon flakes easily.",
        "calories": 420, "protein_g": 34, "carbs_g": 10, "fat_g": 26,
        "ingredients": [
            ("salmon fillet", 300, "g", False), ("zucchini", 1, "unit", False), ("cherry tomatoes", 150, "g", False),
            ("olive oil", 2, "tbsp", False), ("lemon", 1, "unit", True), ("salt", 1, "tsp", False),
        ],
    },
    {
        "title": "Pan Seared White Fish with Greens",
        "cuisine": "mediterranean", "tags": "high-protein,healthy,quick",
        "prep_time_minutes": 20,
        "steps": "1. Season fish with salt and pepper.\n2. Sear in butter 3 minutes per side.\n3. Wilt spinach in the same pan with garlic.\n4. Serve fish over greens with a squeeze of lemon.",
        "calories": 340, "protein_g": 32, "carbs_g": 6, "fat_g": 18,
        "ingredients": [
            ("white fish fillet", 300, "g", False), ("spinach", 150, "g", False), ("garlic", 1, "clove", False),
            ("butter", 20, "g", False), ("lemon", 1, "unit", True), ("salt", 1, "tsp", False),
        ],
    },
    {
        "title": "Greek Salad",
        "cuisine": "mediterranean", "tags": "vegetarian,quick,no-cook,healthy",
        "prep_time_minutes": 15,
        "steps": "1. Chop cucumber, tomato, and red onion.\n2. Combine with feta and olives.\n3. Dress with olive oil, lemon juice, and oregano.\n4. Toss and serve.",
        "calories": 260, "protein_g": 8, "carbs_g": 12, "fat_g": 20,
        "ingredients": [
            ("cucumber", 1, "unit", False), ("tomato", 2, "unit", False), ("red onion", 0.25, "unit", False),
            ("feta", 80, "g", False), ("olive oil", 2, "tbsp", False), ("lemon juice", 1, "tbsp", False),
            ("oregano", 1, "tsp", True),
        ],
    },
    {
        "title": "Caprese Salad",
        "cuisine": "italian", "tags": "vegetarian,quick,no-cook",
        "prep_time_minutes": 10,
        "steps": "1. Slice tomato and mozzarella.\n2. Layer alternating slices on a plate.\n3. Tuck basil leaves between slices.\n4. Drizzle with olive oil and season with salt and pepper.",
        "calories": 300, "protein_g": 16, "carbs_g": 8, "fat_g": 22,
        "ingredients": [
            ("tomato", 3, "unit", False), ("mozzarella", 150, "g", False), ("basil", 10, "g", False),
            ("olive oil", 2, "tbsp", False), ("salt", 1, "tsp", False),
        ],
    },
    {
        "title": "Egg Fried Rice",
        "cuisine": "asian", "tags": "quick,vegetarian,budget,leftover-friendly",
        "prep_time_minutes": 15,
        "steps": "1. Scramble eggs, set aside.\n2. Stir fry cold rice in oil until heated through.\n3. Add soy sauce and eggs, toss together.\n4. Garnish with scallion if available.",
        "calories": 380, "protein_g": 12, "carbs_g": 58, "fat_g": 10,
        "ingredients": [
            ("white rice", 300, "g", False), ("egg", 3, "unit", False), ("soy sauce", 2, "tbsp", False),
            ("vegetable oil", 2, "tbsp", False),
        ],
    },
    {
        "title": "Vegetable Omelette",
        "cuisine": "american", "tags": "quick,vegetarian,breakfast,budget",
        "prep_time_minutes": 15,
        "steps": "1. Whisk eggs with salt and pepper.\n2. Saute bell pepper, onion, and mushroom until soft.\n3. Pour eggs over vegetables in a hot pan.\n4. Fold once set and top with cheddar.",
        "calories": 340, "protein_g": 22, "carbs_g": 8, "fat_g": 24,
        "ingredients": [
            ("egg", 3, "unit", False), ("bell pepper", 0.5, "unit", True), ("yellow onion", 0.25, "unit", True),
            ("mushroom", 50, "g", True), ("cheddar", 30, "g", True), ("butter", 10, "g", False),
        ],
    },
    {
        "title": "Chicken Caesar Salad",
        "cuisine": "american", "tags": "high-protein,quick",
        "prep_time_minutes": 20,
        "steps": "1. Season and sear chicken breast, slice thin.\n2. Toss lettuce with parmesan and dressing of choice.\n3. Top with sliced chicken.\n4. Finish with black pepper and extra parmesan.",
        "calories": 400, "protein_g": 36, "carbs_g": 10, "fat_g": 22,
        "ingredients": [
            ("chicken breast", 250, "g", False), ("lettuce", 150, "g", False), ("parmesan", 30, "g", False),
            ("olive oil", 1, "tbsp", False), ("lemon juice", 1, "tbsp", True), ("black pepper", 1, "tsp", False),
        ],
    },
    {
        "title": "Pulled Pork Sandwich",
        "cuisine": "american", "tags": "high-protein,batch-cook",
        "prep_time_minutes": 180,
        "steps": "1. Season pork with paprika, salt, and pepper.\n2. Slow cook with a little broth until falling apart, about 3 hours.\n3. Shred pork with two forks.\n4. Pile onto bread with cabbage slaw.",
        "calories": 560, "protein_g": 38, "carbs_g": 42, "fat_g": 26,
        "ingredients": [
            ("pork chop", 500, "g", False), ("bread", 4, "unit", False), ("cabbage", 150, "g", True),
            ("paprika", 1, "tsp", False), ("chicken broth", 100, "ml", True), ("salt", 1, "tsp", False),
        ],
    },
    {
        "title": "Bacon and Egg Breakfast Hash",
        "cuisine": "american", "tags": "quick,breakfast",
        "prep_time_minutes": 25,
        "steps": "1. Cook bacon until crisp, remove and chop.\n2. Cube and pan fry potato in bacon fat until golden.\n3. Add onion and cook until soft.\n4. Top with fried eggs and bacon.",
        "calories": 520, "protein_g": 24, "carbs_g": 36, "fat_g": 32,
        "ingredients": [
            ("bacon", 100, "g", False), ("potato", 2, "unit", False), ("yellow onion", 0.5, "unit", True),
            ("egg", 2, "unit", False), ("salt", 1, "tsp", False),
        ],
    },
    {
        "title": "Roasted Vegetable Quinoa Bowl",
        "cuisine": "mediterranean", "tags": "vegetarian,healthy,batch-cook",
        "prep_time_minutes": 35,
        "steps": "1. Roast sweet potato, broccoli, and chickpeas with olive oil at 425F (220C) for 25 minutes.\n2. Cook quinoa according to package directions.\n3. Combine quinoa and roasted vegetables in a bowl.\n4. Drizzle with lemon juice and season to taste.",
        "calories": 460, "protein_g": 16, "carbs_g": 70, "fat_g": 14,
        "ingredients": [
            ("quinoa", 150, "g", False), ("sweet potato", 1, "unit", False), ("broccoli", 150, "g", False),
            ("chickpeas", 150, "g", False), ("olive oil", 2, "tbsp", False), ("lemon juice", 1, "tbsp", True),
        ],
    },
    {
        "title": "Peanut Noodles",
        "cuisine": "asian", "tags": "quick,vegetarian,budget",
        "prep_time_minutes": 20,
        "steps": "1. Cook spaghetti until al dente.\n2. Whisk peanut butter, soy sauce, and a splash of water into a sauce.\n3. Toss noodles with sauce and shredded carrot.\n4. Garnish with cilantro.",
        "calories": 480, "protein_g": 16, "carbs_g": 62, "fat_g": 18,
        "ingredients": [
            ("spaghetti", 200, "g", False), ("peanut butter", 60, "g", False), ("soy sauce", 2, "tbsp", False),
            ("carrot", 1, "unit", True), ("cilantro", 5, "g", True),
        ],
    },
    {
        "title": "Mushroom Risotto",
        "cuisine": "italian", "tags": "vegetarian,comfort-food",
        "prep_time_minutes": 40,
        "steps": "1. Saute mushroom in butter, set aside.\n2. Saute onion and garlic, add rice and toast 1 minute.\n3. Add broth a ladle at a time, stirring until absorbed.\n4. Stir in mushroom and parmesan before serving.",
        "calories": 440, "protein_g": 12, "carbs_g": 62, "fat_g": 16,
        "ingredients": [
            ("white rice", 250, "g", False), ("mushroom", 200, "g", False), ("yellow onion", 0.5, "unit", False),
            ("garlic", 1, "clove", False), ("vegetable broth", 800, "ml", False), ("parmesan", 40, "g", False),
            ("butter", 20, "g", False),
        ],
    },
    {
        "title": "Zucchini and Chickpea Stew",
        "cuisine": "mediterranean", "tags": "vegetarian,budget,healthy",
        "prep_time_minutes": 30,
        "steps": "1. Saute onion and garlic in olive oil.\n2. Add zucchini, tomato, and chickpeas.\n3. Simmer 20 minutes with cumin and paprika.\n4. Season to taste and serve with bread.",
        "calories": 340, "protein_g": 14, "carbs_g": 46, "fat_g": 12,
        "ingredients": [
            ("zucchini", 2, "unit", False), ("chickpeas", 300, "g", False), ("tomato", 2, "unit", False),
            ("yellow onion", 1, "unit", False), ("garlic", 2, "clove", False), ("cumin", 1, "tsp", True),
            ("paprika", 1, "tsp", True), ("olive oil", 2, "tbsp", False), ("bread", 2, "unit", True),
        ],
    },
    {
        "title": "Cheesy Baked Cauliflower",
        "cuisine": "american", "tags": "vegetarian,low-carb",
        "prep_time_minutes": 35,
        "steps": "1. Steam or par-boil cauliflower florets until just tender.\n2. Place in a baking dish and top with cheddar.\n3. Bake at 400F (200C) for 15 minutes until bubbly.\n4. Season with salt and pepper before serving.",
        "calories": 260, "protein_g": 14, "carbs_g": 12, "fat_g": 18,
        "ingredients": [
            ("cauliflower", 500, "g", False), ("cheddar", 100, "g", False), ("butter", 15, "g", True),
            ("salt", 1, "tsp", False), ("black pepper", 1, "tsp", False),
        ],
    },
    {
        "title": "Turkey Style Ground Beef Lettuce Wraps",
        "cuisine": "asian", "tags": "low-carb,high-protein,quick",
        "prep_time_minutes": 20,
        "steps": "1. Brown ground beef with garlic and ginger.\n2. Stir in soy sauce and a pinch of chili flakes.\n3. Spoon mixture into lettuce leaves.\n4. Top with shredded carrot and serve.",
        "calories": 380, "protein_g": 28, "carbs_g": 10, "fat_g": 24,
        "ingredients": [
            ("ground beef", 300, "g", False), ("lettuce", 150, "g", False), ("garlic", 2, "clove", False),
            ("ginger", 1, "tsp", True), ("soy sauce", 2, "tbsp", False), ("carrot", 1, "unit", True),
            ("red pepper flakes", 1, "tsp", True),
        ],
    },
    {
        "title": "Banana Oat Pancakes",
        "cuisine": "american", "tags": "vegetarian,breakfast,quick",
        "prep_time_minutes": 20,
        "steps": "1. Mash banana and whisk with eggs and milk.\n2. Stir in flour and baking powder until just combined.\n3. Cook spoonfuls of batter on a buttered griddle.\n4. Flip once bubbles form, cook until golden.",
        "calories": 360, "protein_g": 12, "carbs_g": 52, "fat_g": 12,
        "ingredients": [
            ("banana", 2, "unit", False), ("egg", 2, "unit", False), ("milk", 100, "ml", False),
            ("flour", 150, "g", False), ("baking powder", 1, "tsp", False), ("butter", 15, "g", False),
        ],
    },
    {
        "title": "Apple Cinnamon Oatmeal",
        "cuisine": "american", "tags": "vegetarian,breakfast,quick,budget",
        "prep_time_minutes": 15,
        "steps": "1. Bring milk to a simmer.\n2. Stir in oats and diced apple.\n3. Cook 5 minutes, stirring occasionally.\n4. Sweeten with honey and dust with cinnamon.",
        "calories": 310, "protein_g": 9, "carbs_g": 55, "fat_g": 6,
        "ingredients": [
            ("apple", 1, "unit", False), ("milk", 250, "ml", False), ("cinnamon", 1, "tsp", False),
            ("honey", 1, "tbsp", True),
        ],
    },
    {
        "title": "Avocado Toast with Egg",
        "cuisine": "american", "tags": "vegetarian,quick,breakfast",
        "prep_time_minutes": 10,
        "steps": "1. Toast bread until crisp.\n2. Mash avocado with salt, pepper, and lemon juice.\n3. Fry or poach an egg.\n4. Spread avocado on toast and top with the egg.",
        "calories": 330, "protein_g": 14, "carbs_g": 28, "fat_g": 20,
        "ingredients": [
            ("bread", 2, "unit", False), ("avocado", 1, "unit", False), ("egg", 1, "unit", False),
            ("lemon juice", 1, "tsp", True), ("salt", 1, "tsp", False),
        ],
    },
    {
        "title": "Chicken Noodle Soup",
        "cuisine": "american", "tags": "comfort-food,high-protein",
        "prep_time_minutes": 40,
        "steps": "1. Saute onion and carrot in a large pot.\n2. Add broth and chicken breast, simmer until cooked through.\n3. Shred chicken and return to pot.\n4. Add spaghetti broken into pieces, cook until tender.",
        "calories": 340, "protein_g": 28, "carbs_g": 32, "fat_g": 8,
        "ingredients": [
            ("chicken breast", 300, "g", False), ("carrot", 2, "unit", False), ("yellow onion", 1, "unit", False),
            ("chicken broth", 1000, "ml", False), ("spaghetti", 100, "g", False),
        ],
    },
    {
        "title": "Kale and White Bean Soup",
        "cuisine": "mediterranean", "tags": "vegetarian,healthy,budget",
        "prep_time_minutes": 30,
        "steps": "1. Saute garlic and onion in olive oil.\n2. Add broth and kidney beans, simmer 10 minutes.\n3. Stir in kale and cook until wilted.\n4. Season with salt, pepper, and a squeeze of lemon.",
        "calories": 280, "protein_g": 14, "carbs_g": 38, "fat_g": 8,
        "ingredients": [
            ("kale", 150, "g", False), ("kidney beans", 300, "g", False), ("garlic", 2, "clove", False),
            ("yellow onion", 0.5, "unit", False), ("vegetable broth", 700, "ml", False), ("olive oil", 1, "tbsp", False),
            ("lemon", 0.5, "unit", True),
        ],
    },
    {
        "title": "Stuffed Bell Peppers",
        "cuisine": "american", "tags": "batch-cook,high-protein",
        "prep_time_minutes": 45,
        "steps": "1. Cook rice and mix with browned ground beef, onion, and garlic.\n2. Stuff mixture into halved bell peppers.\n3. Top with cheddar.\n4. Bake at 375F (190C) for 25 minutes.",
        "calories": 430, "protein_g": 26, "carbs_g": 34, "fat_g": 20,
        "ingredients": [
            ("bell pepper", 4, "unit", False), ("ground beef", 300, "g", False), ("white rice", 150, "g", False),
            ("yellow onion", 0.5, "unit", False), ("garlic", 1, "clove", False), ("cheddar", 60, "g", True),
        ],
    },
    {
        "title": "Shakshuka",
        "cuisine": "mediterranean", "tags": "vegetarian,breakfast,budget",
        "prep_time_minutes": 30,
        "steps": "1. Saute onion, garlic, and bell pepper in olive oil.\n2. Add tomato and paprika, simmer 10 minutes.\n3. Make wells in the sauce and crack eggs into them.\n4. Cover and cook until eggs are just set.",
        "calories": 320, "protein_g": 16, "carbs_g": 18, "fat_g": 20,
        "ingredients": [
            ("egg", 4, "unit", False), ("tomato", 4, "unit", False), ("bell pepper", 1, "unit", False),
            ("yellow onion", 1, "unit", False), ("garlic", 2, "clove", False), ("paprika", 1, "tsp", False),
            ("olive oil", 2, "tbsp", False),
        ],
    },
    {
        "title": "Cucumber Yogurt Salad",
        "cuisine": "mediterranean", "tags": "vegetarian,no-cook,quick,healthy",
        "prep_time_minutes": 10,
        "steps": "1. Dice cucumber and combine with greek yogurt.\n2. Add minced garlic and a drizzle of olive oil.\n3. Season with salt and pepper.\n4. Chill before serving.",
        "calories": 150, "protein_g": 10, "carbs_g": 10, "fat_g": 8,
        "ingredients": [
            ("cucumber", 1, "unit", False), ("greek yogurt", 200, "g", False), ("garlic", 1, "clove", True),
            ("olive oil", 1, "tbsp", True), ("salt", 1, "tsp", False),
        ],
    },
    {
        "title": "Sweet Potato Black Bean Bowl",
        "cuisine": "mexican", "tags": "vegetarian,budget,healthy,batch-cook",
        "prep_time_minutes": 35,
        "steps": "1. Roast cubed sweet potato with cumin and chili powder at 400F (200C) for 25 minutes.\n2. Warm black beans.\n3. Combine sweet potato and beans in a bowl.\n4. Top with avocado and lime juice.",
        "calories": 420, "protein_g": 14, "carbs_g": 66, "fat_g": 12,
        "ingredients": [
            ("sweet potato", 2, "unit", False), ("black beans", 300, "g", False), ("avocado", 1, "unit", True),
            ("lime juice", 1, "tbsp", True), ("cumin", 1, "tsp", False), ("chili powder", 1, "tsp", False),
        ],
    },
    {
        "title": "Honey Garlic Salmon",
        "cuisine": "asian", "tags": "high-protein,quick",
        "prep_time_minutes": 20,
        "steps": "1. Whisk honey, soy sauce, and minced garlic into a glaze.\n2. Sear salmon skin side down, flip.\n3. Pour glaze over salmon and simmer 2 minutes.\n4. Serve over rice with the pan sauce.",
        "calories": 460, "protein_g": 34, "carbs_g": 32, "fat_g": 20,
        "ingredients": [
            ("salmon fillet", 300, "g", False), ("honey", 2, "tbsp", False), ("soy sauce", 2, "tbsp", False),
            ("garlic", 2, "clove", False), ("white rice", 150, "g", True),
        ],
    },
    {
        "title": "Pork Chop with Roasted Potatoes",
        "cuisine": "american", "tags": "high-protein,comfort-food",
        "prep_time_minutes": 40,
        "steps": "1. Season pork chops with paprika, salt, and pepper.\n2. Roast potato wedges with olive oil at 425F (220C) for 20 minutes.\n3. Sear pork chops 4 minutes per side.\n4. Rest pork chops before serving with potatoes.",
        "calories": 520, "protein_g": 36, "carbs_g": 36, "fat_g": 24,
        "ingredients": [
            ("pork chop", 2, "unit", False), ("potato", 3, "unit", False), ("paprika", 1, "tsp", False),
            ("olive oil", 2, "tbsp", False), ("salt", 1, "tsp", False),
        ],
    },
    {
        "title": "Broccoli Cheddar Soup",
        "cuisine": "american", "tags": "vegetarian,comfort-food",
        "prep_time_minutes": 35,
        "steps": "1. Saute onion in butter, add broth and broccoli.\n2. Simmer until broccoli is tender, about 10 minutes.\n3. Blend partially for a chunky texture.\n4. Stir in cheddar and heavy cream until melted.",
        "calories": 400, "protein_g": 16, "carbs_g": 20, "fat_g": 28,
        "ingredients": [
            ("broccoli", 300, "g", False), ("cheddar", 100, "g", False), ("yellow onion", 0.5, "unit", False),
            ("vegetable broth", 500, "ml", False), ("heavy cream", 100, "ml", False), ("butter", 20, "g", False),
        ],
    },
]


def build_recipes():
    result = []
    for r in RECIPES:
        ingredients = [
            {"name": name, "category": INGREDIENT_CATEGORY.get(name, "pantry"),
             "quantity": qty, "unit": unit, "optional": opt}
            for name, qty, unit, opt in r["ingredients"]
        ]
        entry = {k: v for k, v in r.items() if k != "ingredients"}
        entry["ingredients"] = ingredients
        result.append(entry)
    return result


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "recipes.json"), "w") as f:
        json.dump(build_recipes(), f, indent=2)
    with open(os.path.join(here, "shelf_life.json"), "w") as f:
        json.dump(SHELF_LIFE_DAYS, f, indent=2)
    with open(os.path.join(here, "substitutions.json"), "w") as f:
        json.dump(SUBSTITUTIONS, f, indent=2)
    print(f"Wrote {len(RECIPES)} recipes.")


if __name__ == "__main__":
    main()
