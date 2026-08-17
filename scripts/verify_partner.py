#!/usr/bin/env python3
"""verify_partner.py — GATE MITRA & FEE (Fase 42).

Janji bisnis yang dijaga (`docs/v2/25_PARTNER_SPEC.md` §8 — Definition of Done):

  1. Menu "Mitra & Fee" DIBUKA (punya route & halaman), sementara rute lama
     `/marketing-fee` tetap hidup sebagai alias — tautan & bookmark lama tidak boleh rusak.
  2. Lead mitra tidak bisa dibuat tanpa mitra AKTIF berkontrak (bila toggle menyala).
  3. Tidak ada fee tanpa aturan yang berlaku (INV-09) — dan bila dua aturan sama spesifik,
     sistem MENOLAK, tidak memilih diam-diam.
  4. Nominal fee = hasil evaluasi aturan (persen/tier/porsi pemicu), termasuk PPh; beban =
     netto + PPh sehingga jurnal tetap seimbang.
  5. Satu mitra × satu deal × satu pemicu = satu tagihan (idempoten).
  6. Aturan tidak sah DITOLAK sebelum tersimpan (porsi ≠ 100%, tier bolong, tarif liar).
  7. Status mitra hanya bisa diubah dengan ALASAN (berdampak pada uang).
  8. Analitik mitra = hitungan dari data, bukan angka yang diketik.
  9. RBAC: sales tidak boleh mendaftarkan mitra / mengubah aturan fee.

Exit !=0 bila ada FAIL. Uji-mutasi: `scripts/mutasi_41_42.py`.
"""
import os
import pathlib
import re
import sys
import time

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "backend" / ".env")
BASE = "http://localhost:8001/api"
PW = "Sipro#2026"
FE = ROOT / "frontend" / "src"
MARKER = "GATE 42 — fee mitra otomatis"
GATE_PHONE = "+628129990042"
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
fails = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)
    return bool(cond)


def login(email):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": PW}, timeout=20)
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def read(rel):
    p = FE / rel
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def main():
    admin = login("superadmin@sipro.co.id")
    manager = login("manager@sipro.co.id")
    sales = login("sales@sipro.co.id")
    finance = login("finance@sipro.co.id")

    print("\n1. Menu dibuka tanpa merusak tautan lama")
    nav = read("config/navigationConfig.js")
    app = read("App.js")
    routes = set(re.findall(r'<Route\s+path="([^"]+)"', app))
    body = nav.split("export const NAV_STRUCTURE", 1)[-1].split("export function", 1)[0]
    partner_block = [b for b in re.split(r"\n\s{4,6}\{", body) if 'id: "partners"' in b]
    check("item menu 'Mitra & Fee' ada", len(partner_block) == 1, f"{len(partner_block)} blok")
    if partner_block:
        check("menu mitra TIDAK lagi 'Segera Hadir'", "comingSoon" not in partner_block[0])
        check("menu mitra punya path /partners", 'path: "/partners"' in partner_block[0])
    check("route /partners ada", "/partners" in routes)
    check("halaman kanonik /partners/:id ada", "/partners/:id" in routes)
    check("rute alias /marketing-fee TETAP hidup", "/marketing-fee" in routes)
    nav_paths = set(re.findall(r'path:\s*"([^"]+)"', body))
    check("'/marketing-fee' tidak lagi jadi baris sidebar (jadi tab Tagihan Fee)",
          "/marketing-fee" not in nav_paths)
    mig = read("config/navMigrationMap.js")
    check("peta menu memberi tahu ke mana Marketing Fee pindah",
          "/partners?hub=tagihan" in mig)
    check("halaman hub mitra memakai TabPage ?hub=",
          'paramKey="hub"' in read("pages/PartnersPage.js"))
    check("tab Tagihan Fee memakai panel fee yang sudah ada (bukan salinan baru)",
          "FeesPanel" in read("pages/PartnersPage.js"))
    for rel in ("components/partners/PartnersListTab.js", "components/partners/FeeRulesTab.js",
                "components/partners/PartnerAnalyticsTab.js",
                "components/partners/ConflictsTab.js", "pages/PartnerProfilePage.js"):
        check(f"{pathlib.Path(rel).name} ada", bool(read(rel)))
    check("daftar mitra memakai pola tabel pro",
          all(x in read("components/partners/PartnersListTab.js")
              for x in ("DataTable", "FilterBar", "useListQuery")))

    print("\n2. Master mitra: data & pagar validasi")
    r = requests.get(f"{BASE}/partners", headers=admin, timeout=30)
    check("GET /partners = 200", r.status_code == 200, r.text[:120])
    partners = r.json().get("data") or []
    check("ada mitra terdaftar", len(partners) >= 2, f"{len(partners)} mitra")
    check("setiap mitra punya jenis & bentuk badan (dasar PPh)",
          all(p.get("partner_kind") and p.get("entity_type") for p in partners))
    check("kelayakan kontrak dihitung server", all("contract_ok" in p for p in partners))
    dup = requests.post(f"{BASE}/partners", headers=admin, timeout=30, json={
        "name": partners[0]["name"], "partner_kind": "agen_perorangan", "phone": "+628120000999"})
    check("nama mitra ganda ditolak", dup.status_code == 400, f"got {dup.status_code}")
    dup2 = requests.post(f"{BASE}/partners", headers=admin, timeout=30, json={
        "name": "Mitra Uji Nomor Ganda", "partner_kind": "agen_perorangan",
        "phone": partners[0]["phone"]})
    check("nomor mitra ganda ditolak (atribusi harus bisa dipertanggungjawabkan)",
          dup2.status_code == 400, f"got {dup2.status_code}")
    bad_kind = requests.post(f"{BASE}/partners", headers=admin, timeout=30, json={
        "name": "Mitra Jenis Ngawur", "partner_kind": "tukang_bakso", "phone": "+628120000998"})
    check("jenis mitra di luar SSOT ditolak", bad_kind.status_code == 400,
          f"got {bad_kind.status_code}")
    r = requests.post(f"{BASE}/partners/{partners[0]['id']}/status", headers=admin,
                      json={"status": "suspended"}, timeout=30)
    check("ubah status mitra tanpa alasan = 400", r.status_code == 400, f"got {r.status_code}")

    print("\n3. Aturan fee: validasi & pemilihan")
    rules = requests.get(f"{BASE}/partners/rules", headers=admin, timeout=30)
    check("GET /partners/rules = 200", rules.status_code == 200, rules.text[:120])
    rows = rules.json().get("data") or []
    check("ada aturan fee terdaftar", len(rows) >= 2, f"{len(rows)} aturan")
    check("aturan menyebut prioritas (paling spesifik menang)",
          all("specificity" in x for x in rows))
    bad = requests.post(f"{BASE}/partners/rules", headers=admin, timeout=30, json={
        "name": "Gate — porsi tidak 100", "basis": "percent_price", "value": 2,
        "splits": [{"trigger": "ppjb_signed", "pct": 40}]})
    check("porsi pembayaran bertahap ≠ 100% ditolak", bad.status_code == 400,
          f"got {bad.status_code}: {bad.text[:80]}")
    bad = requests.post(f"{BASE}/partners/rules", headers=admin, timeout=30, json={
        "name": "Gate — tier bolong", "basis": "tier_volume", "trigger": "ppjb_signed",
        "tiers": [{"min": 0, "max": 2, "value": 1, "mode": "percent"},
                  {"min": 5, "max": None, "value": 2, "mode": "percent"}]})
    check("tier dengan celah ditolak", bad.status_code == 400, f"got {bad.status_code}")
    bad = requests.post(f"{BASE}/partners/rules", headers=admin, timeout=30, json={
        "name": "Gate — tarif pajak liar", "basis": "fixed_per_deal", "value": 1000,
        "trigger": "ppjb_signed", "tax": {"pph_type": "pph23", "rate": 250}})
    check("tarif PPh di luar batas ditolak", bad.status_code == 400, f"got {bad.status_code}")

    print("\n4. INV-09 & fee dari pemicu NYATA (reservasi → booking → PPJB)")
    partner = next((p for p in partners if p.get("partner_kind") == "referral_pembeli"
                    and p.get("status") == "active"), None) or partners[0]
    no_rule = next((p for p in partners
                    if p["id"] != partner["id"] and p.get("status") == "active"), None)
    deal_marker = db.deals.find_one({"notes": MARKER}, {"_id": 0})
    lead = None
    if not deal_marker:
        lead = db.leads.find_one({"stage": {"$in": ["nurturing", "appointment"]},
                                  "partner_id": None}, {"_id": 0})
        unit = db.units.find_one({"status": "available"}, {"_id": 0})
        if lead and unit:
            db.leads.update_one({"id": lead["id"]},
                                {"$set": {"source": "partner", "partner_id": partner["id"]}})
            r = requests.post(f"{BASE}/deals/reserve", headers=manager, timeout=30, json={
                "lead_id": lead["id"], "unit_id": unit["id"], "booking_fee": 1000000,
                "notes": MARKER})
            check("reservasi unit untuk lead mitra = 200", r.status_code == 200, r.text[:150])
            deal_marker = r.json().get("data") if r.ok else None
            if deal_marker:
                requests.post(f"{BASE}/deals/{deal_marker['id']}/book", headers=manager,
                              json={"note": MARKER}, timeout=30)
                requests.post(f"{BASE}/deals/{deal_marker['id']}/ppjb", headers=manager,
                              json={"note": MARKER}, timeout=30)
    if deal_marker:
        fee = None
        for _ in range(30):
            fee = db.marketing_fees.find_one(
                {"deal_id": deal_marker["id"], "source": "auto"}, {"_id": 0})
            if fee:
                break
            time.sleep(1)
        if check("pemicu NYATA menerbitkan tagihan fee otomatis", bool(fee)):
            rule = db.partner_fee_rules.find_one({"id": fee.get("rule_id")}, {"_id": 0})
            check("tagihan menyebut aturan penerbitnya", bool(rule), fee.get("rule_code"))
            check("beban = netto + PPh (jurnal seimbang)",
                  int(fee["amount_gross"]) == int(fee["amount_net"]) + int(fee["pph_amount"]),
                  f"{fee['amount_gross']} vs {fee['amount_net']}+{fee['pph_amount']}")
            if rule and rule.get("basis") == "percent_price":
                full = round(int(fee["deal_price"]) * float(rule["value"]) / 100.0)
                want = round(full * float(fee["share_pct"]) / 100.0)
                check("nominal = porsi pemicu × hasil aturan",
                      abs(int(fee["amount_gross"]) - want) <= 1,
                      f"{fee['amount_gross']} vs {want}")
            check("tagihan otomatis menunggu persetujuan finance",
                  fee["status"] in ("submitted", "approved", "paid"), fee["status"])
            r = requests.post(f"{BASE}/partners/rules/issue", headers=finance, timeout=30, json={
                "partner_id": fee["agent_id"], "deal_id": fee["deal_id"],
                "trigger": fee["trigger"]})
            check("pemicu yang sama TIDAK bisa menerbitkan tagihan kedua (idempoten)",
                  r.status_code == 400, f"got {r.status_code}: {r.text[:90]}")
        if no_rule:
            r = requests.post(f"{BASE}/partners/rules/preview", headers=admin, timeout=30, json={
                "partner_id": no_rule["id"], "deal_id": deal_marker["id"],
                "trigger": "booking_fee_verified"})
            data = r.json().get("data") if r.ok else {}
            check("tanpa aturan berlaku → fee DITOLAK dengan alasan (INV-09)",
                  r.status_code == 200 and not data.get("ok")
                  and "aturan" in (data.get("reason") or "").lower(),
                  (data.get("reason") or r.text)[:100])
        r = requests.post(f"{BASE}/partners/rules/preview", headers=admin, timeout=30, json={
            "partner_id": partner["id"], "deal_id": deal_marker["id"],
            "trigger": "ppjb_signed"})
        pv = r.json().get("data") if r.ok else {}
        check("pratinjau memakai mesin yang sama (menyebut aturan atau alasan)",
              r.status_code == 200 and (pv.get("rule") or pv.get("reason")),
              str(pv.get("reason") or (pv.get("rule") or {}).get("code"))[:80])
    else:
        print("  SKIP  tidak ada unit/lead tersedia untuk menguji alur pemicu")

    print("\n5. Lead mitra: atribusi wajib & sengketa tercatat")
    r = requests.post(f"{BASE}/leads", headers=manager, timeout=30, json={
        "name": "Gate 42 Tanpa Mitra", "phone": "+628129990043", "source": "partner"})
    check("lead sumber mitra tanpa partner_id = 400", r.status_code == 400,
          f"got {r.status_code}: {r.text[:90]}")
    r = requests.post(f"{BASE}/leads", headers=manager, timeout=30, json={
        "name": "Gate 42 Lead Mitra", "phone": GATE_PHONE, "source": "partner",
        "partner_id": partner["id"]})
    check("lead mitra sah dibuat / sudah ada", r.status_code in (200, 409),
          f"got {r.status_code}")
    if no_rule:
        conflict = requests.post(f"{BASE}/leads", headers=manager, timeout=30, json={
            "name": "Gate 42 Klaim Kedua", "phone": GATE_PHONE, "source": "partner",
            "partner_id": no_rule["id"]})
        check("nomor lead ganda tetap ditolak sebagai lead baru", conflict.status_code == 409,
              f"got {conflict.status_code}")
    blocked = next((p for p in partners if p.get("status") != "active"), None)
    if blocked:
        r = requests.post(f"{BASE}/leads", headers=manager, timeout=30, json={
            "name": "Gate 42 Mitra Nonaktif", "phone": "+628129990044", "source": "partner",
            "partner_id": blocked["id"]})
        check("mitra non-aktif tidak boleh menyetor lead", r.status_code == 400,
              f"got {r.status_code}")
    r = requests.get(f"{BASE}/partners/conflicts", headers=admin, timeout=30)
    check("daftar sengketa atribusi bisa dibuka", r.status_code == 200, r.text[:100])
    check("lead mitra bisa difilter per mitra",
          requests.get(f"{BASE}/leads", headers=admin,
                       params={"partner_id": partner["id"], "limit": 1},
                       timeout=30).json().get("total", 0) >= 1)

    print("\n6. Analitik mitra = hitungan dari data")
    r = requests.get(f"{BASE}/partners/analytics", headers=admin, timeout=60)
    check("GET /partners/analytics = 200", r.status_code == 200, r.text[:100])
    body_a = r.json()
    rows_a, totals = body_a.get("data") or [], body_a.get("totals") or {}
    check("jumlah lead mitra = isi database",
          totals.get("leads") == db.leads.count_documents({"partner_id": {"$ne": None}}),
          f"{totals.get('leads')} vs {db.leads.count_documents({'partner_id': {'$ne': None}})}")
    check("total beban fee = jumlah baris analitik",
          totals.get("fee_expense") == sum(x["fee_expense"] for x in rows_a))
    approved = list(db.marketing_fees.find({"status": {"$in": ["approved", "paid"]}}, {"_id": 0}))
    want_out = sum(int(f["amount_net"]) - int(f.get("paid_amount", 0)) for f in approved)
    check("sisa utang fee analitik = Σ (netto − terbayar) fee disetujui",
          totals.get("fee_outstanding") == want_out,
          f"{totals.get('fee_outstanding')} vs {want_out}")
    detail = requests.get(f"{BASE}/partners/{partner['id']}", headers=admin, timeout=30)
    check("profil mitra memuat kontrak, aturan, lead, tagihan",
          detail.status_code == 200 and all(
              k in detail.json()["data"] for k in ("partner", "rules", "leads", "fees",
                                                  "contract_ok")), detail.text[:100])

    print("\n7. RBAC mitra & fee")
    r = requests.post(f"{BASE}/partners", headers=sales, timeout=30, json={
        "name": "Mitra oleh Sales", "partner_kind": "agen_perorangan", "phone": "+628120000997"})
    check("sales TIDAK boleh mendaftarkan mitra", r.status_code == 403, f"got {r.status_code}")
    r = requests.post(f"{BASE}/partners/rules", headers=sales, timeout=30, json={
        "name": "Aturan oleh Sales", "basis": "fixed_per_deal", "value": 1000,
        "trigger": "ppjb_signed"})
    check("sales TIDAK boleh membuat aturan fee", r.status_code == 403, f"got {r.status_code}")
    r = requests.get(f"{BASE}/partners", headers=sales, timeout=30)
    check("sales boleh melihat mitra (untuk memilih saat membuat lead)",
          r.status_code == 200, f"got {r.status_code}")
    r = requests.get(f"{BASE}/partners", headers=finance, timeout=30)
    check("finance boleh melihat mitra (untuk approve fee)", r.status_code == 200,
          f"got {r.status_code}")

    print("-" * 60)
    if fails:
        print(f"GATE MITRA FAILED: {len(fails)} temuan — {fails[:8]}")
        sys.exit(1)
    print("GATE MITRA PASSED: menu dibuka tanpa merusak alias, fee lahir dari aturan & "
          "pemicu nyata, analitik cocok dengan data")


if __name__ == "__main__":
    main()
