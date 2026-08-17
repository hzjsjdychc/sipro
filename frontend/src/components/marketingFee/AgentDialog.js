import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import ReferenceSelect from "@/components/patterns/ReferenceSelect";
import api from "@/services/apiClient";
import { MFEE } from "@/constants/testIds";

const EMPTY = {
  name: "", agent_type: "agen_properti", company: "", phone: "", email: "",
  npwp: "", bank_name: "", bank_account: "", note: "",
};

/** Tambah / ubah agen mitra eksternal. */
export default function AgentDialog({ state, onClose, onSaved }) {
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!state) return;
    setErr("");
    if (state.mode === "edit" && state.agent) {
      const a = state.agent;
      setForm({
        name: a.name || "", agent_type: a.agent_type || "agen_properti",
        company: a.company || "", phone: a.phone || "", email: a.email || "",
        npwp: a.npwp || "", bank_name: a.bank_name || "", bank_account: a.bank_account || "",
        note: a.note || "",
      });
    } else {
      setForm(EMPTY);
    }
  }, [state]);

  if (!state) return null;
  const isEdit = state.mode === "edit";
  const set = (patch) => setForm((p) => ({ ...p, ...patch }));

  const submit = async () => {
    setSaving(true); setErr("");
    const body = {
      name: form.name, agent_type: form.agent_type,
      company: form.company || null, phone: form.phone || null, email: form.email || null,
      npwp: form.npwp || null, bank_name: form.bank_name || null,
      bank_account: form.bank_account || null, note: form.note || null,
    };
    try {
      if (isEdit) await api.put(`/marketing/agents/${state.agent.id}`, body);
      else await api.post("/marketing/agents", body);
      toast.success(isEdit ? "Data agen diperbarui." : "Agen baru terdaftar.");
      onClose(); onSaved?.();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Gagal menyimpan data agen.");
    } finally { setSaving(false); }
  };

  return (
    <Dialog open onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent data-testid={MFEE.agentDialog} className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Ubah Data Agen" : "Tambah Agen / Mitra"}</DialogTitle>
          <DialogDescription>
            Data rekening dipakai saat pembayaran marketing fee.
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2 space-y-1.5">
            <Label htmlFor="ag-name">Nama agen / mitra</Label>
            <Input id="ag-name" data-testid={MFEE.agentName} value={form.name}
              placeholder="Mis. PT Griya Mitra Andalan"
              onChange={(e) => set({ name: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <Label>Jenis mitra</Label>
            <ReferenceSelect group="agent_type" value={form.agent_type}
              onChange={(v) => set({ agent_type: v })} testId={MFEE.agentType} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ag-company">Perusahaan / kantor</Label>
            <Input id="ag-company" data-testid={MFEE.agentCompany} value={form.company}
              onChange={(e) => set({ company: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ag-phone">Nomor telepon</Label>
            <Input id="ag-phone" data-testid={MFEE.agentPhone} value={form.phone}
              placeholder="+62812…" onChange={(e) => set({ phone: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ag-email">Email</Label>
            <Input id="ag-email" data-testid={MFEE.agentEmail} type="email" value={form.email}
              onChange={(e) => set({ email: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ag-npwp">NPWP</Label>
            <Input id="ag-npwp" data-testid={MFEE.agentNpwp} value={form.npwp}
              placeholder="01.234.567.8-901.000"
              onChange={(e) => set({ npwp: e.target.value })} />
          </div>
          <div className="space-y-1.5">
            <Label>Bank</Label>
            <ReferenceSelect group="financing_bank" value={form.bank_name}
              onChange={(v) => set({ bank_name: v })} testId={MFEE.agentBank}
              placeholder="Pilih bank…" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ag-acct">Nomor rekening</Label>
            <Input id="ag-acct" data-testid={MFEE.agentAccount} value={form.bank_account}
              onChange={(e) => set({ bank_account: e.target.value })} />
          </div>
          <div className="col-span-2 space-y-1.5">
            <Label htmlFor="ag-note">Catatan</Label>
            <Textarea id="ag-note" value={form.note} rows={2}
              onChange={(e) => set({ note: e.target.value })} />
          </div>
        </div>
        {err ? <p className="rounded-md bg-rose-50 p-2 text-sm text-rose-700">{err}</p> : null}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Batal</Button>
          <Button data-testid={MFEE.agentSubmit} onClick={submit}
            disabled={saving || form.name.trim().length < 3}>
            {saving ? "Menyimpan…" : isEdit ? "Simpan Perubahan" : "Simpan Agen"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
