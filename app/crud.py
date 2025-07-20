from sqlalchemy.orm import Session
from . import models, schemas

# Box
def get_box(db: Session, box_id: int):
    return db.query(models.Box).filter(models.Box.id == box_id).first()

def get_boxes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Box).offset(skip).limit(limit).all()

def create_box(db: Session, box: schemas.BoxCreate):
    db_box = models.Box(name=box.name)
    db.add(db_box)
    db.commit()
    db.refresh(db_box)
    return db_box

def delete_box(db: Session, box_id: int):
    db.query(models.Box).filter(models.Box.id == box_id).delete()
    db.commit()

# Item
def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

def create_item(db: Session, item: schemas.ItemCreate, box_id: int):
    db_item = models.Item(**item.dict(), box_id=box_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_item_qty(db: Session, item_id: int, delta: int):
    db_item = get_item(db, item_id)
    if db_item:
        db_item.quantity = max(0, db_item.quantity + delta)
        db.commit()
        db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int):
    db.query(models.Item).filter(models.Item.id == item_id).delete()
    db.commit()
