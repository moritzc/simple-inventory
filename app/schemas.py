from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ItemBase(BaseModel):
    name: str
    quantity: int = Field(1, ge=0)
    category: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    box_id: int
    last_updated: Optional[datetime]

    class Config:
        orm_mode = True

class BoxBase(BaseModel):
    name: str

class BoxCreate(BoxBase):
    pass

class Box(BoxBase):
    id: int
    items: List[Item] = Field(default_factory=list)

    class Config:
        orm_mode = True

