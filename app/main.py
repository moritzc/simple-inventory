from fastapi import FastAPI, Request, Depends, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER
from datetime import datetime
import csv, io, json
from . import crud, models, schemas, db

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

models.Base.metadata.create_all(bind=db.engine)

def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

@app.get("/")
def home(request: Request, db: Session = Depends(get_db), q: str = ""):
    boxes = crud.get_boxes(db)
    results = []
    if q:
        ql = q.lower()
        for box in boxes:
            matches = [i for i in box.items
                       if ql in i.name.lower() or (i.category and ql in i.category.lower())]
            if ql in box.name.lower() or matches:
                results.append({"box": box, "matches": matches})
    else:
        results = [{"box": b, "matches": []} for b in boxes]
    return templates.TemplateResponse("index.html", {
        "request": request, "results": results, "q": q
    })

@app.post("/create-box")
def create_box(name: str = Form(...), db: Session = Depends(get_db)):
    crud.create_box(db, schemas.BoxCreate(name=name))
    return RedirectResponse("/", HTTP_303_SEE_OTHER)

@app.post("/box/{box_id}/delete")
def delete_box(box_id: int, db: Session = Depends(get_db)):
    crud.delete_box(db, box_id)
    return RedirectResponse("/", HTTP_303_SEE_OTHER)

@app.get("/box/{box_id}")
def view_box(box_id: int, request: Request, db: Session = Depends(get_db)):
    box = crud.get_box(db, box_id)
    return templates.TemplateResponse("box.html", {
        "request": request, "box": box
    })

@app.post("/box/{box_id}/add-item")
def add_item(
    box_id: int,
    name: str = Form(...),
    quantity: int = Form(...),
    category: str = Form(None),
    db: Session = Depends(get_db)
):
    crud.create_item(db, schemas.ItemCreate(
        name=name, quantity=quantity, category=category
    ), box_id)
    return RedirectResponse(f"/box/{box_id}", HTTP_303_SEE_OTHER)

@app.post("/item/{item_id}/change")
def change_quantity(
    item_id: int,
    delta: int = Form(...),
    db: Session = Depends(get_db)
):
    item = crud.update_item_qty(db, item_id, delta)
    if item:
        return JSONResponse({"new_quantity": item.quantity})
    return JSONResponse({"error": "not found"}, status_code=404)

@app.post("/item/{item_id}/set")
def set_quantity(
    item_id: int,
    quantity: int = Form(...),
    db: Session = Depends(get_db)
):
    item = crud.set_item_quantity(db, item_id, quantity)
    if item:
        return JSONResponse({"new_quantity": item.quantity})
    return JSONResponse({"error": "not found"}, status_code=404)

@app.post("/item/{item_id}/delete")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    crud.delete_item(db, item_id)
    return JSONResponse({"status": "ok"})

@app.post("/item/{item_id}/edit")
def edit_item(
    item_id: int,
    name: str = Form(...),
    category: str = Form(None),
    db: Session = Depends(get_db)
):
    item = crud.get_item(db, item_id)
    if not item:
        return JSONResponse({"error": "not found"}, status_code=404)
    item.name = name
    item.category = category
    from datetime import datetime
    item.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return JSONResponse({"ok": True, "name": item.name, "category": item.category})

@app.post("/box/{box_id}/edit")
def edit_box(box_id: int, name: str = Form(...), db: Session = Depends(get_db)):
    box = crud.get_box(db, box_id)
    if not box:
        return JSONResponse({"error": "not found"}, status_code=404)
    box.name = name
    from datetime import datetime
    for item in box.items:
        item.last_updated = datetime.utcnow()  # Option: Box-Rename als Änderung für Items werten
    db.commit()
    db.refresh(box)
    return JSONResponse({"ok": True, "name": box.name})


@app.get("/export/json")
def export_json(db: Session = Depends(get_db)):
    data = []
    for box in crud.get_boxes(db):
        data.append({
            "id": box.id,
            "name": box.name,
            "items": [
                {
                    "name": i.name,
                    "quantity": i.quantity,
                    "category": i.category,
                    "last_updated": i.last_updated.isoformat() if i.last_updated else None
                } for i in box.items
            ]
        })
    now = datetime.now()
    fname = f"inventory-{now.month:02d}-{now.year}.json"
    file_data = io.StringIO(json.dumps(data, ensure_ascii=False, indent=2))
    headers = {"Content-Disposition": f"attachment; filename={fname}"}
    return StreamingResponse(file_data, media_type="application/json", headers=headers)

@app.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Box", "Item", "Quantity", "Category", "Last Updated"])
    for box in crud.get_boxes(db):
        for i in box.items:
            writer.writerow([
                box.name, i.name, i.quantity, i.category or "",
                i.last_updated.isoformat() if i.last_updated else ""
            ])
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory.csv"}
    )

@app.post("/import")
async def import_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = (await file.read()).decode()
    data = json.loads(content)

    # ALLES LÖSCHEN
    db.query(models.Item).delete()
    db.query(models.Box).delete()
    db.commit()

    # Importiere die neuen Daten
    for box_data in data:
        b = crud.create_box(db, schemas.BoxCreate(name=box_data["name"]))
        for it in box_data.get("items", []):
            crud.create_item(db, schemas.ItemCreate(
                name=it["name"],
                quantity=it.get("quantity", 1),
                category=it.get("category")
            ), b.id)
    return RedirectResponse("/", HTTP_303_SEE_OTHER)
