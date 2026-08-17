#!/usr/bin/env python3
"""verify_ia_v2.py — GATE IA & Design System V2 (Fase 40).

Kenapa gate ini ada (cacat NYATA yang sudah pernah terjadi di repo ini):

  1. **Menu dilebur, fitur hilang tanpa sadar.** Fase 40c membuang enam pintu menu
     (`/deals`, `/construction`, `/build-calendar`, `/build-calibration`, `/field`,
     `/permits`) ke dalam hub bertab. Kalau rutenya juga ikut dihapus, semua notifikasi &
     tugas yang SUDAH terbit (menyimpan tautan ke rute itu) menjadi rusak. Gate menuntut:
     hilang dari sidebar, TETAP ADA sebagai route.
  2. **Menu "Segera Hadir" yang punya route** = halaman kosong yang terasa seperti bug.
     Gate menuntut item comingSoon tidak punya `path` sama sekali.
  3. **Daftar yang belum dimigrasikan.** Sebelum Fase 40, tujuh daftar transaksional tidak
     punya filter/sort/ekspor dan sebagian mengurutkan data terpaginasi di browser (bohong).
     Gate menuntut setiap daftar utama memakai `DataTable` + `FilterQuery` (useListQuery) dan
     TIDAK lagi memakai `<Table>` mentah.
  4. **KPI yang tidak bisa ditelusuri.** Blueprint §7.3: "angka KPI wajib bisa di-drill-down;
     tanpa itu dianggap belum selesai". Gate memanggil API sungguhan: setiap KPI Beranda
     harus punya `drill`, rute tujuannya harus ada, dan untuk KPI berbasis hitungan tugas
     jumlah baris hasil filter HARUS SAMA dengan angka KPI-nya (kalau beda, angka bohong).
  5. **Peta menu membusuk.** `navMigrationMap.js` dipakai dialog "menu saya ke mana?"; setiap
     tujuannya harus rute yang benar-benar ada, dan dialognya harus terpasang di Sidebar.

Exit !=0 bila ada FAIL. Uji-mutasi: `scripts/mutasi_40_ia.py`.
"""
import pathlib
import re
import sys

import requests

BASE = "http://localhost:8001/api"
PW = "Sipro#2026"
ROOT = pathlib.Path(__file__).resolve().parent.parent
FE = ROOT / "frontend" / "src"
fails = []

# Menu yang dilebur ke hub: WAJIB hilang dari sidebar, WAJIB tetap punya route (alias).
MERGED = ["/deals", "/construction", "/build-calendar", "/build-calibration", "/field",
          "/permits"]
# Batas jumlah item menu non-admin (blueprint §3: 33 → 26). Angka nyata sesudah Fase 40c = 26.
MAX_NONADMIN_ITEMS = 26
# Daftar transaksional yang WAJIB memakai pola tabel pro.
LISTS = {
    "pages/LeadsPage.js": "lead",
    "components/sales/DealsListTab.js": "deal",
    "components/customers/CustomersListTab.js": "pembeli",
    "components/projects/AllUnitsTab.js": "unit",
    "components/work/TasksListTab.js": "tugas",
    "components/finance/ArPanel.js": "piutang (AR)",
    "components/documents/DocumentsListTab.js": "dokumen",
    "components/complaints/ComplaintsListTab.js": "komplain",
}


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)
    return cond


def read(rel):
    p = FE / rel
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def login(email):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": PW}, timeout=20)
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def nav_items(nav_src):
    """[(id, path|None, comingSoon, group)] dari NAV_STRUCTURE (regex, KODE menang)."""
    items, group = [], "?"
    body = nav_src.split("export const NAV_STRUCTURE", 1)[-1].split("export function", 1)[0]
    for line in body.splitlines():
        g = re.search(r'groupId:\s*"([^"]+)"', line)
        if g:
            group = g.group(1)
        mid = re.search(r'id:\s*"([^"]+)"', line)
        if not mid or g:
            if not (mid and not g):
                continue
        # item bisa memanjang beberapa baris; ambil blok sampai penutupnya
        items.append({"id": mid.group(1), "line": line, "group": group})
    return items


def main():
    nav = read("config/navigationConfig.js")
    app = read("App.js")
    routes = set(re.findall(r'<Route\s+path="([^"]+)"', app))

    print("\n1. Peleburan menu (fitur tidak boleh hilang)")
    body = nav.split("export const NAV_STRUCTURE", 1)[-1].split("export function", 1)[0]
    nav_paths = set(re.findall(r'path:\s*"([^"]+)"', body))
    for p in MERGED:
        check(f"menu lama '{p}' tidak lagi di sidebar", p not in nav_paths)
        check(f"rute alias '{p}' TETAP hidup", p in routes)
    check("hub Pembangunan '/build' ada di sidebar", "/build" in nav_paths)
    check("hub Pembangunan '/build' punya route", "/build" in routes)
    meta = nav.split("PAGE_META", 1)[-1].split("const ALL", 1)[0]
    check("'/build' punya PAGE_META (judul TopBar resolve)", '"/build"' in meta)

    print("\n2. Item 'Segera Hadir' tidak boleh bisa diklik")
    soon_blocks = [b for b in re.split(r"\n\s{4,6}\{", body) if "comingSoon: true" in b]
    check("ada item comingSoon (peta jalan jujur)", len(soon_blocks) >= 1,
          f"{len(soon_blocks)} item")
    for b in soon_blocks:
        label = (re.search(r'label:\s*"([^"]+)"', b) or [None, "?"])[1]
        check(f"comingSoon '{label}' tanpa path", "path:" not in b)
        check(f"comingSoon '{label}' menjelaskan kapan (note)", "note:" in b)

    print("\n3. Jumlah item menu (33 → 26) & struktur grup")
    admin = {p for p in nav_paths if p.startswith("/admin")}
    non_admin = nav_paths - admin
    check(f"item menu non-admin ≤ {MAX_NONADMIN_ITEMS}", len(non_admin) <= MAX_NONADMIN_ITEMS,
          f"{len(non_admin)} item")
    check("buildNavGroups menyembunyikan grup kosong",
          "if (roleItems.length) result.push" in nav)
    check("countNavItems tersedia untuk audit", "export function countNavItems" in nav)

    print("\n4. Hub bertab memakai penanda ?hub= (tidak bentrok dengan ?tab= di dalamnya)")
    for page, testid in (("pages/BuildHubPage.js", "HUB.build"),
                         ("pages/CustomersPage.js", "CUSTOMERS.page"),
                         ("pages/DocumentsPage.js", "DOCS.page")):
        src = read(page)
        check(f"{pathlib.Path(page).name} memakai TabPage paramKey=\"hub\"",
              'paramKey="hub"' in src and "TabPage" in src)
        check(f"{pathlib.Path(page).name} punya data-testid halaman", testid.split(".")[0] in src)

    print("\n5. Semua daftar utama = tabel pro (cari + filter + sort + ekspor + paginasi)")
    toolbar = read("components/patterns/DataTableToolbar.js")
    check("toolbar tabel punya kotak cari ber-testid",
          "data-testid={testIds.search || DT.search}" in toolbar)
    check("toolbar tabel punya ekspor CSV", "testIds.export || DT.export" in toolbar)
    check("toolbar tabel punya pemilih kolom", "testIds.columns || DT.columns" in toolbar)
    check("tabel punya sort per kolom ber-testid", "${DT.sort}-${key}" in read("components/patterns/DataTable.js"))
    for rel, label in LISTS.items():
        src = read(rel)
        name = pathlib.Path(rel).name
        if not check(f"{name} ada", bool(src)):
            continue
        check(f"{name} memakai DataTable", "DataTable" in src)
        check(f"{name} memakai FilterBar", "FilterBar" in src)
        check(f"{name} query hidup di URL (useListQuery)", "useListQuery" in src)
        check(f"{name} tidak lagi memakai <Table> mentah",
              "@/components/ui/table" not in src, label)

    print("\n6. Halaman yang dipakai GANDA (rute lama + tab hub) tidak boleh menendang pemakai")
    # Cacat NYATA yang ditemukan lewat uji browser sesi ini: halaman yang disematkan di hub
    # menulis keadaannya ke URL dengan pathname HARDCODE, sehingga `/build?hub=kalender`
    # langsung terpental ke `/build-calendar` (tab yang baru diklik hilang).
    for rel, legacy in (("pages/BuildCalendarPage.js", "/build-calendar"),
                        ("pages/ConstructionPage.js", "/construction")):
        src = read(rel)
        name = pathlib.Path(rel).name
        check(f"{name} tidak menulis pathname hardcode",
              f'pathname: "{legacy}"' not in src, legacy)
        check(f"{name} memakai selfPath(loc.pathname, …)", "selfPath(loc.pathname" in src)
    tabpage = read("components/patterns/TabPage.js")
    # Cacat kedua: filter satu tab bocor ke tab lain (mis. `project_id` dari tab Kalender
    # terbaca tab Papan Unit sebagai filter proyek yang tidak pernah dipilih pemakai).
    check("TabPage memulai query BERSIH saat pindah tab",
          "const next = new URLSearchParams();" in tabpage)
    check("TabPage tetap menjaga penanda tab yang lebih luar (hub)",
          "TAB_MARKERS" in tabpage and 'if (marker === paramKey) break;' in tabpage)

    print("\n7. Peta menu lama→baru bisa dicapai DARI DALAM aplikasi")
    mig = read("config/navMigrationMap.js")
    sidebar = read("components/layout/Sidebar.js")
    check("navMigrationMap.js ada", bool(mig))
    # Diperiksa pada PEMAKAIANNYA (JSX), bukan sekadar ada string namanya: uji-mutasi M8
    # membuktikan komponennya bisa dicabut dari tampilan sementara `import`-nya tertinggal,
    # dan pemeriksaan longgar tetap hijau padahal peta menu sudah tak bisa dibuka pemakai.
    check("dialog peta menu terpasang di Sidebar", "<NavMigrationDialog" in sidebar)
    check("dokumen peta nav ada", (ROOT / "docs/v2/40_PETA_NAV_V2.md").exists())
    targets = re.findall(r'to:\s*"([^"]+)"', mig)
    check("peta menu punya minimal 12 baris", len(targets) >= 12, f"{len(targets)} baris")
    for t in targets:
        base = t.split("?")[0]
        check(f"tujuan peta '{t}' punya route", base in routes)

    print("\n8. KPI Beranda WAJIB bisa di-drill-down (bukti API, bukan bacaan kode)")
    home_js = read("pages/Home.js")
    check("Home.js meneruskan drill ke KpiCard", "to={k.drill}" in home_js)
    check("KpiCard mendukung tautan drill", 'data-drill={to}' in read("components/patterns/KpiCard.js"))
    for email in ("superadmin@sipro.co.id", "sales@sipro.co.id", "finance@sipro.co.id",
                  "pm@sipro.co.id", "manager@sipro.co.id"):
        h = login(email)
        data = requests.get(f"{BASE}/work/home", headers=h, timeout=30).json()["data"]
        kpis = data.get("kpis") or []
        check(f"{email}: ada KPI", len(kpis) >= 3, f"{len(kpis)} kartu")
        for k in kpis:
            drill = k.get("drill") or ""
            if not check(f"{email}: KPI '{k['label']}' punya drill", bool(drill)):
                continue
            path, _, qs = drill.partition("?")
            check(f"{email}: drill '{drill}' menuju route yang ada", path in routes)
            # KPI tugas: jumlah baris hasil filter harus SAMA dengan angka KPI-nya.
            if path == "/tasks" and "bucket=" in qs:
                params = dict(p.split("=", 1) for p in qs.split("&") if "=" in p)
                params.pop("tab", None)
                r = requests.get(f"{BASE}/work/tasks", headers=h,
                                 params={**params, "limit": 1}, timeout=30)
                total = r.json().get("total") if r.ok else f"HTTP {r.status_code}"
                check(f"{email}: angka '{k['label']}'={k['value']} sama dengan hasil filter",
                      total == k["value"], f"daftar mengembalikan {total}")
        team = data.get("team")
        if team:
            check(f"{email}: angka tim punya drill", bool(team.get("drills")))

    print("-" * 60)
    if fails:
        print(f"GATE IA V2 FAILED: {len(fails)} temuan — {fails[:8]}")
        sys.exit(1)
    print("GATE IA V2 PASSED: menu dilebur tanpa fitur hilang, daftar seragam, KPI bisa "
          "ditelusuri sampai barisnya")


if __name__ == "__main__":
    main()
