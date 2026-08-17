import React from "react";
import { Handshake } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import FeesPanel from "@/components/marketingFee/FeesPanel";
import AgentsPanel from "@/components/marketingFee/AgentsPanel";
import { MFEE } from "@/constants/testIds";

/**
 * Marketing Fee (Fase 27) — fee mitra EKSTERNAL: agen properti, kantor broker,
 * referral pembeli, influencer. Berbeda dari Komisi sales internal.
 * Utang fee dibukukan di akun 2-1500, bebannya di 6-1200.
 */
export default function MarketingFeePage() {
  return (
    <div data-testid={MFEE.page} className="space-y-5">
      <div className="flex items-center gap-2">
        <Handshake className="h-5 w-5 text-primary" />
        <div>
          <h1 className="font-heading text-xl font-semibold">Marketing Fee Agen & Mitra</h1>
          <p className="text-xs text-muted-foreground">
            Mitra eksternal (agen/broker/referral) · beban 6-1200, utang fee 2-1500,
            PPh dipotong ke 2-1300.
          </p>
        </div>
      </div>

      <Tabs defaultValue="fees">
        <TabsList>
          <TabsTrigger data-testid={MFEE.tabFees} value="fees">Pengajuan Fee</TabsTrigger>
          <TabsTrigger data-testid={MFEE.tabAgents} value="agents">Master Agen</TabsTrigger>
        </TabsList>
        <TabsContent value="fees" className="mt-4"><FeesPanel /></TabsContent>
        <TabsContent value="agents" className="mt-4"><AgentsPanel /></TabsContent>
      </Tabs>
    </div>
  );
}
