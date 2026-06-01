# Law Office Pro - Multi-Tenant SaaS Architecture

## Tenant Model

- كل شركة قانونية = `tenant` مستقل.
- بيانات كل شركة معزولة عبر `tenant_id` في جداول النظام.
- خصائص الـtenant:
  - `name`
  - `slug`
  - `logo_path`
  - `subscription_plan`
  - `theme_primary`

## Data Isolation Strategy

- جداول النظام الأساسية تحتوي `tenant_id`:
  - users, clients, cases, sessions, payments, expenses, tasks, contracts, documents, logs, online_users
- كل استعلام CRUD في التطبيق يفلتر بـ `tenant_id` الحالي من الجلسة.
- تسجيل الدخول يربط المستخدم مع tenant محدد.

## Auth Flow (Tenant-aware)

1. المستخدم يختار الشركة (`tenant_slug`) من شاشة الدخول.
2. النظام يتحقق من tenant نشط.
3. المصادقة تكون على `(username + password + tenant_id)`.
4. تخزين بيانات tenant في session:
   - `tenant_id`, `tenant_name`, `tenant_slug`, `tenant_plan`

## SaaS Plans

- Basic: 5 users, 1GB, no advanced analytics
- Pro: 20 users, 8GB, advanced analytics
- Enterprise: high limits, advanced analytics

## Billing Domain

- `billing_invoices`: الفواتير
- `billing_payments`: عمليات السداد
- `tenant_subscriptions`: خطة كل شركة وحدودها
- شاشة `billing` لعرض الفواتير والمدفوعات.

## API Ready Structure

- Endpoint: `GET /api/v1/tenant/summary`
  - tenant info
  - plan features
  - usage summary

## Suggested Frontend Modular Layout (React Target)

- `/components` عناصر واجهة عامة قابلة لإعادة الاستخدام
- `/modules` وحدات نطاق الأعمال (clients/cases/billing)
- `/tenant` تخصيص الهوية والـtheme
- `/auth` تدفق الدخول والاختيار بين الشركات
- `/dashboard` Hero + metrics + insights
