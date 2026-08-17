import React, { useCallback, useEffect, useState } from "react";
import { BarChart3, Repeat } from "lucide-react";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import MetricCard from "@/components/patterns/MetricCard";
import StatusPill from "@/components/patterns/StatusPill";
import EmptyState from "@/components/patterns/EmptyState";
import { LoadingCards, ErrorState } from "@/components/patterns/StateViews";
import { formatNumber, formatIDR, formatDateTimeWIB } from "@/utils/formatters";
import api from "@/services/apiClient";
import { OMNI } from "@/constants/testIds";
import RefLabel from "@/components/patterns/RefLabel";

const EVENT_LABEL = {
  Lead: "Lead", InitiateCheckout: "Booking", Purchase: "Purchase (AJB)",
};

export default function AttributionPanel() {
  const [data, setData] = useState(null);
  const [conversions, setConversions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [a, c] = await Promise.all([
        api.get("/capture-events/attribution"),
        api.get("/capture-events/conversions"),
      ]);
      setData(a.data.data);
      setConversions(c.data.data || []);
    } catch (e) {
      setError(e?.response?.data?.detail || "Gagal memuat atribusi.");
    } finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingCards count={4} />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const rows = data?.rows || [];
  const t = data?.totals || {};

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Funnel atribusi lead per sumber &amp; campaign. (CPL/biaya iklan tidak tersedia di mode simulasi.)
      </p>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <MetricCard label="Total Lead" value={formatNumber(t.leads || 0)} />
        <MetricCard label="Hot" value={formatNumber(t.hot || 0)} tone="rose" />
        <MetricCard label="Qualified" value={formatNumber(t.qualified || 0)} tone="indigo" />
        <MetricCard label="Booked/Won" value={formatNumber(t.booked || 0)} tone="emerald" />
        <MetricCard label="Feedback CAPI" value={formatNumber(t.conversions || 0)} tone="amber"
          hint="event dikirim balik ke platform" />
      </div>

      {!rows.length ? (
        <EmptyState icon={BarChart3} title="Belum ada data atribusi" description="Data muncul saat lead masuk dari kanal." />
      ) : (
        <div data-testid={OMNI.attrTable} className="overflow-x-auto rounded-xl border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Sumber</TableHead>
                <TableHead>Campaign</TableHead>
                <TableHead className="text-right">Lead</TableHead>
                <TableHead className="text-right">Hot</TableHead>
                <TableHead className="text-right">Qualified</TableHead>
                <TableHead className="text-right">Booked</TableHead>
                <TableHead className="text-right">CAPI</TableHead>
                <TableHead className="text-right">Konversi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r, i) => (
                <TableRow key={`${r.source}-${r.campaign}-${i}`} data-testid={OMNI.attrRow}>
                  <TableCell className="font-medium"><RefLabel group="lead_source" value={r.source} /></TableCell>
                  <TableCell className="text-muted-foreground">{r.campaign}</TableCell>
                  <TableCell className="text-right">{formatNumber(r.leads)}</TableCell>
                  <TableCell className="text-right">{formatNumber(r.hot)}</TableCell>
                  <TableCell className="text-right">{formatNumber(r.qualified)}</TableCell>
                  <TableCell className="text-right">{formatNumber(r.booked)}</TableCell>
                  <TableCell className="text-right text-amber-600">{formatNumber(r.conversions || 0)}</TableCell>
                  <TableCell className="text-right font-medium">{r.conversion_pct}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* CAPI feedback loop — conversion events fed back to ad platforms */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Repeat className="h-4 w-4 text-primary" />
          <h3 className="font-heading text-sm font-semibold">Feedback Loop (CAPI)</h3>
        </div>
        <p className="text-xs text-muted-foreground">
          Event konversi yang dikirim balik ke platform iklan (Meta/Google/TikTok) agar optimasi kampanye membaik.
          Semua berjalan <b>SIMULASI</b> hingga token platform dikonfigurasi.
        </p>
        {!conversions.length ? (
          <EmptyState icon={Repeat} title="Belum ada event konversi"
            description="Event muncul otomatis saat lead ber-atribusi iklan masuk / deal booked / AJB." />
        ) : (
          <div data-testid={OMNI.convTable} className="overflow-x-auto rounded-xl border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Platform</TableHead>
                  <TableHead>Event</TableHead>
                  <TableHead>Campaign</TableHead>
                  <TableHead className="text-right">Nilai</TableHead>
                  <TableHead className="text-right">Transport</TableHead>
                  <TableHead className="text-right">Waktu</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {conversions.map((c) => (
                  <TableRow key={c.id} data-testid={OMNI.convRow}>
                    <TableCell className="font-medium">{c.platform_label || c.platform}</TableCell>
                    <TableCell>{EVENT_LABEL[c.event_name] || c.event_name}</TableCell>
                    <TableCell className="text-muted-foreground">{c.campaign || "-"}</TableCell>
                    <TableCell className="text-right tabular-nums">{c.value ? formatIDR(c.value) : "-"}</TableCell>
                    <TableCell className="text-right">
                      <StatusPill status={c.transport === "live" ? "active" : "simulation"}
                        label={c.transport === "live" ? "Live" : "Simulasi"} />
                    </TableCell>
                    <TableCell className="text-right text-xs text-muted-foreground">{formatDateTimeWIB(c.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </div>
  );
}
