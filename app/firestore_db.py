# Copyright 2026 Google LLC
# Firestore Backend & Local Storage Provider for Recipe Assistant

import json
import os
import tempfile
from typing import Any

from google.cloud import firestore

SEEDED_RECIPES = [
    {
        "id": "recipe-001",
        "name": "Garlic Butter Chicken Bowl",
        "cuisine": "American",
        "prep_time_minutes": 20,
        "ingredients": ["chicken breast", "broccoli", "rice", "garlic", "butter", "soy sauce"],
        "instructions": [
            "Sear chicken in butter and minced garlic until golden brown.",
            "Steam broccoli until tender-crisp.",
            "Serve cooked chicken and broccoli over warm rice with a splash of soy sauce."
        ],
        "allergens": ["dairy", "soy"]
    },
    {
        "id": "recipe-002",
        "name": "Veggie Stir-Fry Noodles",
        "cuisine": "Asian",
        "prep_time_minutes": 15,
        "ingredients": ["noodles", "broccoli", "carrots", "bell pepper", "soy sauce", "sesame oil"],
        "instructions": [
            "Boil noodles according to package directions.",
            "Stir-fry chopped vegetables in sesame oil until vibrant.",
            "Toss noodles and veggies together with soy sauce."
        ],
        "allergens": ["soy", "sesame", "gluten"]
    },
    {
        "id": "recipe-003",
        "name": "Mediterranean Chickpea Salad",
        "cuisine": "Mediterranean",
        "prep_time_minutes": 10,
        "ingredients": ["chickpeas", "cucumber", "cherry tomatoes", "feta cheese", "olive oil", "lemon juice"],
        "instructions": [
            "Rinse and drain chickpeas.",
            "Dice cucumber and cut cherry tomatoes in half.",
            "Toss all ingredients in a bowl with olive oil, lemon juice, and crumbled feta cheese."
        ],
        "allergens": ["dairy"]
    }
]

SEEDED_PANTRY = [
    {"id": "pantry-001", "name": "chicken breast", "quantity": 2.0, "unit": "lbs", "category": "meat"},
    {"id": "pantry-002", "name": "broccoli", "quantity": 1.0, "unit": "head", "category": "produce"},
    {"id": "pantry-003", "name": "rice", "quantity": 5.0, "unit": "cups", "category": "pantry"},
    {"id": "pantry-004", "name": "soy sauce", "quantity": 1.0, "unit": "bottle", "category": "pantry"},
    {"id": "pantry-005", "name": "garlic", "quantity": 3.0, "unit": "cloves", "category": "produce"},
    {"id": "pantry-006", "name": "butter", "quantity": 1.0, "unit": "stick", "category": "dairy"}
]

LOCAL_DATA_FILE = os.path.join(tempfile.gettempdir(), "pantry_and_recipes.json")


class FirestoreBackend:
    def __init__(self, project_id: str | None = None):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-02-49bffb3cf692")
        self.use_gcp = False
        self.db = None
        self._initialized = False

    def _ensure_init(self):
        if self._initialized:
            return
        try:
            client = firestore.Client(project=self.project_id)
            # Try a shallow read to confirm Firestore database existence
            _ = list(client.collections())
            self.db = client
            self.use_gcp = True
        except Exception:
            self.use_gcp = False
            self._init_local_storage()
        finally:
            self._initialized = True

    def _init_local_storage(self):
        os.makedirs(os.path.dirname(LOCAL_DATA_FILE), exist_ok=True)
        if not os.path.exists(LOCAL_DATA_FILE):
            data = {
                "recipes": SEEDED_RECIPES,
                "pantry_items": SEEDED_PANTRY
            }
            with open(LOCAL_DATA_FILE, "w") as f:
                json.dump(data, f, indent=2)

    def _read_local(self) -> dict[str, list[dict[str, Any]]]:
        self._init_local_storage()
        with open(LOCAL_DATA_FILE, "r") as f:
            return json.load(f)

    def _write_local(self, data: dict[str, list[dict[str, Any]]]):
        os.makedirs(os.path.dirname(LOCAL_DATA_FILE), exist_ok=True)
        with open(LOCAL_DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def get_recipes(self) -> list[dict[str, Any]]:
        self._ensure_init()
        if self.use_gcp and self.db:
            try:
                docs = self.db.collection("recipes").stream()
                recipes = [doc.to_dict() for doc in docs]
                if not recipes:
                    for item in SEEDED_RECIPES:
                        self.db.collection("recipes").document(item["id"]).set(item)
                    return SEEDED_RECIPES
                return recipes
            except Exception:
                return self._read_local()["recipes"]
        else:
            return self._read_local()["recipes"]

    def add_recipe(self, recipe: dict[str, Any]) -> dict[str, Any]:
        self._ensure_init()
        if self.use_gcp and self.db:
            try:
                doc_ref = self.db.collection("recipes").document(recipe["id"])
                doc_ref.set(recipe)
            except Exception:
                data = self._read_local()
                data["recipes"].append(recipe)
                self._write_local(data)
        else:
            data = self._read_local()
            data["recipes"].append(recipe)
            self._write_local(data)
        return recipe

    def get_pantry(self) -> list[dict[str, Any]]:
        self._ensure_init()
        if self.use_gcp and self.db:
            try:
                docs = self.db.collection("pantry_items").stream()
                items = [doc.to_dict() for doc in docs]
                if not items:
                    for item in SEEDED_PANTRY:
                        self.db.collection("pantry_items").document(item["id"]).set(item)
                    return SEEDED_PANTRY
                return items
            except Exception:
                return self._read_local()["pantry_items"]
        else:
            return self._read_local()["pantry_items"]

    def add_pantry_item(self, item: dict[str, Any]) -> dict[str, Any]:
        self._ensure_init()
        if self.use_gcp and self.db:
            try:
                doc_ref = self.db.collection("pantry_items").document(item["id"])
                doc_ref.set(item)
            except Exception:
                data = self._read_local()
                existing = False
                for idx, p in enumerate(data["pantry_items"]):
                    if p["name"].lower() == item["name"].lower():
                        data["pantry_items"][idx]["quantity"] += item["quantity"]
                        existing = True
                        break
                if not existing:
                    data["pantry_items"].append(item)
                self._write_local(data)
        else:
            data = self._read_local()
            existing = False
            for idx, p in enumerate(data["pantry_items"]):
                if p["name"].lower() == item["name"].lower():
                    data["pantry_items"][idx]["quantity"] += item["quantity"]
                    existing = True
                    break
            if not existing:
                data["pantry_items"].append(item)
            self._write_local(data)
        return item


# Singleton backend instance
backend = FirestoreBackend()
