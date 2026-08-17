import React, { useCallback, useEffect, useState } from "react";
import { Calculator, Plus, Trash2, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import MetricCard from "@/components/patterns/MetricCard";
import EmptyState from "@/components/patterns/EmptyState";
import { LoadingCards, ErrorState } from "@/components/patterns/StateViews";
import ProjectSelect from "@/components/construction/ProjectSelect";
import AddBoQItemDialog from "@/components/boq/AddBoQItemDialog";
import BoQStepMapDialog from "@/components/boq/BoQStepMapDialog";
import CostControlPanel from "@/components/boq/CostControlPanel";
import { useAuth } from "@/context/AuthContext";
import { formatIDR, formatNumber } from "@/utils/formatters";
import api from "@/services/apiClient";
import { PROCUREMENT, COST } from "@/constants/testIds";
import { useReference } from "@/context/ReferenceContext";

const MANAGE = ["owner", "super_admin", "project_manager"];

export default function BoQPage() {
  const { labelOf } = useReference();
  const { user } = useAuth();
  const canManage = MANAGE.includes(user?.role);
  const [projectId, setProjectId] = useState(null);
  const [items, setItems] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [mapFor, setMapFor] = useState(null);

  const load = useCallback(async () => {
    if (!projectId) return;
    setLoading(true); setError("");
    try {
      const [ri, rs] = await Promise.all([
        api.get("/boq/items", { params: { project_id: projectId } }),
        api.get("/boq/summary", { params: { project_id: projectId } }),
      ]);
      setItems(ri.data); setSummary(rs.data.data);
    } catch (e) { setError(e?.response?.data?.detail || "Gagal memuat data RAB."); }
    finally { setLoading(false); }
  }, [projectId]);
  useEffect(() => { load(); }, [load]);

  const del = async (id) => {
    try { await api.delete(`/boq/items/${id}`); toast.success("Item dihapus."); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Gagal menghapus item."); }
  };

  return (
    <div data-testid={PROCUREMENT.boqPage} className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Calculator className="h-5 w-5 text-primary" />
          <h1 className="font-heading text-xl font-semibold">RAB / Bill of Quantities</h1>
        </div>
        <ProjectSelect value={projectId} onChange={setProjectId} testId={PROCUREMENT.boqProjectSelect} />
      </div>

      {!projectId ? (
        <EmptyState icon={Calculator} title="Pilih proyek"
          description="Pilih proyek untuk melihat anggaran biaya (RAB) dan kontrol biaya." />
      ) : (
        <Tabs defaultValue="items">
          <TabsList>
            <TabsTrigger data-testid={COST.itemsTab} value="items">Rincian RAB</TabsTrigger>
            <TabsTrigger data-testid={COST.controlTab} value="control">Kendali Biaya</TabsTrigger>
          </TabsList>

          <TabsContent value="items" className="mt-4 space-y-5">
            {loading ? <LoadingCards count={4} /> : error ? <ErrorState message={error} onRetry={load} /> : (
              <>
                {summary ? (
                  <>
                    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                      <MetricCard label="Anggaran (RAB)" value={summary.budget} tone="primary" format="idr" />
                      <MetricCard label="Komitmen (PO)" value={summary.committed} tone="indigo" format="idr" />
                      <MetricCard label="Realisasi (Tagihan)" value={summary.actual} tone="amber" format="idr" />
                      <MetricCard label="Sisa Anggaran" value={summary.remaining} tone={summary.remaining < 0 ? "rose" : "emerald"} format="idr" />
                    </div>
                    {summary.over_budget ? (
                      <div data-testid="boq-over-budget" className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
                        <AlertTriangle className="h-4 w-4" /> Komitmen PO melebihi anggaran RAB proyek ini.
                      </div>
                    ) : null}
                    {summary.categories?.length ? (
                      <div className="flex flex-wrap gap-2">
                        {summary.categories.map((c) => (
                          <span key={c.category} className="rounded-full border bg-card px-3 py-1 text-xs">
                            <span className="text-muted-foreground">{labelOf("work_category", c.category)}:</span>{" "}
                            <span className="font-medium tabular-nums">{formatIDR(c.amount)}</span>
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </>
                ) : null}

                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">Rincian Item ({items?.total || 0})</p>
                  {canManage ? (
                    <Button data-testid={PROCUREMENT.boqAddBtn} size="sm" onClick={() => setAddOpen(true)}>
                      <Plus className="mr-1.5 h-4 w-4" /> Tambah Item
                    </Button>
                  ) : null}
                </div>

                {!items?.data?.length ? (
                  <EmptyState icon={Calculator} title="Belum ada item RAB"
                    description="Tambahkan item pekerjaan (kode biaya, volume, harga satuan) untuk menyusun anggaran."
                    actionLabel={canManage ? "Tambah Item" : undefined} onAction={() => setAddOpen(true)} />
                ) : (
                  <div className="overflow-x-auto rounded-xl border bg-card">
                    <Table>
                      <TableHeader><TableRow>
                        <TableHead>Kode</TableHead><TableHead>Kategori</TableHead><TableHead>Uraian</TableHead>
                        <TableHead>Langkah jadwal</TableHead>
                        <TableHead className="text-right">Volume</TableHead><TableHead className="text-right">Harga Satuan</TableHead>
                        <TableHead className="text-right">Jumlah</TableHead>{canManage ? <TableHead /> : null}
                      </TableRow></TableHeader>
                      <TableBody>
                        {items.data.map((it) => (
                          <TableRow key={it.id} data-testid={PROCUREMENT.boqRow}>
                            <TableCell className="font-medium">{it.cost_code || "-"}</TableCell>
                            <TableCell className="text-sm">{labelOf("work_category", it.category)}</TableCell>
                            <TableCell className="text-sm">{it.description}</TableCell>
                            <TableCell className="text-[11px]">
                              {(it.step_codes || []).length ? (
                                <button type="button" data-testid={COST.mapBtn}
                                  className="rounded bg-secondary px-1.5 py-0.5 font-mono hover:underline"
                                  disabled={!canManage}
                                  onClick={() => setMapFor({ id: it.id, code: it.cost_code,
                                    label: it.description, steps: it.step_codes || [] })}>
                                  {(it.step_codes || []).join(", ")}
                                </button>
                              ) : canManage ? (
                                <Button size="sm" variant="ghost" data-testid={COST.mapBtn}
                                  className="h-7 text-[11px] text-amber-700"
                                  onClick={() => setMapFor({ id: it.id, code: it.cost_code,
                                    label: it.description, steps: [] })}>
                                  Petakan ke langkah
                                </Button>
                              ) : <span className="text-amber-700">belum dipetakan</span>}
                            </TableCell>
                            <TableCell className="text-right tabular-nums text-sm">{formatNumber(it.quantity)} {it.uom}</TableCell>
                            <TableCell className="text-right tabular-nums text-sm">{formatIDR(it.unit_price)}</TableCell>
                            <TableCell className="text-right tabular-nums font-medium">{formatIDR(it.amount)}</TableCell>
                            {canManage ? (
                              <TableCell>
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-rose-600"
                                  aria-label={`Hapus item ${it.cost_code || it.description}`}
                                  onClick={() => del(it.id)}>
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </TableCell>
                            ) : null}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </>
            )}
          </TabsContent>

          <TabsContent value="control" className="mt-4">
            <CostControlPanel projectId={projectId} canManage={canManage} onMapped={load} />
          </TabsContent>
        </Tabs>
      )}
      <AddBoQItemDialog projectId={projectId} open={addOpen} onOpenChange={setAddOpen} onDone={load} />
      <BoQStepMapDialog projectId={projectId} item={mapFor} open={!!mapFor}
        onOpenChange={(v) => !v && setMapFor(null)} onDone={load} />
    </div>
  );
}
