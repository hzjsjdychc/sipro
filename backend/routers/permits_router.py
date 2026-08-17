"""Permit / Legal-document Tracker (Phase 10 — EPIC 2.7).

Tracks perizinan proyek (KRK/IMB/PBG/SLF/AMDAL/addendum) with deadlines + a status
lifecycle. A scheduler job (engine.permit_deadline_sweeper) raises a corrective task
+ notifies the project PM when a permit is due-soon or overdue. Read is org+project
scoped; project-scoped roles (PM/site) only see their assigned projects.
"""
from fastapi import APIRouter, Depends, HTTPException

from db import db, ORG_ID
from core_utils import new_id, now_iso, serialize_doc
from rbac import require_permission, assert_project_access, project_query
from models import PermitCreate, PermitUpdate, PermitStatusUpdate

router = APIRouter(prefix="/permits", tags=["permits"])

STATUSES = ("not_started", "in_progress", "submitted", "approved", "rejected", "expired")
DONE = ("approved", "rejected", "expired")


@router.get("")
async def list_permits(project_id: str = None, status: str = None,
                       user: dict = Depends(require_permission("permits", "view"))):
    org = user.get("org_id", ORG_ID)
    projs = await db.projects.find(project_query(user, {}), {"_id": 0, "id": 1, "name": 1}).to_list(500)
    pmap = {p["id"]: p["name"] for p in projs}
    fq = {"org_id": org}
    if user.get("role") in ("project_manager", "site_engineer"):
        fq["project_id"] = {"$in": list(pmap.keys())}
    if project_id:
        fq["project_id"] = project_id
    if status:
        fq["status"] = status
    rows = await db.permits.find(fq, {"_id": 0}).sort("deadline", 1).to_list(500)
    now = now_iso()
    for r in rows:
        r["project_name"] = pmap.get(r.get("project_id"), r.get("project_name"))
        r["overdue"] = bool(r.get("status") not in DONE and r.get("deadline") and r["deadline"] < now)
    summary = {
        "total": len(rows),
        "approved": sum(1 for r in rows if r.get("status") == "approved"),
        "in_progress": sum(1 for r in rows if r.get("status") in ("not_started", "in_progress", "submitted")),
        "overdue": sum(1 for r in rows if r.get("overdue")),
    }
    return {"data": serialize_doc(rows), "total": len(rows), "summary": summary}


@router.post("")
async def create_permit(payload: PermitCreate,
                        user: dict = Depends(require_permission("permits", "create"))):
    proj = await assert_project_access(payload.project_id, user)
    org = user.get("org_id", ORG_ID)
    ts = now_iso()
    doc = {
        "id": new_id(), "org_id": org, "project_id": payload.project_id,
        "project_name": proj.get("name"), "type": payload.type,
        "name": payload.name or payload.type, "reference_no": payload.reference_no,
        "authority": payload.authority, "status": "not_started",
        "deadline": payload.deadline, "reminder_days": payload.reminder_days,
        "submitted_at": None, "approved_at": None, "notes": payload.notes,
        "created_by": user.get("email"), "created_at": ts, "updated_at": ts,
    }
    await db.permits.insert_one(dict(doc))
    doc.pop("_id", None)
    return {"data": serialize_doc(doc)}


async def _get(pid: str, user: dict) -> dict:
    doc = await db.permits.find_one({"id": pid, "org_id": user.get("org_id", ORG_ID)}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Perizinan tidak ditemukan")
    await assert_project_access(doc["project_id"], user)
    return doc


@router.get("/{pid}")
async def get_permit(pid: str, user: dict = Depends(require_permission("permits", "view"))):
    return {"data": serialize_doc(await _get(pid, user))}


@router.put("/{pid}")
async def update_permit(pid: str, payload: PermitUpdate,
                        user: dict = Depends(require_permission("permits", "update"))):
    doc = await _get(pid, user)
    upd = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    upd["updated_at"] = now_iso()
    await db.permits.update_one({"id": pid, "org_id": doc["org_id"]}, {"$set": upd})
    return {"data": serialize_doc(await db.permits.find_one({"id": pid}, {"_id": 0}))}


@router.post("/{pid}/status")
async def permit_status(pid: str, payload: PermitStatusUpdate,
                        user: dict = Depends(require_permission("permits", "update"))):
    if payload.status not in STATUSES:
        raise HTTPException(status_code=400, detail="Status tidak valid.")
    doc = await _get(pid, user)
    ts = now_iso()
    setter = {"status": payload.status, "updated_at": ts}
    if payload.status == "submitted" and not doc.get("submitted_at"):
        setter["submitted_at"] = ts
    if payload.status == "approved":
        setter["approved_at"] = ts
    if payload.note:
        setter["notes"] = ((doc.get("notes") or "") + f"\n[{ts[:10]}] {payload.note}").strip()
    await db.permits.update_one({"id": pid, "org_id": doc["org_id"]}, {"$set": setter})
    return {"data": serialize_doc(await db.permits.find_one({"id": pid}, {"_id": 0}))}


@router.delete("/{pid}")
async def delete_permit(pid: str, user: dict = Depends(require_permission("permits", "update"))):
    doc = await _get(pid, user)
    await db.permits.delete_one({"id": pid, "org_id": doc["org_id"]})
    return {"data": {"deleted": True}}
