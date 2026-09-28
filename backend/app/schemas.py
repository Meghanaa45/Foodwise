from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    category: str
    default_shelf_life_days: int


class InventoryItemCreate(BaseModel):
    ingredient_name: str
    quantity: float = 1.0
    unit: str = "unit"
    storage_location: str = "pantry"
    purchase_date: Optional[date] = None
    expiry_date: Optional[date] = None


class InventoryItemUpdate(BaseModel):
    quantity: Optional[float] = None
    unit: Optional[str] = None
    storage_location: Optional[str] = None
    expiry_date: Optional[date] = None


class InventoryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ingredient: IngredientOut
    quantity: float
    unit: str
    storage_location: str
    purchase_date: date
    expiry_date: Optional[date]
    days_until_expiry: Optional[int] = None


class RecipeIngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ingredient: IngredientOut
    quantity: float
    unit: str
    optional: bool


class RecipeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    cuisine: str
    tags: str
    prep_time_minutes: int
    steps: str
    calories: Optional[int]
    protein_g: Optional[int]
    carbs_g: Optional[int]
    fat_g: Optional[int]
    ingredients: List[RecipeIngredientOut] = []


class RecommendationOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    recipe: RecipeOut
    score: float
    coverage: float
    expiry_urgency: float
    preference_score: float
    nutrition_fit: float
    missing_ingredients: List[str]
    substitutable: dict
    expiring_ingredients_used: List[str]
    model_used: str


class InteractionCreate(BaseModel):
    recipe_id: int
    action: str  # viewed | cooked | skipped | rated
    rating: Optional[int] = None


class InteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    recipe_id: int
    action: str
    rating: Optional[int]
    created_at: datetime


class UserPreferenceUpdate(BaseModel):
    dietary_restrictions: Optional[List[str]] = None
    disliked_ingredients: Optional[List[str]] = None
    cuisine_weights: Optional[dict] = None
    nutrition_goal: Optional[str] = None
    expiry_horizon_days: Optional[int] = None


class UserPreferenceOut(BaseModel):
    dietary_restrictions: List[str]
    disliked_ingredients: List[str]
    cuisine_weights: dict
    nutrition_goal: str
    expiry_horizon_days: int


class ReceiptParsedItem(BaseModel):
    raw_text: str
    matched_ingredient_name: Optional[str]
    match_confidence: float
    quantity: float
    unit: str


class ReceiptScanResult(BaseModel):
    items: List[ReceiptParsedItem]


class ReceiptConfirmItem(BaseModel):
    ingredient_name: str
    quantity: float = 1.0
    unit: str = "unit"
    storage_location: str = "pantry"


class ReceiptConfirmRequest(BaseModel):
    items: List[ReceiptConfirmItem]
