// Fase 41 — SATU definisi filter "umur/SLA" + format jam untuk SEMUA daftar.
//
// Kenapa dipusatkan: sebelum Fase 41 setiap daftar menulis ambang SLA-nya sendiri di dalam
// komponen (72 jam di Lead, 48 di Tugas & Komplain, 168 di Deal, 336 di Pembeli, 720 di AR).
// Akibatnya kebijakan tidak bisa diubah tanpa deploy, dan dua layar bisa menyebut hal yang
// sama dengan angka berbeda. Ambang kini datang DARI SERVER pada tiap baris
// (`stage_sla_hours`, `sla_state`) sesuai Pusat Konfigurasi; berkas ini hanya menyimpan
// pilihan FILTER-nya supaya kalimatnya seragam.

export const SLA_FILTER_OPTIONS = [
  { value: "over", label: "Lewat SLA tahap" },
  { value: "over2", label: "Lewat 2× SLA tahap" },
  { value: "ok", label: "Masih dalam SLA" },
  { value: "none", label: "Tanpa SLA (tahap akhir)" },
];

/** Definisi filter untuk `FilterBar`. `extra` = pilihan khusus daftar itu (mis. tenggat tugas). */
export const slaFilter = (extra = []) => ({
  key: "sla", label: "Umur / SLA", type: "select",
  options: [...extra, ...SLA_FILTER_OPTIONS],
});

/** 0.4 → "24m", 30 → "30j", 60 → "2h 12j" (dipakai kolom umur & laporan umur tahap). */
export function formatHours(hours) {
  if (hours === null || hours === undefined || hours === "") return "-";
  const h = Number(hours);
  if (!Number.isFinite(h)) return "-";
  if (h < 1) return `${Math.max(1, Math.round(h * 60))}m`;
  if (h < 48) return `${Math.round(h)}j`;
  const days = Math.floor(h / 24);
  const rest = Math.round(h % 24);
  return rest ? `${days}h ${rest}j` : `${days}h`;
}

export const SLA_STATE_LABEL = {
  ok: "dalam SLA",
  over: "lewat SLA",
  over2: "lewat 2× SLA",
  none: "tanpa SLA",
};

export const SLA_STATE_TONE = {
  ok: "text-foreground",
  over: "text-amber-700",
  over2: "text-rose-700",
  none: "text-muted-foreground",
};
