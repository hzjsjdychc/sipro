import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import ReferenceSelect from "@/components/patterns/ReferenceSelect";
import api from "@/services/apiClient";
import { PERMITS } from "@/constants/testIds";

const EMPTY = { project_id: "", type: "IMB", name: "", reference_no: "", authority: "", deadline: "", notes: "" };

export default function AddPermitDialog({ open, onOpenChange, projects, onDone }) {
  const [form, setForm] = useState(EMPTY);
  const [busy, setBusy] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  useEffect(() => {
    if (open) setForm({ ...EMPTY, project_id: projects?.[0]?.id || "" });
  }, [open, projects]);

  const submit = async () => {
    if (!form.project_id) { toast.error("Pilih proyek."); return; }
    setBusy(true);
    try {
      const payload = {
        project_id: form.project_id, type: form.type,
        name: form.name || null, reference_no: form.reference_no || null,
        authority: form.authority || null, notes: form.notes || null,
        deadline: form.deadline ? new Date(form.deadline).toISOString() : null,
      };
      await api.post("/permits", payload);
      toast.success("Perizinan ditambahkan.");
      onOpenChange(false); onDone && onDone();
    } catch (e) { toast.error(e?.response?.data?.detail || "Gagal menambah perizinan."); }
    finally { setBusy(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Tambah Perizinan</DialogTitle>
          <DialogDescription>Catat izin/dokumen legal proyek beserta tenggatnya.</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5"><Label htmlFor="permit-project">Proyek</Label>
            <Select value={form.project_id} onValueChange={(v) => set("project_id", v)}>
              <SelectTrigger id="permit-project" aria-label="Proyek"
                data-testid={PERMITS.formProject}><SelectValue placeholder="Pilih proyek" /></SelectTrigger>
              <SelectContent>{(projects || []).map((p) => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}</SelectContent>
            </Select></div>
          <div className="space-y-1.5"><Label>Jenis</Label>
            <ReferenceSelect group="permit_type" value={form.type}
              onChange={(v) => set("type", v)} testId="permit-form-type" /></div>
          <div className="space-y-1.5 sm:col-span-2"><Label htmlFor="permit-name">Nama Dokumen</Label>
            <Input id="permit-name" data-testid="permit-form-name" value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="mis. Persetujuan Bangunan Gedung" /></div>
          <div className="space-y-1.5"><Label htmlFor="permit-ref">No. Referensi</Label>
            <Input id="permit-ref" data-testid="permit-form-ref" value={form.reference_no} onChange={(e) => set("reference_no", e.target.value)} placeholder="mis. 503/1234/DPMPTSP/2026" /></div>
          <div className="space-y-1.5"><Label>Instansi</Label>
            <ReferenceSelect group="permit_authority" value={form.authority}
              onChange={(v) => set("authority", v)} testId="permit-form-authority"
              placeholder="Pilih instansi" /></div>
          <div className="space-y-1.5 sm:col-span-2"><Label htmlFor="permit-deadline">Tenggat</Label>
            <Input id="permit-deadline" data-testid="permit-form-deadline" type="date" value={form.deadline} onChange={(e) => set("deadline", e.target.value)} /></div>
          <div className="space-y-1.5 sm:col-span-2"><Label htmlFor="permit-notes">Catatan</Label>
            <Textarea id="permit-notes" data-testid="permit-form-notes" rows={2} value={form.notes} onChange={(e) => set("notes", e.target.value)} placeholder="mis. syarat tambahan dari instansi" /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={busy}>Batal</Button>
          <Button data-testid={PERMITS.addSubmit} onClick={submit} disabled={busy}>{busy ? "Menyimpan…" : "Simpan"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
