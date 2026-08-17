import React, { useCallback, useEffect, useState } from "react";
import { Stamp, Plus, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import StatusPill from "@/components/patterns/StatusPill";
import MetricCard from "@/components/patterns/MetricCard";
import EmptyState from "@/components/patterns/EmptyState";
import { LoadingCards, ErrorState } from "@/components/patterns/StateViews";
import AddPermitDialog from "@/components/permits/AddPermitDialog";
import PermitDetailSheet from "@/components/permits/PermitDetailSheet";
import { useAuth } from "@/context/AuthContext";
import { formatDateWIB } from "@/utils/formatters";
import api from "@/services/apiClient";
import { PERMITS } from "@/constants/testIds";


export default function PermitsPage() {
  const { user } = useAuth();
  const canManage = ["owner", "super_admin", "project_manager"].includes(user?.role);
  const [data, setData] = useState(null);
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [selected, setSelected] = useState(null);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const res = await api.get("/permits", { params: { project_id: projectId === "all" ? undefined : projectId } });
      setData(res.data);
    } catch (e) { setError(e?.response?.data?.detail || "Gagal memuat perizinan."); }
    finally { setLoading(false); }
  }, [projectId]);

  useEffect(() => {
    (async () => {
      try { const r = await api.get("/projects"); setProjects(r.data.data || []); } catch { /* ignore */ }
    })();
  }, []);
  useEffect(() => { load(); }, [load]);

  const s = data?.summary;
  return (
    <div data-testid={PERMITS.page} className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Stamp className="h-5 w-5 text-primary" />
          <h1 className="font-heading text-xl font-semibold">Perizinan & Dokumen</h1>
        </div>
        {canManage ? (
          <Button data-testid={PERMITS.addBtn} size="sm" onClick={() => setAddOpen(true)}>
            <Plus className="mr-1.5 h-4 w-4" /> Tambah Izin
          </Button>
        ) : null}
      </div>

      {s ? (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <MetricCard label="Total Izin" value={s.total} tone="primary" />
          <MetricCard label="Disetujui" value={s.approved} tone="emerald" />
          <MetricCard label="Dalam Proses" value={s.in_progress} tone="indigo" />
          <MetricCard label="Terlambat" value={s.overdue} tone="rose" />
        </div>
      ) : null}

      <div className="max-w-xs">
        <Select value={projectId} onValueChange={setProjectId}>
          <SelectTrigger data-testid={PERMITS.projectSelect}><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua Proyek</SelectItem>
            {projects.map((p) => <SelectItem key={p.id} value={p.id}>{p.name} ({p.code})</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {loading ? <LoadingCards count={5} /> : error ? <ErrorState message={error} onRetry={load} /> :
        !data?.data?.length ? (
          <EmptyState icon={Stamp} title="Belum ada perizinan"
            description="Catat izin proyek (KRK/IMB/PBG/SLF) dengan tenggat agar tidak terlewat."
            actionLabel={canManage ? "Tambah Izin" : undefined} onAction={() => setAddOpen(true)} />
        ) : (
          <div className="overflow-x-auto rounded-xl border bg-card">
            <Table>
              <TableHeader><TableRow>
                <TableHead>Jenis</TableHead><TableHead>Instansi</TableHead>
                <TableHead>Proyek</TableHead><TableHead>Status</TableHead><TableHead>Tenggat</TableHead>
              </TableRow></TableHeader>
              <TableBody>
                {data.data.map((p) => (
                  <TableRow key={p.id} data-testid={PERMITS.row} className="cursor-pointer" onClick={() => setSelected(p)}>
                    <TableCell>
                      <p className="font-medium">{p.type}</p>
                      <p className="text-xs text-muted-foreground">{p.name}{p.reference_no ? ` · ${p.reference_no}` : ""}</p>
                    </TableCell>
                    <TableCell className="text-sm">{p.authority || "-"}</TableCell>
                    <TableCell className="text-sm">{p.project_name}</TableCell>
                    <TableCell><StatusPill status={p.status} group="permit_status" /></TableCell>
                    <TableCell>
                      {p.overdue ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-rose-600">
                          <AlertTriangle className="h-3.5 w-3.5" /> {formatDateWIB(p.deadline)}
                        </span>
                      ) : <span className="text-xs text-muted-foreground">{p.deadline ? formatDateWIB(p.deadline) : "-"}</span>}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

      <AddPermitDialog open={addOpen} onOpenChange={setAddOpen} projects={projects} onDone={load} />
      <PermitDetailSheet permit={selected} open={!!selected} canManage={canManage}
        onOpenChange={(v) => !v && setSelected(null)} onChanged={load} />
    </div>
  );
}
