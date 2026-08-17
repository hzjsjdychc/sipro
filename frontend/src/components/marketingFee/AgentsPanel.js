import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Users2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from "@/components/ui/table";
import StatusPill from "@/components/patterns/StatusPill";
import EmptyState from "@/components/patterns/EmptyState";
import RefLabel from "@/components/patterns/RefLabel";
import ReferenceSelect from "@/components/patterns/ReferenceSelect";
import { LoadingCards, ErrorState } from "@/components/patterns/StateViews";
import AgentDialog from "@/components/marketingFee/AgentDialog";
import { formatIDR } from "@/utils/formatters";
import api from "@/services/apiClient";
import { MFEE } from "@/constants/testIds";

/** Master agen/mitra eksternal + status kerja sama. */
export default function AgentsPanel() {
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dialog, setDialog] = useState(null); // { mode: "create" | "edit", agent }

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const res = await api.get("/marketing/agents", { params: status ? { status } : {} });
      setRows(res.data.data || []);
    } catch (e) {
      setError(e?.response?.data?.detail || "Gagal memuat daftar agen.");
    } finally { setLoading(false); }
  }, [status]);

  useEffect(() => { load(); }, [load]);

  const toggleStatus = async (agent) => {
    const next = agent.status === "active" ? "inactive" : "active";
    try {
      await api.put(`/marketing/agents/${agent.id}`, { status: next });
      toast.success(`Status ${agent.name} diperbarui.`);
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Gagal memperbarui status agen.");
    }
  };

  if (loading) return <LoadingCards count={3} />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div data-testid={MFEE.agentsPanel} className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="w-56 space-y-1">
          <span className="text-xs text-muted-foreground">Status agen</span>
          <ReferenceSelect group="agent_status" value={status} onChange={setStatus}
            allowEmpty emptyLabel="Semua status" testId={MFEE.agentStatus} />
        </div>
        <Button data-testid={MFEE.agentAddBtn} onClick={() => setDialog({ mode: "create" })}>
          <Plus className="mr-1.5 h-4 w-4" /> Tambah Agen
        </Button>
      </div>

      {!rows.length ? (
        <div data-testid={MFEE.agentsEmpty}>
          <EmptyState icon={Users2} title="Belum ada agen terdaftar"
            description="Daftarkan agen properti, kantor broker, atau pemberi referral agar fee-nya bisa diajukan dan dilacak."
            actionLabel="Tambah Agen" onAction={() => setDialog({ mode: "create" })} />
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border bg-card shadow-sm">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Kode</TableHead>
                <TableHead>Nama</TableHead>
                <TableHead>Jenis</TableHead>
                <TableHead>Kontak</TableHead>
                <TableHead>Rekening</TableHead>
                <TableHead className="text-right">Deal</TableHead>
                <TableHead className="text-right">Total Fee</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Aksi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((a) => (
                <TableRow key={a.id} data-testid={MFEE.agentRow} data-status={a.status}>
                  <TableCell className="font-medium">{a.code}</TableCell>
                  <TableCell>
                    <p className="text-sm">{a.name}</p>
                    <p className="text-[11px] text-muted-foreground">{a.company || "—"}</p>
                  </TableCell>
                  <TableCell className="text-sm">
                    <RefLabel group="agent_type" value={a.agent_type} />
                  </TableCell>
                  <TableCell className="text-sm">
                    <p>{a.phone || "—"}</p>
                    <p className="text-[11px] text-muted-foreground">{a.email || "—"}</p>
                  </TableCell>
                  <TableCell className="text-sm">
                    <p>{a.bank_name || "—"}</p>
                    <p className="text-[11px] text-muted-foreground">{a.bank_account || "—"}</p>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">{a.deals_count || 0}</TableCell>
                  <TableCell className="text-right tabular-nums">{formatIDR(a.fee_total)}</TableCell>
                  <TableCell><StatusPill status={a.status} group="agent_status" /></TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1.5">
                      <Button size="sm" variant="ghost"
                        onClick={() => setDialog({ mode: "edit", agent: a })}>Ubah</Button>
                      <Button size="sm" variant="outline" onClick={() => toggleStatus(a)}>
                        {a.status === "active" ? "Nonaktifkan" : "Aktifkan"}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <AgentDialog state={dialog} onClose={() => setDialog(null)} onSaved={load} />
    </div>
  );
}
