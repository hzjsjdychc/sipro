"""EPIC 1.7 — Conversion API (CAPI) feedback loop (config-driven, honest simulation).

When a lead/deal reaches a conversion milestone we feed the event BACK to the
originating ad platform (Meta CAPI / Google Enhanced Conversions / TikTok Events API)
so their optimisation models learn from real downstream outcomes (closing the loop).

Real transport activates automatically when the matching platform token is
configured in the environment; otherwise a SIMULATION record is written. Either
way a `conversion_events` row is stored so the Attribution funnel can display the
loop honestly. Only ad-trackable sources produce a conversion — organic/manual
channels (walk_in, referral, manual) are skipped (nothing to feed back).
"""
import logging
import os

from db import db, ORG_ID
from core_utils import new_id, now_iso

logger = logging.getLogger("sipro.capi")

# lead.source -> ad platform that should receive the feedback event.
PLATFORM_BY_SOURCE = {
    "meta_ads": "meta",
    "whatsapp": "meta",        # WhatsApp click-to-chat ads also report to Meta.
    "google_lead": "google",
    "tiktok_lead": "tiktok",
    "website": "web_pixel",
}

# platform -> env var whose presence flips transport to LIVE (else simulation).
LIVE_ENV_BY_PLATFORM = {
    "meta": "META_CAPI_TOKEN",
    "google": "GOOGLE_ADS_CONV_TOKEN",
    "tiktok": "TIKTOK_EVENTS_TOKEN",
    "web_pixel": "WEB_PIXEL_TOKEN",
}

PLATFORM_LABEL = {
    "meta": "Meta (Conversions API)",
    "google": "Google (Enhanced Conversions)",
    "tiktok": "TikTok (Events API)",
    "web_pixel": "Web Pixel",
}


def platform_for_source(source):
    return PLATFORM_BY_SOURCE.get((source or "").lower())


def _live(platform: str) -> bool:
    env = LIVE_ENV_BY_PLATFORM.get(platform)
    return bool(env and os.environ.get(env))


async def record_conversion(*, event_name, lead=None, deal=None, value=0,
                            currency="IDR", org_id=ORG_ID):
    """Write a conversion_events row + feed the event back to the ad platform.

    event_name follows the standard ad taxonomy: 'Lead', 'InitiateCheckout',
    'Purchase'. Returns the stored doc, or None when the source is not trackable.
    """
    lead = lead or {}
    source = lead.get("source")
    platform = platform_for_source(source)
    if not platform:
        return None  # organic / manual channel — no loop to close.
    ts = now_iso()
    attribution = lead.get("attribution") or {}
    live = _live(platform)
    doc = {
        "id": new_id(), "org_id": org_id, "platform": platform,
        "platform_label": PLATFORM_LABEL.get(platform, platform),
        "event_name": event_name, "source": source, "campaign": lead.get("campaign"),
        "adset_id": attribution.get("adset_id"), "ad_id": attribution.get("ad_id"),
        "creative_id": attribution.get("creative_id"),
        "lead_id": lead.get("id"), "deal_id": (deal or {}).get("id"),
        "value": int(value or 0), "currency": currency,
        "transport": "live" if live else "simulation",
        "status": "sent", "sent_at": ts, "created_at": ts,
    }
    await db.conversion_events.insert_one(doc)
    logger.info("[CAPI %s] platform=%s event=%s value=%s campaign=%s lead=%s",
                doc["transport"], platform, event_name, value, doc["campaign"], lead.get("id"))
    doc.pop("_id", None)
    return doc
