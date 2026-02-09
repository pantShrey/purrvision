from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue
from .database import get_db, Store, engine
from .tasks import provision_store_task # Import the logic

app = FastAPI()

# Connect to Redis
redis_conn = Redis(host='localhost', port=6379)
q = Queue(connection=redis_conn)

# --- Pydantic Models (Input Validation) ---
class StoreCreate(BaseModel):
    name: str

class StoreResponse(BaseModel):
    id: str
    name: str
    status: str
    url: str | None

# --- Endpoints ---

@app.post("/stores", status_code=202)
def create_store(request: StoreCreate, db: Session = Depends(get_db)):
    """
    1. Checks if store exists
    2. Creates DB Record (QUEUED)
    3. Pushes job to Redis
    """
    # Check uniqueness
    if db.query(Store).filter(Store.name == request.name).first():
        raise HTTPException(status_code=400, detail="Store name already taken")

    # Create DB Record
    new_store = Store(name=request.name, status="QUEUED")
    db.add(new_store)
    db.commit()
    db.refresh(new_store)

    # Enqueue Task
    q.enqueue(provision_store_task, new_store.id)

    return {"id": new_store.id, "status": "QUEUED", "message": "Provisioning started"}

@app.get("/stores/{store_id}", response_model=StoreResponse)
def get_store(store_id: str, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store

@app.get("/stores")
def list_stores(db: Session = Depends(get_db)):
    return db.query(Store).all()