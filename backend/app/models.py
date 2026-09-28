from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    category = Column(String, nullable=False, default="pantry")
    default_shelf_life_days = Column(Integer, nullable=False, default=30)

    inventory_items = relationship("InventoryItem", back_populates="ingredient", cascade="all, delete-orphan")
    recipe_links = relationship("RecipeIngredient", back_populates="ingredient")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit = Column(String, nullable=False, default="unit")
    storage_location = Column(String, nullable=False, default="pantry")
    purchase_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    expiry_date = Column(Date, nullable=True)

    ingredient = relationship("Ingredient", back_populates="inventory_items")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    cuisine = Column(String, nullable=False, default="other")
    tags = Column(String, nullable=False, default="")  # comma separated
    prep_time_minutes = Column(Integer, nullable=False, default=30)
    steps = Column(Text, nullable=False, default="")
    calories = Column(Integer, nullable=True)
    protein_g = Column(Integer, nullable=True)
    carbs_g = Column(Integer, nullable=True)
    fat_g = Column(Integer, nullable=True)

    ingredient_links = relationship(
        "RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit = Column(String, nullable=False, default="unit")
    optional = Column(Boolean, nullable=False, default=False)

    recipe = relationship("Recipe", back_populates="ingredient_links")
    ingredient = relationship("Ingredient", back_populates="recipe_links")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    action = Column(String, nullable=False)  # viewed | cooked | skipped | rated
    rating = Column(Integer, nullable=True)  # 1-5, only for action == rated
    coverage = Column(Float, nullable=True)
    expiry_urgency = Column(Float, nullable=True)
    preference_score = Column(Float, nullable=True)
    nutrition_fit = Column(Float, nullable=True)
    missing_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, default=1)
    dietary_restrictions = Column(String, nullable=False, default="")  # comma separated
    disliked_ingredients = Column(String, nullable=False, default="")  # comma separated
    cuisine_weights = Column(Text, nullable=False, default="{}")  # json string
    nutrition_goal = Column(String, nullable=False, default="balanced")
    expiry_horizon_days = Column(Integer, nullable=False, default=5)
