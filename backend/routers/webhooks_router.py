"""Webhooks (SIMULATION-first) for omnichannel lead capture.

Public endpoints (no auth) that accept sample payloads from multiple providers:
Meta Lead Ads, WhatsApp, Google Lead Form, TikTok Lead, and a generic Web form.
Ads attribution (campaign/adset/ad/creative/form) is carried through to the lead +
lead_capture_event. When real credentials are available later, set the matching
channel_accounts.mode='live' — the capture contract stays identical.

Fase 30c — TIDAK ADA LEAD YANG HILANG LAGI. Dulu payload cacat (JSON rusak, nomor HP
kosong, field salah nama) dibalas 422 dan menguap: uang iklan terbayar tetapi lead tidak
pernah masuk CRM dan tidak ada jejaknya. Sekarang setiap kegagalan disimpan di antrean
`lead_capture_failures`, memicu event `capture.failed` (tugas DM-02 + notifikasi
supervisor), dan bisa diperbaiki lalu diulang dari halaman Automasi & Channel.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

import capture_failures as cf
from db import ORG_ID
from engine import process_lead_capture
from models import WebhookLead

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _failed(provider: str, failure: dict, reason: str) -> JSONResponse:
    """202: kami MENERIMA panggilan provider, tetapi leadnya tertahan (bukan hilang)."""
    return JSONResponse(status_code=202, content={"data": {
        "captured": False, "lead_id": None, "duplicate": False,
        "failure_id": failure["id"], "reason": reason,
        "queued": "Antrean lead gagal masuk (Automasi & Channel → Gagal Masuk)",
        "mode": "simulation", "provider": provider}})


async def _capture(provider: str, request: Request):
    """Satu pintu untuk semua provider: parse → validasi → proses → (atau antrekan)."""
    raw, parse_err = await cf.read_json(request)
    if parse_err:
        failure = await cf.record(provider, raw or {}, parse_err, kind=cf.KIND_DATA,
                                  org_id=ORG_ID)
        return _failed(provider, failure, parse_err)
    try:
        data = WebhookLead(**raw).model_dump()
    except ValidationError as e:
        first = (e.errors() or [{}])[0]
        loc = ".".join(str(x) for x in (first.get("loc") or []))
        reason = f"Payload tidak sesuai kontrak pada '{loc or 'payload'}': {first.get('msg')}"
        failure = await cf.record(provider, raw, reason, kind=cf.KIND_DATA, org_id=ORG_ID)
        return _failed(provider, failure, reason)
    data.setdefault("source", provider)
    clean, err = cf.validate(data)
    if err:
        failure = await cf.record(provider, data, err, kind=cf.KIND_DATA, org_id=ORG_ID)
        return _failed(provider, failure, err)
    try:
        lead_id, duplicate = await process_lead_capture(provider, clean, org_id=ORG_ID)
    except Exception as e:  # noqa: BLE001 - gangguan sementara: layak dicoba ulang otomatis
        reason = f"Gangguan saat memproses lead: {e}"
        failure = await cf.record(provider, clean, reason, kind=cf.KIND_TRANSIENT,
                                  org_id=ORG_ID)
        return _failed(provider, failure, reason)
    return {"data": {"lead_id": lead_id, "duplicate": duplicate, "captured": True,
                     "mode": "simulation", "provider": provider}}


@router.post("/meta-lead")
async def meta_lead(request: Request):
    return await _capture("meta_ads", request)


@router.post("/wa")
async def wa_inbound(request: Request):
    return await _capture("whatsapp", request)


@router.post("/google-lead")
async def google_lead(request: Request):
    return await _capture("google_lead", request)


@router.post("/tiktok-lead")
async def tiktok_lead(request: Request):
    return await _capture("tiktok_lead", request)


@router.post("/web")
async def web_form(request: Request):
    return await _capture("website", request)
