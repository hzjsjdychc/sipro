# Rencana Development Lanjutan — SIPRO (repo `shdjdujd/sipro`)

Problem statement (verbatim):
> "saya ingin anda lanjutkan development dari repo ini https://github.com/shdjdujd — titik berhenti sebelumnya di: All 12 mutations caught (24/24). Re-running the full gate suite after these fixes ... GATE SUMMARY: 23 gates PASS (...) → OVERALL: PASS (23 gates)."

Baseline sesi ini (sudah diverifikasi): restore pod + seed OK, login OK, `bash scripts/run_all_gates.sh` **OVERALL PASS (23 gates)**.

Fokus sesi (keputusan user): **Fase 41 (mesin tahap & aging jadi field nyata) → Fase 42 (Mitra & Fee)**. Integrasi pihak ketiga tetap **simulasi**, utang teknis UI ditunda.

---

## 1) Objectives

1. **Fase 41**: jadikan `stage_entered_at` / `status_entered_at` sebagai **field tersimpan** (bukan turunan per request), agar:
   - aging bisa **di-query** (filter/sort) dan dipakai laporan tanpa hitung ulang,
   - SLA per tahap/status bisa dibaca dari **Config Center** (bukan angka mati di frontend).
2. **Fase 42**: implementasi modul **Mitra & Fee** sesuai `docs/v2/25_PARTNER_SPEC.md` dengan prinsip:
   - tetap pakai koleksi `agents` (jaga invarian GL `marketing_fee.py`), expose alias `/api/partners`,
   - aturan fee + auto-create fee via event bus (tanpa mock),
   - buka 1 menu yang relevan: **Mitra & Fee** (menu lain tetap “Segera Hadir”).
3. Tambah gate baru + mutasi untuk memastikan fase 41–42 punya “gigi”, tanpa merusak 23 gate existing.

---

## 2) Implementation Steps

### Phase 1 — Core POC (isolated) untuk 2 core workflow paling risk (wajib beres sebelum UI besar)

**Core workflow A (Fase 41): stage/status aging tersimpan & konsisten**
- Websearch singkat best-practice: *“MongoDB update denorm stage_entered_at event sourcing”, “FastAPI background jobs for backfill”*.
- POC script `scripts/poc_41_aging_fields.py`:
  1) ambil 20 lead/deal/task/AR/complaint, 
  2) jalankan backfill minimal untuk menulis `*_entered_at` bila kosong,
  3) lakukan 1 transisi lead via API (yang memanggil `lead_lifecycle.record`) dan pastikan field tersimpan ikut berubah,
  4) verifikasi hasil query: filter `stage_age_hours > X` bisa dilakukan (via mongo query / endpoint).

**Core workflow B (Fase 42): auto-create partner fee dari rule saat trigger event**
- POC script `scripts/poc_42_partner_fee.py`:
  1) buat 1 partner (via `/api/partners`), 1 rule fee, 
  2) kaitkan partner ke lead/deal (minimal: set `lead.source='partner'` + `partner_id`),
  3) tembak event trigger yang sudah ada (mis. `deal.booked`/`deal.ppjb`/`deal.ajb` tergantung data seed),
  4) tunggu `dispatch_pending` memproses event,
  5) pastikan `marketing_fees` tercipta (status sesuai toggle `partner.fee_needs_approval`) dan nominal = evaluasi rule.

**Output phase 1**: 2 script POC hijau + tidak merusak gate baseline.

User stories (POC):
1. Sebagai admin, saya ingin menjalankan backfill agar data lama memiliki `stage_entered_at` tanpa merusak data produksi.
2. Sebagai sistem, setiap perpindahan tahap lead harus memperbarui `stage_entered_at` sehingga umur tahap bisa dihitung tanpa `stage_history` scan.
3. Sebagai admin, saya ingin membuat rule fee mitra dan melihat perhitungan fee untuk 1 deal nyata.
4. Sebagai finance, saya ingin fee mitra otomatis dibuat saat trigger tercapai sehingga tidak ada fee yang terlewat.
5. Sebagai QA, saya ingin skrip POC yang bisa dijalankan ulang untuk memastikan core workflow tetap bekerja setelah refactor.

---

### Phase 2 — V1 App Development (implementasi nyata + UI MVP)

#### 2.1 Fase 41 — Data model, backfill, dan API
- Tambah field tersimpan (minimal):
  - `leads.stage_entered_at`, `tasks.status_entered_at`, `ar_invoices.status_entered_at`,
    `complaints.status_entered_at`, `documents.status_entered_at`, `deals.status_entered_at`.
- Update “single source of truth” penulisan transisi:
  - `lead_lifecycle.record()` menulis `stage_entered_at=ts` (selain `stage_changed_at`).
  - Untuk entity lain: pastikan setiap endpoint yang mengubah `status` / `kyc_status` juga menulis `*_entered_at` dan push history tetap.
- Backfill command (idempotent) `scripts/backfill_41_entered_at.py`:
  - isi `*_entered_at` dari: `*_changed_at` → history terakhir → `created_at`.
- SLA dari Config Center:
  - backend endpoint ringan `/api/settings/effective` sudah ada → buat endpoint agregat khusus UI list
    (atau gunakan existing) untuk mengambil SLA map (lead + task + complaint + AR + customer).
  - frontend mengganti literal `slaHours={...}` menjadi nilai dari settings (fallback ke nilai lama).

#### 2.2 Fase 42 — Backend: partners + rules + auto-fee
- Partners API (alias ke `agents`):
  - `routers/partners_router.py`: `GET/POST/PUT /api/partners`, `POST /api/partners/{id}/status`,
    `GET /api/partners/{id}/overview`, `/leads`, `/fees`.
  - Extend schema `agents` dengan field dari spec: `partner_kind`, `entity_type`, `nik`, `address`, `contract{...}`, `settings`, `stats`.
- Fee rules:
  - koleksi baru `partner_fee_rules` + evaluasi rule minimal V1: `percent_price`, `fixed_per_deal` (yang lain ditandai “Segera Hadir” di UI, tapi model siap).
  - validasi prioritas aturan “paling spesifik” + konflik.
- Auto-create fee:
  - handler event baru di `engine.HANDLERS`: saat `deal.booked` / `deal.ppjb` / `deal.ajb` / `payment.paid_off` (sesuai trigger), cek lead punya `partner_id` dan partner aktif + kontrak valid (toggle-driven), lalu create `marketing_fee` berbasis rule.
  - `partner.fee_needs_approval`: bila true → status `submitted` (pakai flow existing); bila false → auto approve (tetap idempotent, pakai `source_event`).
- Pastikan invarian `marketing_fee.py` tidak berubah (akun 6-1200/2-1500/2-1300 tetap).

#### 2.3 Fase 42 — Frontend: buka menu “Mitra & Fee” + hub halaman
- Navigation:
  - ubah item `partners` dari `comingSoon: true` menjadi `path: "/partners"` (tetap jaga total item non-admin ≤ 26).
  - pindahkan “Marketing Fee” dari sidebar (atau jadikan non-menu alias) dan buat:
    - `/partners` (hub) dengan tab: Master Mitra, Aturan Fee, Tagihan Fee (menggunakan komponen existing Marketing Fee sebagai tab), Lead Mitra, Analitik (soon).
    - rute alias `/marketing-fee` **tetap hidup** dan me-render tab Tagihan Fee untuk kompatibilitas.
- Implement UI MVP (reuse DS V2):
  - PartnersList (DataTable + FilterBar + useListQuery) + PartnerProfile (TabPage `?tab=`): Profil, Kontrak & Dokumen, Aturan Fee, Lead, Tagihan Fee.
  - Fee Rules CRUD sederhana (2 basis dulu) + preview perhitungan.
  - Semua elemen interaktif wajib `data-testid` (ikut pola `constants/testIds/*`).

User stories (V1 app):
1. Sebagai owner/admin, saya ingin melihat daftar Mitra (filter jenis/status) dan membuka profil mitra.
2. Sebagai admin, saya ingin menambahkan mitra baru lengkap dengan kontrak sehingga sistem bisa menerima lead dari mitra itu.
3. Sebagai marketing/sales, saya ingin mengaitkan lead ke mitra sehingga atribusi & fee bisa dihitung otomatis.
4. Sebagai finance, saya ingin melihat “Tagihan Fee” mitra, menyetujui, dan membayar seperti alur Marketing Fee yang sudah ada.
5. Sebagai manajer, saya ingin memastikan SLA/aging yang tampil di semua daftar berasal dari Config Center (bukan hardcode), dan umur tahap konsisten.

---

### Phase 3 — Testing, gates, mutation, dan hardening

- Tambah gate baru:
  - `scripts/verify_41.py` + `scripts/mutasi_41.py`: cek field entered_at tersimpan & berubah saat transisi; cek SLA settings dipakai (bukan literal hardcode di file utama).
  - `scripts/verify_partner.py` + `scripts/mutasi_42.py`: cek `/api/partners` ada, rule create, auto-fee tercipta dari event, `/partners` route ada, `/marketing-fee` alias tetap hidup.
  - Daftarkan di `scripts/run_all_gates.sh`.
- Minta `testing_agent_v3` menjalankan:
  1) E2E multi-peran minimal: superadmin (setup) → marketing/sales (buat lead/assign partner) → finance (approve/pay).
  2) full gate suite (23 + 2 gate baru) + mutation scripts.
- Update `test_result.md` (format yaml) + update `plan.md` status fase.

User stories (testing/hardening):
1. Sebagai QA, saya ingin gate mendeteksi bila menu comingSoon diberi path tanpa route atau sebaliknya.
2. Sebagai QA, saya ingin mutasi yang menghapus handler auto-fee membuat gate gagal.
3. Sebagai QA, saya ingin mutasi yang mengembalikan hardcode SLA di frontend membuat gate gagal.
4. Sebagai QA, saya ingin memastikan route alias lama tetap hidup setelah perubahan IA.
5. Sebagai pemilik, saya ingin seluruh suite gate PASS sebelum fitur dianggap selesai.

---

## 3) Next Actions (urutan eksekusi)

1. Implement POC scripts Phase 1 dan jalankan sampai stabil.
2. Fase 41 backend: add stored fields + update writer paths + backfill script.
3. Fase 41 frontend: SLA from Config Center (remove hardcode literals).
4. Fase 42 backend: partners router + fee rules + event handlers auto-fee.
5. Fase 42 frontend: `/partners` hub + migrate Marketing Fee into tab + keep `/marketing-fee` alias.
6. Tambah verify+mutasi gates fase 41–42; pastikan `bash scripts/run_all_gates.sh` PASS.
7. Delegate E2E ke testing agent, perbaiki temuan, update `test_result.md` + `plan.md`.

---

## 4) Success Criteria

- **Fase 41**
  - `*_entered_at` tersimpan pada entity yang relevan; transisi mengubah field ini dengan benar.
  - SLA/aging UI membaca dari Config Center (fallback jelas), bukan angka hardcode.
  - Bisa query/filter/sort berdasar umur tahap tanpa hitung ulang di setiap request.

- **Fase 42**
  - `/api/partners` berfungsi (CRUD minimal) dengan data tersimpan di `agents`.
  - `partner_fee_rules` minimal (percent + fixed) berjalan; fee otomatis tercipta dari event nyata.
  - Halaman `/partners` tersedia; menu “Mitra & Fee” terbuka; `/marketing-fee` tetap hidup sebagai alias.

- **Quality gates**
  - `bash scripts/run_all_gates.sh` PASS.
  - `mutasi_41.py` dan `mutasi_42.py` menangkap regresi utama.
  - E2E multi-peran oleh testing agent PASS.
