import React from "react";
import { CalendarDays, ClipboardList, HardHat, LayoutGrid, SlidersHorizontal } from "lucide-react";

import TabPage from "@/components/patterns/TabPage";
import AllUnitsTab from "@/components/projects/AllUnitsTab";
import ConstructionPage from "@/pages/ConstructionPage";
import BuildCalendarPage from "@/pages/BuildCalendarPage";
import FieldPage from "@/pages/FieldPage";
import BuildCalibrationPage from "@/pages/BuildCalibrationPage";
import { HUB } from "@/constants/testIds";

/**
 * BuildHubPage (`/build`) — hub **Pembangunan** (IA V2 §3).
 *
 * Empat menu lama (Progres & Mutu · Kalender Jadwal · Kalibrasi Jadwal · Buku Harian & Punch)
 * dilebur menjadi satu pintu dengan tab, ditambah “Papan Unit”: tabel unit lintas proyek yang
 * bisa dicari/difilter (mis. semua unit ber-status QC hold) — sebelumnya tidak ada satu pun
 * layar yang bisa menjawab pertanyaan itu.
 *
 * Rute lama (`/construction`, `/build-calendar`, `/build-calibration`, `/field`) TETAP hidup
 * supaya tautan lama, pintasan notifikasi, dan deep-link `?tab=` di dalamnya tidak rusak.
 * Penanda tab hub memakai `?hub=` agar tidak bertabrakan dengan `?tab=` milik halaman di
 * dalamnya (ConstructionPage sudah memakai `?tab=` sejak Fase 32).
 */
export default function BuildHubPage() {
  return (
    <div data-testid={HUB.build} className="space-y-4">
      <div>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">Pembangunan</h1>
        <p className="text-sm text-muted-foreground">
          Satu pintu pembangunan: papan unit lintas proyek, progres &amp; mutu, jadwal, laporan
          lapangan, dan kalibrasi template jadwal.
        </p>
      </div>
      <TabPage paramKey="hub" tabs={[
        { key: "unit", label: "Papan Unit", icon: LayoutGrid, content: <AllUnitsTab /> },
        { key: "progres", label: "Progres & Mutu", icon: HardHat, content: <ConstructionPage /> },
        { key: "kalender", label: "Kalender Jadwal", icon: CalendarDays,
          content: <BuildCalendarPage /> },
        { key: "lapangan", label: "Buku Harian & Punch", icon: ClipboardList,
          content: <FieldPage /> },
        { key: "kalibrasi", label: "Kalibrasi Jadwal", icon: SlidersHorizontal,
          content: <BuildCalibrationPage /> },
      ]} />
    </div>
  );
}
