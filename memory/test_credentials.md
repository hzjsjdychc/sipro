# Kredensial Uji SIPRO (demo seed)

Sandi SEMUA akun demo: `Sipro#2026`

| Peran | Email | Catatan |
|---|---|---|
| Super Admin | superadmin@sipro.co.id | akses penuh + admin sistem |
| Owner/Direksi | owner@sipro.co.id | dashboard direksi, laporan |
| Manajer Sales | manager@sipro.co.id | approve diskon, pipeline |
| Marketing Admin | marketing@sipro.co.id | leads, kampanye |
| Sales | sales@sipro.co.id | leads/deal miliknya (uji RBAC 403 konstruksi) |
| Sales 2 | sales2@sipro.co.id | uji isolasi antar sales |
| Finance | finance@sipro.co.id | pembayaran, kas, GL |
| Manajer Proyek | pm@sipro.co.id | konstruksi, kalender, kalibrasi |
| Pelaksana Lapangan | site@sipro.co.id | Papan Mandor, progres (tanpa tombol kalibrasi) |

## Portal Pelanggan
- Login OTP; **OTP master pengujian = `000000`** (env `PORTAL_MASTER_OTP`).
- Nomor/nama pelanggan demo dapat dilihat di halaman Customer (hasil seed `customers`).

## Catatan pengujian
- Tidak ada backdoor auth. Halaman login punya tombol **"Masuk cepat"** yang hanya memanggil
  `POST /api/auth/login` biasa dengan akun demo di atas (boleh dihapus sebelum go-live).
- Bersihkan `localStorage` saat berganti peran agar sesi lama tidak terbawa.
- Login endpoint: `POST {REACT_APP_BACKEND_URL}/api/auth/login` body `{"email": "...", "password": "Sipro#2026"}`.
