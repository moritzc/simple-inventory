from fastapi import FastAPI, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from . import crud, models, schemas, db

import io, csv, json

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

models.Base.metadata.create_all(bind=db.engine)

def get_db():
    database = db.SessionLocal()
    try:
        yield database
    finally:
        database.close()

@app.get("/")
def home(request: Request, db: Session = Depends(get_db), q: str = ""):
    boxes = crud.get_boxes(db)
    if q:
        q_lower = q.lower()
        boxes = [
            box for box in boxes
            if q_lower in box.name.lower()
            or any(q_lower in item.name.lower() for item in box.items)
        ]
    return templates.TemplateResponse("index.html", {"request": request, "boxes": boxes, "q": q})

@app.post("/create-box")
def create_box(name: str = Form(...), db: Session = Depends(get_db)):
    crud.create_box(db, schemas.BoxCreate(name=name))
    return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)

@app.post("/box/{box_id}/delete")
def delete_box(box_id: int, db: Session = Depends(get_db)):
    crud.delete_box(db, box_id)
    return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)

@app.get("/box/{box_id}")
def view_box(box_id: int, request: Request, db: Session = Depends(get_db)):
    box = crud.get_box(db, box_id)
    return templates.TemplateResponse("box.html", {"request": request, "box": box})

@app.post("/box/{box_id}/add-item")
def add_item(box_id: int, name: str = Form(...), quantity: int = Form(...), db: Session = Depends(get_db)):
    crud.create_item(db, schemas.ItemCreate(name=name, quantity=quantity), box_id=box_id)
    return RedirectResponse(f"/box/{box_id}", status_code=HTTP_303_SEE_OTHER)

@app.post("/item/{item_id}/delete")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    crud.delete_item(db, item_id)
    return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)

@app.post("/item/{item_id}/increase")
def increase_item(item_id: int, db: Session = Depends(get_db)):
    crud.update_item_qty(db, item_id, delta=1)
    return RedirectResponse(request_url_for_box(item_id, db), status_code=HTTP_303_SEE_OTHER)

@app.post("/item/{item_id}/decrease")
def decrease_item(item_id: int, db: Session = Depends(get_db)):
    crud.update_item_qty(db, item_id, delta=-1)
    return RedirectResponse(request_url_for_box(item_id, db), status_code=HTTP_303_SEE_OTHER)

@app.post("/item/{item_id}/set")
def set_item_quantity(item_id: int, quantity: int = Form(...), db: Session = Depends(get_db)):
    item = crud.get_item(db, item_id)
    if item:
        item.quantity = max(0, quantity)
        db.commit()
    return RedirectResponse(f"/box/{item.box_id}", status_code=HTTP_303_SEE_OTHER)

def request_url_for_box(item_id: int, db: Session):
    item = crud.get_item(db, item_id)
    return f"/box/{item.box_id}" if item else "/"

@app.get("/export")
def export_data(format: str = "json", db: Session = Depends(get_db)):
    boxes = crud.get_boxes(db)
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Box", "Item", "Quantity"])
        for box in boxes:
            for item in box.items:
                writer.writerow([box.name, item.name, item.quantity])
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=inventory.csv"})
    else:
        data = [
            {
                "name": box.name,
                "items": [{"name": i.name, "quantity": i.quantity} for i in box.items]
            }
            for box in boxes
        ]
        return StreamingResponse(io.BytesIO(json.dumps(data, indent=2).encode()), media_type="application/json", headers={"Content-Disposition": "attachment; filename=inventory.json"})

@app.post("/import")
async def import_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    data = json.loads(content)

    for box_data in data:
        box = crud.create_box(db, schemas.BoxCreate(name=box_data["name"]))
        for item in box_data.get("items", []):
            crud.create_item(db, schemas.ItemCreate(**item), box.id)

    return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)
