from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .db import SessionLocal, engine
from fastapi.staticfiles import StaticFiles

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Inventory API")

app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Boxes
@app.post("/boxes", response_model=schemas.Box)
def create_box(box: schemas.BoxCreate, db: Session = Depends(get_db)):
    return crud.create_box(db=db, box=box)

@app.get("/boxes", response_model=list[schemas.Box])
def read_boxes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_boxes(db, skip=skip, limit=limit)

@app.get("/boxes/{box_id}", response_model=schemas.Box)
def read_box(box_id: int, db: Session = Depends(get_db)):
    db_box = crud.get_box(db, box_id=box_id)
    if db_box is None:
        raise HTTPException(status_code=404, detail="Box not found")
    return db_box

@app.delete("/boxes/{box_id}", status_code=204)
def remove_box(box_id: int, db: Session = Depends(get_db)):
    crud.delete_box(db, box_id)

# Items
@app.post("/boxes/{box_id}/items", response_model=schemas.Item)
def create_item_for_box(box_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db=db, item=item, box_id=box_id)

@app.put("/items/{item_id}/quantity")
def change_qty(item_id: int, delta: int, db: Session = Depends(get_db)):
    updated = crud.update_item_qty(db, item_id, delta)
    if updated is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated

@app.delete("/items/{item_id}", status_code=204)
def remove_item(item_id: int, db: Session = Depends(get_db)):
    crud.delete_item(db, item_id)
