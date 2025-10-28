from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.status import HTTP_303_SEE_OTHER
from datetime import datetime
import csv, io, json
from . import crud, models, schemas, db
from starlette.datastructures import URL

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

def redirect_home(**params) -> RedirectResponse:
    url = URL("/")
    if params:
        url = url.include_query_params(**params)
    return RedirectResponse(str(url), HTTP_303_SEE_OTHER)


def redirect_box(box_id: int, **params) -> RedirectResponse:
    url = URL(f"/box/{box_id}")
    if params:
        url = url.include_query_params(**params)
    return RedirectResponse(str(url), HTTP_303_SEE_OTHER)


@app.get("/")
def home(
    request: Request,
    db: Session = Depends(get_db),
    q: str = "",
    message: str = "",
    error_message: str = ""
):
    boxes = crud.get_boxes(db)
    ql = q.lower()
    results = []
    if q:
        for box in boxes:
            matches = [
                i for i in box.items
                if ql in i.name.lower() or (i.category and ql in i.category.lower())
            ]
            if ql in box.name.lower() or matches:
                results.append({"box": box, "matches": matches})
    else:
        results = [{"box": box, "matches": []} for box in boxes]

    totals = {
        "boxes": len(boxes),
        "items": sum(len(box.items) for box in boxes),
        "visible_boxes": len(results)
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        "results": results,
        "q": q,
        "message": message,
        "error_message": error_message,
        "totals": totals
    })

@app.post("/create-box")
def create_box(name: str = Form(...), db: Session = Depends(get_db)):
    clean_name = name.strip()
    if not clean_name:
        return redirect_home(error_message="Der Boxname darf nicht leer sein.")
    try:
        crud.create_box(db, schemas.BoxCreate(name=clean_name))
    except IntegrityError:
        db.rollback()
        return redirect_home(error_message="Es existiert bereits eine Box mit diesem Namen.")
    return redirect_home(message=f"Box '{clean_name}' wurde angelegt.")

@app.post("/box/{box_id}/delete")
def delete_box(box_id: int, db: Session = Depends(get_db)):
    crud.delete_box(db, box_id)
    return redirect_home(message="Box wurde gelöscht.")

@app.get("/box/{box_id}")
def view_box(
    box_id: int,
    request: Request,
    db: Session = Depends(get_db),
    message: str = "",
    error_message: str = ""
):
    box = crud.get_box(db, box_id)
    if not box:
        raise HTTPException(status_code=404, detail="Box nicht gefunden")
    return templates.TemplateResponse("box.html", {
        "request": request,
        "box": box,
        "message": message,
        "error_message": error_message
    })

@app.post("/box/{box_id}/add-item")
def add_item(
    box_id: int,
    name: str = Form(...),
    quantity: int = Form(...),
    category: str = Form(None),
    db: Session = Depends(get_db)
):
    box = crud.get_box(db, box_id)
    if not box:
        raise HTTPException(status_code=404, detail="Box nicht gefunden")
    clean_name = name.strip()
    if not clean_name:
        return redirect_box(box_id, error_message="Bitte einen Namen für den Gegenstand angeben.")
    safe_quantity = max(0, quantity)
    clean_category = category.strip() if category else None
    crud.create_item(db, schemas.ItemCreate(
        name=clean_name,
        quantity=safe_quantity,
        category=clean_category
    ), box_id)
    return redirect_box(box_id, message=f"'{clean_name}' wurde hinzugefügt.")

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
    item = crud.set_item_quantity(db, item_id, max(0, quantity))
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
    try:
        raw_bytes = await file.read()
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return redirect_home(error_message="Die Importdatei muss UTF-8 kodiert sein.")

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return redirect_home(error_message="Die Importdatei enthält kein gültiges JSON.")

    if not isinstance(data, list):
        return redirect_home(error_message="Das Importformat wird nicht unterstützt.")

    imported_boxes = 0
    imported_items = 0
    try:
        db.query(models.Item).delete()
        db.query(models.Box).delete()
        db.commit()

        for box_data in data:
            name = str(box_data.get("name", "")).strip()
            if not name:
                continue
            box = models.Box(name=name)
            db.add(box)
            db.flush()
            imported_boxes += 1

            for item_data in box_data.get("items", []):
                item_name = str(item_data.get("name", "")).strip()
                if not item_name:
                    continue
                quantity = item_data.get("quantity", 1)
                try:
                    quantity = int(quantity)
                except (TypeError, ValueError):
                    quantity = 1
                quantity = max(0, quantity)
                category = item_data.get("category")
                category = category.strip() if isinstance(category, str) else None
                last_updated_value = item_data.get("last_updated")
                last_updated = None
                if isinstance(last_updated_value, str):
                    try:
                        last_updated = datetime.fromisoformat(last_updated_value)
                    except ValueError:
                        last_updated = None

                item = models.Item(
                    name=item_name,
                    quantity=quantity,
                    category=category,
                    box=box
                )
                if last_updated:
                    item.last_updated = last_updated
                db.add(item)
                imported_items += 1

        db.commit()
    except SQLAlchemyError:
        db.rollback()
        return redirect_home(error_message="Import fehlgeschlagen. Die Datenbank wurde nicht aktualisiert.")

    return redirect_home(message=f"Import abgeschlossen: {imported_boxes} Boxen, {imported_items} Gegenstände.")
