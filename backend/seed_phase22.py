"""EPIC 1.7 Omnichannel seed (SIMULATION): channel accounts, WA templates,
automation rules (message.received / lead.captured / no_response), ads-attribution
capture events, and a stale/unanswered demo conversation (closed 24h window)."""
from db import db, ORG_ID
from core_utils import new_id, now_iso, due_in


async def seed_omnichannel(org_id, ts, ctx):
    lead2 = ctx.get("lead2")
    conv_id = ctx.get("conv_id")

    # 1) Channel accounts (all SIMULATION mode).
    channels = [
        ("wa_main", "whatsapp", "WhatsApp Sales"),
        ("meta_ads", "meta_lead_ads", "Meta Lead Ads"),
        ("google_ads", "google_lead", "Google Lead Form"),
        ("tiktok_ads", "tiktok_lead", "TikTok Lead"),
        ("web_form", "website", "Formulir Website"),
    ]
    await db.channel_accounts.insert_many([
        {"id": new_id(), "org_id": org_id, "code": c, "channel": ch, "name": n,
         "mode": "simulation", "is_active": True, "created_by": "seed", "created_at": ts}
        for c, ch, n in channels])

    # 2) Pre-approved WhatsApp templates (used to (re)open the 24h session window).
    templates = [
        ("welcome", "Sapaan Awal", "utility",
         "Halo {{name}}, terima kasih sudah menghubungi PT SIPRO Land. Ada yang bisa kami bantu "
         "terkait unit hunian Anda?", ["name"]),
        ("price_info", "Info Harga", "utility",
         "Untuk unit Tipe 45 di Cluster Asri, harga mulai Rp 850 juta (skema KPR & cash bertahap "
         "tersedia). Mau kami jadwalkan survey lokasi?", []),
        ("appointment_reminder", "Pengingat Survey", "utility",
         "Halo {{name}}, mengingatkan jadwal survey unit pada {{date}}. Sampai jumpa!", ["name", "date"]),
        ("reengage", "Aktivasi Ulang", "marketing",
         "Halo {{name}}, masih tertarik dengan unit di Cluster Asri? Ada promo terbatas bulan ini. "
         "Balas pesan ini untuk info lebih lanjut.", ["name"]),
    ]
    await db.wa_templates.insert_many([
        {"id": new_id(), "org_id": org_id, "code": code, "name": name, "category": cat,
         "language": "id", "body": body, "variables": vars_, "status": "approved",
         "created_by": "seed", "created_at": ts, "updated_at": ts}
        for code, name, cat, body, vars_ in templates])

    # 3) Automation rules (richer set; replaces the single inline rule from seed.py).
    await db.automation_rules.delete_many({"org_id": org_id})
    rules = [
        {"name": "Intent Harga/KPR/Survey", "event": "message.received",
         "keywords": ["harga", "kpr", "survey", "cicilan", "dp", "bunga"],
         "actions": [{"type": "suggest_stage", "stage": "appointment"},
                     {"type": "send_template", "template_code": "price_info"},
                     {"type": "create_task", "title": "Tindak lanjut intent harga/KPR"}]},
        {"name": "Sapaan Otomatis Lead Baru", "event": "lead.captured", "keywords": [],
         "actions": [{"type": "send_template", "template_code": "welcome"},
                     {"type": "create_task", "title": "Verifikasi kebutuhan lead baru"}]},
        {"name": "Aktivasi Ulang 3 Hari Diam", "event": "no_response", "keywords": [],
         "no_response_days": 3,
         "actions": [{"type": "send_template", "template_code": "reengage"},
                     {"type": "create_task", "title": "Follow-up lead pasif (3 hari)"}]},
    ]
    for r in rules:
        await db.automation_rules.insert_one({
            "id": new_id(), "org_id": org_id, "name": r["name"], "is_active": True,
            "trigger": {"event": r["event"], "keywords": r.get("keywords", []),
                        "no_response_days": r.get("no_response_days")},
            "actions": r["actions"], "require_confirmation": True, "executions": 0,
            "created_by": "seed", "created_at": ts})

    # 4) Ads attribution on the existing meta_ads lead + a capture-event audit row.
    if lead2:
        attribution = {"adset_id": "adset-102", "ad_id": "ad-556",
                       "creative_id": "cr-video-a", "form_id": "lf-778"}
        await db.leads.update_one({"id": lead2}, {"$set": {"attribution": attribution}})
        await db.lead_capture_events.insert_one({
            "id": new_id(), "org_id": org_id, "provider": "meta_ads",
            "dedup_key": "meta_ads:+628122222222", "status": "processed", "lead_id": lead2,
            "source": "meta_ads", "campaign": "cluster-a-meta", **attribution,
            "raw_payload": {"name": "Bapak Rudi Hartono", "phone": "+628122222222"}, "created_at": ts})

        # 5) A stale, unanswered conversation (24h window CLOSED) — demonstrates the
        #    template-gated composer, the 'unanswered' filter, and the no_response sweeper.
        stale_conv = new_id()
        await db.conversations.insert_one({
            "id": stale_conv, "org_id": org_id, "channel": "whatsapp",
            "contact_phone": "+628123333333", "contact_name": "Ibu Sari (Lead Pasif)",
            "lead_id": lead2, "owner": "sales@sipro.co.id", "status": "active",
            "mode": "simulation", "unread": 1, "last_message_at": due_in(days=-4),
            "last_direction": "in", "window_expires_at": due_in(days=-3),
            "created_at": due_in(days=-5), "updated_at": due_in(days=-4)})
        await db.messages.insert_one({
            "id": new_id(), "org_id": org_id, "conversation_id": stale_conv, "direction": "in",
            "body": "Apakah masih tersedia unit Tipe 45? Saya tertarik.", "sender": "contact",
            "created_at": due_in(days=-4)})

    # Mark the existing demo conversation as answered (last message from agent).
    if conv_id:
        await db.conversations.update_one({"id": conv_id}, {"$set": {"last_direction": "out"}})

    # 6) Demo CAPI conversion feedback (Lead) for the meta_ads lead — shows the
    #    closed-loop in the Attribution panel at seed time (runtime adds more on
    #    lead.captured / deal.booked / deal.sold).
    if lead2:
        await db.conversion_events.insert_one({
            "id": new_id(), "org_id": org_id, "platform": "meta",
            "platform_label": "Meta (Conversions API)", "event_name": "Lead",
            "source": "meta_ads", "campaign": "cluster-a-meta", "adset_id": "adset-102",
            "ad_id": "ad-556", "creative_id": "cr-video-a", "lead_id": lead2, "deal_id": None,
            "value": 0, "currency": "IDR", "transport": "simulation", "status": "sent",
            "sent_at": ts, "created_at": ts})

    # 7) Demo broadcast (completed) targeting the passive/meta segment via 'reengage'.
    if lead2:
        bid = new_id()
        await db.broadcasts.insert_one({
            "id": bid, "org_id": org_id, "name": "Aktivasi Ulang Cluster Asri (Meta)",
            "template_code": "reengage", "template_name": "Aktivasi Ulang",
            "segment": {"lead_stages": ["nurturing"], "score_bands": [], "sources": ["meta_ads"],
                        "campaigns": [], "include_customers": False},
            "channel": "whatsapp", "mode": "simulation", "status": "completed",
            "total": 1, "sent": 1, "delivered": 1, "read": 1, "failed": 0,
            "created_by": "seed", "created_at": due_in(days=-1), "updated_at": due_in(days=-1)})
        await db.broadcast_recipients.insert_one({
            "id": new_id(), "org_id": org_id, "broadcast_id": bid, "kind": "lead",
            "ref_id": lead2, "lead_id": lead2, "name": "Bapak Rudi Hartono",
            "phone": "+628122222222", "status": "read", "delivered_at": due_in(days=-1),
            "read_at": due_in(days=-1), "created_at": due_in(days=-1)})
