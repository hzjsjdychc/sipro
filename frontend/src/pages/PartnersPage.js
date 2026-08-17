import React from "react";
import { Banknote, Handshake, ListChecks, Scale, TrendingUp } from "lucide-react";

import TabPage from "@/components/patterns/TabPage";
import PartnersListTab from "@/components/partners/PartnersListTab";
import FeeRulesTab from "@/components/partners/FeeRulesTab";
import PartnerAnalyticsTab from "@/components/partners/PartnerAnalyticsTab";
import ConflictsTab from "@/components/partners/ConflictsTab";
import FeesPanel from "@/components/marketingFee/FeesPanel";
import { PARTNERS } from "@/constants/testIds";

/**
 * PartnersPage (`/partners`) — hub **Mitra &amp; Fee** (Fase 42).
 *
 * Menu ini sebelumnya berstatus “Segera Hadir” (terkunci, tanpa route) dan yang ada hanyalah
 * menu “Marketing Fee” berisi master agen + pengajuan fee manual. Sesuai peta navigasi
 * (`docs/v2/40_PETA_NAV_V2.md`), Marketing Fee kini menjadi tab **Tagihan Fee** di dalam hub
 * ini — rutenya (`/marketing-fee`) SENGAJA tetap hidup sebagai alias supaya notifikasi,
 * tugas, dan bookmark lama tidak rusak.
 *
 * Penanda tab memakai `?hub=` (bukan `?tab=`) agar tidak bertabrakan dengan tab di dalam
 * halaman anak.
 */
export default function PartnersPage() {
  return (
    <div data-testid={PARTNERS.page} className="space-y-4">
      <div>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">Mitra &amp; Fee</h1>
        <p className="text-sm text-muted-foreground">
          Mitra eksternal (agen, broker, aggregator, referral): kontrak, aturan fee, tagihan
          fee, sengketa atribusi lead, dan kinerja tiap mitra. Utang fee dibukukan di akun
          2-1500, bebannya 6-1200, PPh dipotong ke 2-1300.
        </p>
      </div>
      <TabPage paramKey="hub" testId={PARTNERS.hubTab} tabs={[
        { key: "mitra", label: "Master Mitra", icon: Handshake, content: <PartnersListTab /> },
        { key: "aturan", label: "Aturan Fee", icon: ListChecks, content: <FeeRulesTab /> },
        { key: "tagihan", label: "Tagihan Fee", icon: Banknote, content: <FeesPanel /> },
        { key: "sengketa", label: "Sengketa Atribusi", icon: Scale, content: <ConflictsTab /> },
        { key: "analitik", label: "Analitik Mitra", icon: TrendingUp,
          content: <PartnerAnalyticsTab /> },
      ]} />
    </div>
  );
}
