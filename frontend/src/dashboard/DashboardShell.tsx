import React from "react";
import { MetricCard } from "../components/ui/MetricCard";

export function DashboardShell() {
  return (
    <main dir="rtl" className="space-y-4 bg-[#0F1115] p-6 text-white">
      <section className="rounded-3xl border border-[#C9A54C]/30 bg-[#1A1D24]/90 p-5">
        <h1 className="text-2xl font-black">مرحبًا بك في لوحة الشركة القانونية</h1>
        <p className="mt-1 text-sm text-slate-300">منصة SaaS متعددة الشركات مع عزل بيانات كامل.</p>
      </section>
      <section className="grid grid-cols-1 gap-3 md:grid-cols-4">
        <MetricCard title="إجمالي القضايا" value={124} trend="↑ 12%" icon="⚖️" />
        <MetricCard title="القضايا النشطة" value={38} trend="↔ مستقر" icon="🟢" />
        <MetricCard title="جلسات اليوم" value={7} trend="↑ 5%" icon="📆" />
        <MetricCard title="المهام المتأخرة" value={5} trend="↓ يحتاج متابعة" icon="⏳" />
      </section>
    </main>
  );
}
