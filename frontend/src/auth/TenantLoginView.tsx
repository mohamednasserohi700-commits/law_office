import React from "react";

export function TenantLoginView() {
  return (
    <section dir="rtl" className="mx-auto mt-16 max-w-md rounded-3xl border border-white/10 bg-[#1A1D24]/80 p-6 text-white">
      <div className="mx-auto mb-4 flex h-24 w-24 items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-black/20">
        <img
          src="/brand-logo.png"
          alt="Law Office Pro"
          className="h-full w-full object-contain drop-shadow-[0_14px_24px_rgba(3,7,18,0.5)]"
        />
      </div>
      <h1 className="text-2xl font-black">تسجيل الدخول</h1>
      <p className="mt-1 text-sm text-slate-300">اختر الشركة ثم أدخل بيانات الحساب.</p>
      <form className="mt-5 space-y-3">
        <select className="w-full rounded-xl border border-white/10 bg-black/20 p-2">
          <option>المكتب الرئيسي - Pro</option>
        </select>
        <input className="w-full rounded-xl border border-white/10 bg-black/20 p-2" placeholder="اسم المستخدم" />
        <input type="password" className="w-full rounded-xl border border-white/10 bg-black/20 p-2" placeholder="كلمة المرور" />
        <button className="w-full rounded-xl bg-gradient-to-r from-[#C9A54C] to-[#E1C073] p-2 font-bold text-[#111827]">دخول</button>
      </form>
    </section>
  );
}
