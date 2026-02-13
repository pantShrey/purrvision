from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, computed_field
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue
from .database import get_db, Store, StoreStatus, StoreEngine, AuditLog
from .tasks import provision_store_task
from app.tasks import delete_store_task
from typing import List
import secrets
import string
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For local dev, allow all. In prod, lock this down.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
redis_conn = Redis(host=REDIS_HOST, port=6379)
q = Queue(connection=redis_conn)


# ---------------------------
# Pydantic models
# ---------------------------
class StoreCreate(BaseModel):
    name: str
    engine: StoreEngine = StoreEngine.WOOCOMMERCE
    admin_user: str = "admin"
    admin_password: str | None = None  # Optional


class StoreResponse(BaseModel):
    id: str
    name: str
    status: StoreStatus
    engine: StoreEngine
    url: str | None

    # GENERALIZED ADMIN URL
    @computed_field
    def store_admin_url(self) -> str | None:
        if not self.url:
            return None

        if self.engine == StoreEngine.WOOCOMMERCE:
            return f"{self.url}/wp-admin/admin.php?page=wc-admin"
        elif self.engine == StoreEngine.MEDUSA:
            return f"{self.url}/app"
        return None

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    event: str
    details: str | None
    timestamp: str

    class Config:
        from_attributes = True


# ---------------------------
# Helper 
# ---------------------------
def active_stores(query):
    """Filter out soft-deleted stores from a query object."""
    return query.filter(Store.status != StoreStatus.DELETED)


# ---------------------------
# Endpoints
# ---------------------------
@app.post("/stores", status_code=202)
def create_store(request: StoreCreate, db: Session = Depends(get_db)):
    # 1. Medusa Stub 
    if request.engine == StoreEngine.MEDUSA:
        raise HTTPException(status_code=501, detail="Medusa engine coming in Round 2.")

    if db.query(Store).filter(Store.name == request.name).first():
        raise HTTPException(status_code=400, detail="Store name already taken")

    # 2. Basic Password Generation
    password = request.admin_password
    if not password:
        chars = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(chars) for i in range(16))

    new_store = Store(
        name=request.name,
        status=StoreStatus.QUEUED,
        engine=request.engine,
        admin_user=request.admin_user,
        admin_password=password,
    )
    db.add(new_store)
    db.commit()
    db.refresh(new_store)

    q.enqueue(provision_store_task, new_store.id, job_timeout = 600)

    return {
        "id": new_store.id,
        "status": "QUEUED",
        "message": "Provisioning started",
        "initial_credentials": {"username": new_store.admin_user, "password": password},
    }


@app.get("/stores/{store_id}", response_model=StoreResponse)
def get_store(store_id: str, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.id == store_id).first()
    # Treat DELETED stores as "not found" for now
    if not store or store.status == StoreStatus.DELETED:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@app.get("/stores", response_model=List[StoreResponse])
def list_stores(include_deleted: bool = Query(False, description="Set true to include soft-deleted stores"), db: Session = Depends(get_db)):
    """
    Returns active stores by default. Set ?include_deleted=true to include soft-deleted stores.
    """
    query = db.query(Store)
    if not include_deleted:
        query = active_stores(query)
    return query.all()


@app.get("/stores/{store_id}/audit", response_model=List[AuditLogResponse])
def get_store_audit_logs(store_id: str, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).filter(AuditLog.store_id == store_id).order_by(AuditLog.timestamp.desc()).all()
    return [
        AuditLogResponse(event=l.event, details=l.details, timestamp=l.timestamp.isoformat()) for l in logs
    ]


@app.delete("/stores/{store_id}", status_code=202)
def delete_store(store_id: str, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    # soft-delete: mark DELETING and let background worker finalize
    store.status = StoreStatus.DELETING
    db.commit()
    q.enqueue(delete_store_task, store.id)
    return {"id": store.id, "status": "DELETING", "message": "Deletion started"}
