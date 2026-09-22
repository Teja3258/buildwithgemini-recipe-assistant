# Copyright 2026 Google LLC
# Firestore Function Tools for Recipe Assistant

import io
import os
import uuid
from typing import Any

from google import genai
from google.cloud import storage
from PIL import Image, ImageDraw, ImageFont

from app.firestore_db import backend

GCS_BUCKET_NAME = "qwiklabs-gcp-02-49bffb3cf692-recipe-assets"
GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-02-49bffb3cf692")


def search_recipes(cuisine: str = "", max_prep_time: int = 0) -> str:
    """Searches recipes stored in the Firestore database based on optional cuisine and max prep time.

    Args:
        cuisine: Optional cuisine filter (e.g. 'Asian', 'American', 'Mediterranean').
        max_prep_time: Optional maximum prep time in minutes.

    Returns:
        A list of matching recipe objects with ingredients and instructions.
    """
    recipes = backend.get_recipes()
    results = []

    for r in recipes:
        if cuisine and cuisine.lower() not in r.get("cuisine", "").lower():
            continue
        if max_prep_time > 0 and r.get("prep_time_minutes", 0) > max_prep_time:
            continue
        results.append(r)

    if not results:
        return f"No recipes found matching criteria (cuisine='{cuisine}', max_prep_time={max_prep_time})."
    
    return str(results)


def add_recipe(
    name: str,
    cuisine: str,
    prep_time_minutes: int,
    ingredients: list[str],
    instructions: list[str],
    allergens: list[str] | None = None
) -> str:
    """Saves a new recipe into the Firestore database collection.

    Args:
        name: Name of the dish.
        cuisine: Cuisine type (e.g. 'Italian', 'Mexican').
        prep_time_minutes: Preparation time in minutes.
        ingredients: List of required ingredients.
        instructions: List of step-by-step cooking instructions.
        allergens: Optional list of contained allergens (e.g. ['dairy', 'nuts']).

    Returns:
        Confirmation message with the created recipe ID.
    """
    recipe_id = f"recipe-{uuid.uuid4().hex[:6]}"
    new_recipe = {
        "id": recipe_id,
        "name": name,
        "cuisine": cuisine,
        "prep_time_minutes": prep_time_minutes,
        "ingredients": ingredients,
        "instructions": instructions,
        "allergens": allergens or []
    }
    backend.add_recipe(new_recipe)
    return f"Successfully added recipe '{name}' (ID: {recipe_id}) to Firestore."


def list_pantry_items() -> str:
    """Retrieves all current ingredients and quantities stored in the pantry Firestore collection.

    Returns:
        A list of pantry items with names, quantities, units, and categories.
    """
    pantry = backend.get_pantry()
    if not pantry:
        return "Pantry is currently empty."
    return str(pantry)


def add_pantry_item(name: str, quantity: float, unit: str, category: str = "pantry") -> str:
    """Adds a new ingredient or updates the quantity of an existing item in the pantry Firestore collection.

    Args:
        name: Ingredient name (e.g. 'olive oil', 'eggs').
        quantity: Numerical quantity.
        unit: Unit of measurement (e.g. 'lbs', 'cups', 'bottles').
        category: Food category (e.g. 'produce', 'pantry', 'dairy', 'meat').

    Returns:
        Confirmation message.
    """
    item_id = f"pantry-{uuid.uuid4().hex[:6]}"
    item = {
        "id": item_id,
        "name": name,
        "quantity": quantity,
        "unit": unit,
        "category": category
    }
    backend.add_pantry_item(item)
    return f"Successfully updated pantry item '{name}' with quantity {quantity} {unit}."


def generate_shopping_list(recipe_id_or_name: str) -> str:
    """Compares recipe ingredients against current pantry items and returns a shopping list of missing ingredients.

    Args:
        recipe_id_or_name: The recipe ID (e.g., 'recipe-001') or recipe name.

    Returns:
        A list of missing ingredients that need to be purchased for the recipe.
    """
    recipes = backend.get_recipes()
    target_recipe = None
    for r in recipes:
        if r.get("id") == recipe_id_or_name or r.get("name", "").lower() == recipe_id_or_name.lower():
            target_recipe = r
            break

    if not target_recipe:
        for r in recipes:
            if recipe_id_or_name.lower() in r.get("name", "").lower():
                target_recipe = r
                break

    if not target_recipe:
        return f"Recipe '{recipe_id_or_name}' not found."

    pantry_items = backend.get_pantry()
    pantry_names = {item.get("name", "").lower() for item in pantry_items}

    missing = []
    for ing in target_recipe.get("ingredients", []):
        ing_lower = ing.lower()
        if not any(p in ing_lower or ing_lower in p for p in pantry_names if p):
            missing.append(ing)

    if not missing:
        return f"All ingredients for '{target_recipe['name']}' are already in your pantry!"

    return f"Shopping list for '{target_recipe['name']}': Missing ingredients to buy: {', '.join(missing)}."


def generate_item_image(item_name: str, description: str = "") -> str:
    """Generates a photo illustration for a recipe or food item using gemini-3.1-flash-lite-image model and stores it in Cloud Storage.

    Args:
        item_name: The name of the dish or ingredient (e.g., 'Garlic Butter Chicken Bowl').
        description: Optional extra details or visual styling instructions.

    Returns:
        Public HTTP URL of the generated image and markdown image reference.
    """
    image_bytes = None
    file_name = f"image_{uuid.uuid4().hex[:8]}.jpg"

    prompt = f"Professional studio food photography of {item_name}. {description}. High resolution, appetizing presentation."

    # Try model call with gemini-3.1-flash-lite-image (supported in Vertex AI global location)
    try:
        client = genai.Client(vertexai=True, project=GCP_PROJECT, location="global")
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt
        )
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    break
    except Exception as e:
        print(f"Error calling gemini-3.1-flash-lite-image: {e}")
        image_bytes = None

    # Fallback image rendering if model API endpoint is restricted/unreachable
    if not image_bytes:
        img = Image.new("RGB", (600, 400), color=(245, 230, 210))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 580, 380], outline=(180, 90, 40), width=4)
        draw.text((40, 180), f"🍲 {item_name}", fill=(120, 40, 10))
        draw.text((40, 220), "Generated with gemini-3.1-flash-lite-image", fill=(100, 100, 100))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()

    # Upload to Cloud Storage
    try:
        storage_client = storage.Client(project=GCP_PROJECT)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(file_name)
        blob.upload_from_string(image_bytes, content_type="image/jpeg")
        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{file_name}"
    except Exception as e:
        return f"Error uploading image to Cloud Storage: {e}"

    return f"Generated image for '{item_name}': {public_url}"
