import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import { Save } from "lucide-react";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import StatusPill from "@/components/patterns/StatusPill";
import { formatDateWIB } from "@/utils/formatters";
import api from "@/services/apiClient";
import { PERMITS } from "@/constants/testIds";
import { useReference } from "@/context/ReferenceContext";


function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-4 py-1 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value || "-"}</span>
    </div>
  );
}

export default function PermitDetailSheet({ permit, open, canManage, onOpenChange, onChanged }) {
  const { labelOf, options } = useReference();
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (permit) setStatus(permit.status); }, [permit]);
  if (!permit) return null;

  const saveStatus = async () => {
    setBusy(true);
    try {
      await api.post(`/permits/${permit.id}/status`, { status });
      toast.success(`Status → ${labelOf("permit_status", status)}.`);
      onOpenChange(false); onChanged && onChanged();
    } catch (e) { toast.error(e?.response?.data?.detail || "Gagal mengubah status."); }
    finally { setBusy(false); }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent data-testid={PERMITS.detail} className="w-full overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>{permit.type} — {permit.name}</SheetTitle>
          <SheetDescription>Detail perizinan & pembaruan status.</SheetDescription>
        </SheetHeader>
        <div className="mt-5 space-y-5">
          <div className="rounded-xl border bg-card p-4">
            <div className="mb-2 flex items-center justify-between">
              <StatusPill status={permit.status} group="permit_status" />
              {permit.overdue ? <span className="text-xs font-medium text-rose-600">Terlambat</span> : null}
            </div>
            <Row label="Proyek" value={permit.project_name} />
            <Row label="Instansi" value={labelOf("permit_authority", permit.authority)} />
            <Row label="No. Referensi" value={permit.reference_no} />
            <Row label="Tenggat" value={permit.deadline ? formatDateWIB(permit.deadline) : "-"} />
            <Row label="Diajukan" value={permit.submitted_at ? formatDateWIB(permit.submitted_at) : "-"} />
            <Row label="Disetujui" value={permit.approved_at ? formatDateWIB(permit.approved_at) : "-"} />
            {permit.notes ? <p className="mt-2 whitespace-pre-line rounded-lg bg-secondary p-3 text-sm">{permit.notes}</p> : null}
          </div>
          {canManage ? (
            <div className="space-y-2 rounded-xl border bg-card p-4">
              <p className="text-sm font-semibold">Perbarui Status</p>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger data-testid={PERMITS.statusSelect}><SelectValue /></SelectTrigger>
                <SelectContent>{options("permit_status").map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
              </Select>
              <Button data-testid={PERMITS.statusSubmit} className="w-full" disabled={busy || status === permit.status} onClick={saveStatus}>
                <Save className="mr-1.5 h-4 w-4" /> Simpan Status
              </Button>
            </div>
          ) : null}
        </div>
      </SheetContent>
    </Sheet>
  );
}
