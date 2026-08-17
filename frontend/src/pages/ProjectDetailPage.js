import React, { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import useTabParam from "@/hooks/useTabParam";
import EntityHeader from "@/components/patterns/EntityHeader";
import MetricCard from "@/components/patterns/MetricCard";
import StructureTab from "@/components/projects/StructureTab";
import UnitsTab from "@/components/projects/UnitsTab";
import { LoadingCards, ErrorState } from "@/components/patterns/StateViews";
import { useAuth } from "@/context/AuthContext";
import api from "@/services/apiClient";
import { formatIDR } from "@/utils/formatters";
import { MASTERPLAN } from "@/constants/testIds";

/**
 * Halaman kanonik PROYEK (Fase 39) — tempat mengelola hierarki
 * proyek → cluster → blok → unit yang sebelumnya tidak ada sama sekali (audit CR-05).
 */
export default function ProjectDetailPage() {
  const { id } = useParams();
  const [tab, setTab] = useTabParam("structure");
  const { user } = useAuth();
  const canManage = ["owner", "super_admin", "project_manager"].includes(user?.role);
  const [tree, setTree] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const res = await api.get(`/masterplan/projects/${id}/tree`);
      setTree(res.data.data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Gagal memuat struktur proyek.");
    } finally { setLoading(false); }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingCards count={4} />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const project = tree?.project || {};
  const stats = project.unit_stats || {};
  const soldLike = (stats.booked || 0) + (stats.sold || 0) + (stats.handed_over || 0);

  return (
    <div data-testid={MASTERPLAN.projectPage} className="space-y-5">
      <EntityHeader
        kicker="Proyek"
        title={project.name || "Proyek"}
        subtitle={project.location}
        backLabel="Daftar proyek"
        chips={[
          { label: "Kode", value: project.code },
          { label: "Cluster", value: tree?.totals?.clusters || 0 },
          { label: "Blok", value: tree?.totals?.blocks || 0 },
          { label: "Unit", value: tree?.totals?.units || 0 },
          { label: "Progres konstruksi", value: `${project.construction_progress || 0}%` },
        ]} />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Unit tersedia" value={stats.available || 0} tone="emerald" />
        <MetricCard label="Dipegang / booking" value={(stats.reserved || 0) + (stats.booked || 0)}
          tone="amber" />
        <MetricCard label="Terjual (kumulatif)" value={soldLike} tone="primary"
          hint={`absorpsi ${stats.absorption_pct || 0}%`} />
        <MetricCard label="Nilai unit" value={formatIDR(stats.value || 0)} tone="indigo" />
      </div>

      <Tabs value={tab} onValueChange={setTab} className="space-y-4">
        <TabsList>
          <TabsTrigger data-testid={MASTERPLAN.tabStructure} value="structure">
            Struktur (Cluster → Blok)
          </TabsTrigger>
          <TabsTrigger data-testid={MASTERPLAN.tabUnits} value="units">Unit</TabsTrigger>
        </TabsList>
        <TabsContent value="structure">
          <StructureTab tree={tree} projectId={id} onChanged={load} canManage={canManage} />
        </TabsContent>
        <TabsContent value="units">
          <UnitsTab projectId={id} clusters={tree?.clusters || []} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
