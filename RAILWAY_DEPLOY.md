# نشر النظام على Railway

## الجاهزية

| البند | الحالة |
|--------|--------|
| تشغيل عبر Gunicorn (`Procfile`) | جاهز |
| قاعدة بيانات SQLite + WAL | جاهز |
| تهيئة الجداول عند التشغيل (`init_db`) | جاهز |
| تخزين دائم عبر Volume | **مطلوب إعدادك أنت** |
| `SECRET_KEY` آمن | **مطلوب في Variables** |

بدون **Volume** تُفقد البيانات عند إعادة النشر أو إعادة تشغيل الحاوية.

---

## خطوات النشر

### 1) ربط المستودع
- New Project → Deploy from GitHub → اختر مجلد `Lawyer System Pro`
- Railway يكتشف `Procfile` و`requirements.txt` تلقائياً

### 2) متغيرات البيئة (Variables)
```
SECRET_KEY=<سلسلة عشوائية 32+ حرف>
```
اختياري إذا لم تستخدم Volume بمسار `/data`:
```
DATA_DIR=/data
```

### 3) Volume للتخزين الدائم (مهم)
1. في خدمة الويب: **Volumes** → Add Volume  
2. Mount Path: `/data`  
3. أعد النشر

النظام يخزّن تلقائياً في `/data`:
- `law_office_data.db` — البيانات الرئيسية
- `law_office_data_docs.db` — ملفات المستندات
- `system_settings.json` — إعدادات النظام
- `backups/` — النسخ الاحتياطية

### 4) التحقق
- افتح: `https://<your-app>.up.railway.app/health`  
- يجب أن يظهر: `{"status":"ok","data_dir":"/data"}`

### 5) أول دخول
- المستخدم الافتراضي: `admin` / `admin123`  
- **غيّر كلمة المرور فوراً بعد النشر**

---

## ملاحظات
- الشعار ثابت من `static/img/` ولا يحتاج Volume.
- SQLite مناسب لمكتب واحد أو عدد محدود من المستخدمين؛ للتوسع الكبير لاحقاً يُفضّل PostgreSQL.
- النسخ الاحتياطي من داخل النظام (إن وُجدت الشاشة) يُحفظ في `BACKUP_ROOT` على نفس الـ Volume.
