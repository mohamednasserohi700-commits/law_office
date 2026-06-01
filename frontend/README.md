# Frontend SaaS Structure (React Ready)

This folder is prepared for migration from Flask templates to a React frontend.

## Structure

- `src/components` shared UI building blocks
- `src/modules` business domain screens
- `src/tenant` tenant-aware branding and context
- `src/auth` tenant login flow
- `src/dashboard` premium main dashboard

## API Contract (already available in backend)

- `GET /api/v1/auth/me`
- `GET /api/v1/tenants`
- `GET /api/v1/tenant/summary`
- `GET /api/v1/billing/invoices`
- `GET /api/v1/billing/payments`
- `GET /api/v1/modules/<table>`

## Notes

- RTL by default (`dir="rtl"`).
- Theme tokens should map to graphite/gold/teal/violet brand.
