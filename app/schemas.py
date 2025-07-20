from pydantic import BaseModel, Field

class ItemBase(BaseModel):
    name: str
    quantity: int = 1

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    box_id: int

    class Config:
        orm_mode = True

class BoxBase(BaseModel):
    name: str

class BoxCreate(BoxBase):
    pass

class Box(BoxBase):
    id: int
    items: list[Item] = []

    class Config:
        orm_mode = True
