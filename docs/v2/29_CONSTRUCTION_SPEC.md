# 29 — SPEC KONSTRUKSI UNIT-CENTRIC (konsolidasi 6 menu → 1 hub)

> Menutup CR-24, CR-25, CR-27, CR-29, CR-32. Permintaan owner: *"progress & mutu, kalibrasi jadwal, kalender jadwal itu domain yang sama namun dipecah sehingga user bingung"*, *"harus unit centric"*, *"papan mandor digabung saja dengan laporan dan analitik"*, *"perizinan/buku harian jangan menu tersendiri"*.
> **Yang sudah kuat dan HARUS dipertahankan** (Fase 31–38): `build_engine.py`, `build_schedules`, `build_items`, `build_calendar.py`, `build_calibration.py`, `build_analytics.py`, `build_bulk.py`, `opname.py`, `inspections`, `punch_items`, `site_diaries`.

## 1. Struktur menu baru
**Proyek › Pembangunan** (satu halaman, tab tersinkron URL):

| Tab | Isi | Sumber lama |
|---|---|---|
| **Papan Unit** (default) | tabel unit + status bangun + progres + tenggat terdekat + PIC; filter cluster/blok/status/telat | `ConstructionPage.js` (kartu → tabel) |
| **Kalender** | kalender jadwal (bulan/minggu/hari) lintas unit + bentrok | `BuildCalendarPage.js` |
| **Lapangan** | buku harian, punch list, foto, absensi mandor, cuaca | `FieldPage.js` + Papan Mandor |
| **Mutu & Inspeksi** | QC, inspeksi terjadwal, hasil, temuan | `inspections`, QC |
| **Analitik & Kalibrasi** | analitik telat, rekomendasi kalibrasi template, rapor mingguan | `BuildCalibrationPage.js`, `build_analytics.py`, `workhub_report.py` |
| **Template Jadwal** | master template langkah (bukan menu utama lagi) | `build_templates` |

**Perizinan** (CR-25): tidak lagi menu utama. Ditempatkan sebagai **tab "Dokumen & Perizinan"** pada Unit 360 dan `/projects/:id`; daftar global tetap bisa dilihat lewat **Dokumen** dengan filter `permit`.

## 2. Lifecycle pembangunan per unit (navigasi utama user)
```
not_started ──(jadwalkan)─► scheduled ──(mulai bangun)─► in_progress ──(progres 100% + QC lulus)─► completed ──(BAST)─► handed_over
     │                                              │
     └────────────────────────────────────┴──► on_hold (wajib alasan + tanggal tinjau)
```
**Gerbang bukti (mempertahankan aturan Fase 31–33):** progres hanya naik dari **submission terverifikasi** (foto + langkah), uang subkon hanya mengikuti item pekerjaan terverifikasi, tanggal hanya bisa digeser lewat mekanisme Fase 34 (beralasan + audit).
**Pemicu bisnis:** `payment_plans` cash keras/bertahap menyatakan *"pembangunan mulai setelah DP 80% diterima"* `[DOC]` ⇒ tombol **Mulai Bangun** memeriksa termin DP `paid`; bila belum, tampilkan alasan penolakan yang jelas (bukan tombol mati tanpa penjelasan).

## 3. Halaman kerja unit (klik unit dari Papan Unit)
Membuka **Unit 360 › tab Pembangunan** berisi: kurva-S rencana vs realisasi, daftar langkah (status, tenggat, PIC, bukti), aksi `input progres`, `ajukan verifikasi`, `QC`, `inspeksi`, `punch`, `foto`, `geser tanggal (beralasan)`, `laporan mingguan unit`.

## 4. Tabel-first (CR-27)
Papan Unit memakai `DataTable` ([23](23_IA_UX_BLUEPRINT.md) §5) dengan kolom: `unit, cluster/blok, tipe, status jual, status bangun, progres %, rencana %, deviasi, langkah aktif, tenggat, umur telat, PIC, bukti terakhir`. Baris telat diberi penanda teks + warna. Detail = halaman, bukan drawer (CR-29).

## 5. Perizinan menempel pada objek (CR-25)
`permits` diperluas: `scope(project|cluster|block|unit)`, `scope_id`, `requirement_code` (tautan ke master dokumen), `expiry_at`, `reminder_days`. Izin yang belum ada bisa **memblokir** aksi bila `[CFG] permit.block_build_without=["IMB/PBG"]` — default **peringatan**, bukan blokir (agar tidak menghentikan operasional yang sudah berjalan).

## 6. Definition of Done
1. Menu konstruksi dari 6 → 1 (dengan 6 tab); tidak ada fitur lama yang hilang — dibuktikan checklist fitur lama vs baru.
2. Papan Unit adalah tabel dengan filter/sort/search + kolom deviasi & umur telat.
3. Semua aksi konstruksi bisa dicapai dari Unit 360 (unit-centric) — diuji lewat user story.
4. Perizinan & buku harian tidak lagi menu terpisah, tetapi tetap bisa dicari global.
5. `verify_31..37`, `verify_ui_surfaces` dan seluruh 19 gate **tetap PASS** (tidak boleh ada regresi).
