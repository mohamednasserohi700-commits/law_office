# Law Office Pro Premium - Design System

## 1) Brand Identity Tokens

- Authority + Trust + Technology:
  - `--bg: #0B1220`
  - `--surface: #111827`
  - `--primary-a: #3B82F6`
  - `--primary-b: #7C3AED`
  - `--legal-gold: #C9A54C`
  - `--success: #10B981`
  - `--danger: #FB7185`
  - `--text-main: #E5ECFF`
  - `--text-sub: #9EB0D6`
  - `--border: rgba(255,255,255,0.14)`

## 2) Glass + Glow Rules

- Glass surfaces:
  - backdrop blur: `16px`
  - layered alpha panel: `rgba(17,24,39,0.56)`
  - white border opacity: `0.14`
- Glow levels:
  - low: cards + static widgets (`var(--glow-low)`)
  - medium: hover state (`var(--glow-mid)`)
  - high: active navigation and primary actions (`var(--glow-high)`)
- Ambient glow placement:
  - behind header hero
  - behind active sidebar item
  - on primary CTA and notification bell

## 3) Core Components

- 3D logo system:
  - `static/js/logo3d.js` built with React Three Fiber
  - metallic gold/silver materials + HDRI environment + ambient/point/rim lights + soft shadows
  - animation modes: idle float, hover enlarge + glow, login pulse
- Layout shell:
  - `sidebar-shell` (glass vertical nav)
  - `topbar-shell` (actions/search/notifications)
  - `hero-header` (animated gradient header)
- Data grid:
  - `table-premium` sticky header + hover glow + selectable rows
  - status mapping:
    - نشطة = green glow
    - مؤجلة = yellow
    - مغلقة = gray
- Button system:
  - `btn-primary` gradient + shine animation
  - `btn-secondary` glass neutral button
  - `btn-danger` soft red action state

## 4) UX Intelligence Layer

- Spotlight global search: `Ctrl+K`
- Quick actions modal with high-frequency actions
- Notification bell with pulse highlight
- Animated counters on key metrics
- Loading overlay with mini 3D logo pulse

## 5) RTL & Production Notes

- Full RTL at document level (`dir="rtl"`)
- Arabic labels across navigation and modules
- Shared style and interaction assets:
  - `static/css/premium.css`
  - `static/js/app.js`
  - `static/js/logo3d.js`

