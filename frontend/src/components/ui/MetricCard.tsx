import React from "react";

type MetricCardProps = {
  title: string;
  value: string | number;
  trend?: string;
  icon?: string;
};

export function MetricCard({ title, value, trend, icon = "•" }: MetricCardProps) {
  return (
    <article className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-md">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs text-slate-300">{title}</span>
        <span>{icon}</span>
      </div>
      <p className="text-2xl font-extrabold text-white">{value}</p>
      {trend ? <p className="mt-2 text-xs text-emerald-300">{trend}</p> : null}
    </article>
  );
}
