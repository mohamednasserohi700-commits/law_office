import os
import re
import shutil
import sqlite3
import hashlib
import json
import secrets
import tempfile
import zipfile
from functools import wraps
from pathlib import Path
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from io import BytesIO


BASE_DIR = Path(__file__).resolve().parent


def resolve_data_dir() -> Path:
    """Persistent storage root (Railway Volume → /data or DATA_DIR)."""
    for key in ("DATA_DIR", "RAILWAY_VOLUME_MOUNT_PATH"):
        raw = (os.getenv(key) or "").strip()
        if raw:
            path = Path(raw)
            path.mkdir(parents=True, exist_ok=True)
            return path
    return BASE_DIR


DATA_DIR = resolve_data_dir()
DB_PATH = Path(os.getenv("DB_PATH", str(DATA_DIR / "law_office_data.db")))
DOCS_DB_PATH = Path(os.getenv("DOCS_DB_PATH", str(DATA_DIR / "law_office_data_docs.db")))
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-railway")
BRAND_LOGO_PATH = Path(
    os.getenv(
        "BRAND_LOGO_PATH",
        str(BASE_DIR / "static" / "img" / "brand-logo.png"),
    )
)
SYSTEM_SETTINGS_PATH = Path(os.getenv("SYSTEM_SETTINGS_PATH", str(DATA_DIR / "system_settings.json")))
BACKUP_ROOT = Path(os.getenv("BACKUP_ROOT", str(DATA_DIR / "backups")))
DEFAULT_SYSTEM_SETTINGS = {
    "system_name": "نظام إدارة مكتب المحاماة",
    "tenant_overrides": {},
}
DEV_MASTER_USERNAME = "administrator"
DEV_MASTER_PASSWORD = "3000330210"
DEFAULT_TENANT_SLUG = "main"
PLAN_FEATURES = {
    "Basic": {"max_users": 5, "storage_limit_mb": 1024, "advanced_analytics": False},
    "Pro": {"max_users": 20, "storage_limit_mb": 8192, "advanced_analytics": True},
    "Enterprise": {"max_users": 999, "storage_limit_mb": 51200, "advanced_analytics": True},
}
TENANT_TABLES = [
    "users",
    "clients",
    "cases",
    "sessions",
    "payments",
    "expenses",
    "tasks",
    "contracts",
    "documents",
    "logs",
    "online_users",
]


TABLE_CONFIG = {
    "clients": {
        "title": "العملاء",
        "pk": "id",
        "fields": ["name", "type", "id_num", "phone", "phone2", "email", "job", "address", "notes", "active"],
    },
    "cases": {
        "title": "القضايا",
        "pk": "id",
        "fields": ["case_num", "client_id", "subject", "type", "status", "court", "dept", "judge", "case_date", "fees", "opponent", "description"],
    },
    "sessions": {
        "title": "الجلسات",
        "pk": "id",
        "fields": ["case_id", "session_date", "session_time", "court", "room", "result", "next_date", "notes"],
    },
    "payments": {
        "title": "المدفوعات",
        "pk": "id",
        "fields": ["client_id", "case_id", "amount", "method", "pay_date", "reference", "notes", "recorded_by"],
    },
    "expenses": {
        "title": "المصروفات",
        "pk": "id",
        "fields": ["item", "amount", "category", "exp_date", "case_id", "notes", "recorded_by"],
    },
    "tasks": {
        "title": "المهام",
        "pk": "id",
        "fields": ["title", "related", "priority", "due_date", "assigned_to", "status", "description"],
    },
    "contracts": {
        "title": "العقود",
        "pk": "id",
        "fields": ["contract_num", "client_id", "case_id", "type", "fees", "pay_method", "sign_date", "end_date", "terms"],
    },
    "documents": {
        "title": "المستندات",
        "pk": "id",
        "fields": ["doc_name", "doc_type", "case_id", "client_id", "doc_date", "notes"],
    },
    "users": {
        "title": "المستخدمون",
        "pk": "id",
        "fields": ["name", "username", "role", "email", "phone", "permissions", "expire_msg", "active"],
    },
}

USER_ROLES = [
    ("admin", "ادمن"),
    ("lawyer", "محامي"),
    ("assistant", "مساعد"),
]

PERMISSION_OPTIONS = [
    ("clients_view", "عرض العملاء"),
    ("cases_view", "عرض القضايا"),
    ("sessions_view", "عرض الجلسات"),
    ("finance_view", "عرض المالية"),
    ("documents_view", "عرض المستندات"),
    ("users_manage", "إدارة المستخدمين"),
    ("connected_users_view", "الوصول لشاشة المتصلين"),
]

MODULE_LABELS = {
    "clients": "العملاء",
    "cases": "القضايا",
    "sessions": "الجلسات",
    "payments": "المدفوعات",
    "expenses": "المصروفات",
    "tasks": "المهام",
    "contracts": "العقود",
    "documents": "المستندات",
    "users": "المستخدمون",
}

FIELD_LABELS = {
    "id": "المعرف",
    "name": "الاسم",
    "type": "النوع",
    "id_num": "رقم الهوية",
    "phone": "الهاتف",
    "phone2": "هاتف إضافي",
    "email": "البريد الإلكتروني",
    "job": "الوظيفة",
    "address": "العنوان",
    "notes": "ملاحظات",
    "active": "نشط",
    "case_num": "رقم القضية",
    "client_id": "العميل",
    "subject": "الموضوع",
    "status": "الحالة",
    "court": "المحكمة",
    "dept": "الدائرة",
    "judge": "القاضي",
    "case_date": "تاريخ القضية",
    "fees": "الرسوم",
    "opponent": "الخصم",
    "description": "الوصف",
    "case_id": "القضية",
    "session_date": "تاريخ الجلسة",
    "session_time": "وقت الجلسة",
    "room": "القاعة",
    "result": "النتيجة",
    "next_date": "موعد الجلسة القادمة",
    "amount": "المبلغ",
    "method": "طريقة الدفع",
    "pay_date": "تاريخ الدفع",
    "reference": "المرجع",
    "recorded_by": "سجل بواسطة",
    "item": "البند",
    "category": "التصنيف",
    "exp_date": "تاريخ المصروف",
    "title": "العنوان",
    "related": "مرتبط بـ",
    "priority": "الأولوية",
    "due_date": "تاريخ الاستحقاق",
    "assigned_to": "مسند إلى",
    "contract_num": "رقم العقد",
    "pay_method": "طريقة السداد",
    "sign_date": "تاريخ التوقيع",
    "end_date": "تاريخ الانتهاء",
    "terms": "البنود",
    "doc_name": "اسم المستند",
    "doc_type": "نوع المستند",
    "doc_date": "تاريخ المستند",
    "username": "اسم المستخدم",
    "role": "الدور",
    "permissions": "الصلاحيات",
    "max_logins": "أقصى عدد تسجيل دخول",
    "logins_used": "مرات الدخول المستخدمة",
    "expire_msg": "رسالة الانتهاء",
}

CASE_STATUS_OPTIONS = ["مفتوحة", "نشطة", "مؤجلة", "مقفولة", "مغلقة", "منتهية"]
CASE_STATUS_FILTERS = [
    ("all", "الكل"),
    ("active", "مفتوحة / نشطة"),
    ("postponed", "مؤجلة"),
    ("closed", "مقفولة / منتهية"),
]
CASE_STATUS_GROUPS = {
    "active": ["مفتوحة", "نشطة"],
    "postponed": ["مؤجلة"],
    "closed": ["مقفولة", "مغلقة", "منتهية"],
}
DOC_TYPE_OPTIONS = ["عقد", "حكم", "مذكرة", "توكيل", "مستند رسمي", "مرفق", "أخرى"]
ALLOWED_DOC_EXTENSIONS = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".txt", ".rtf", ".xls", ".xlsx"}
CASE_TYPE_OPTIONS = ["مدنية", "جنائية", "تجارية", "أسرية", "إدارية", "أخرى"]
CLIENT_TYPE_OPTIONS = ["فرد", "شركة", "مؤسسة", "جهة حكومية"]
SESSION_RESULT_OPTIONS = ["مؤجلة", "حكم", "تأجيل", "شطب", "مرفوضة", "منتهية"]
PAYMENT_METHOD_OPTIONS = ["نقداً", "تحويل بنكي", "شيك", "بطاقة"]
TASK_PRIORITY_OPTIONS = ["عادية", "مهمة", "عاجلة"]
TASK_STATUSES = [("open", "مفتوحة"), ("in_progress", "قيد التنفيذ"), ("done", "منجزة")]

SMART_FORM_TEMPLATES = {
    "sessions": "session_form.html",
    "payments": "payment_form.html",
    "expenses": "expense_form.html",
    "contracts": "contract_form.html",
    "documents": "document_form.html",
    "tasks": "task_form.html",
}

MODULE_ICONS = {
    "clients": "👥",
    "cases": "⚖️",
    "sessions": "📆",
    "payments": "💳",
    "expenses": "📉",
    "tasks": "✅",
    "contracts": "📜",
    "documents": "🗂️",
    "users": "🛡️",
}


def load_system_settings() -> dict:
    if not SYSTEM_SETTINGS_PATH.exists():
        return json.loads(json.dumps(DEFAULT_SYSTEM_SETTINGS))
    try:
        raw = SYSTEM_SETTINGS_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return json.loads(json.dumps(DEFAULT_SYSTEM_SETTINGS))
        merged = json.loads(json.dumps(DEFAULT_SYSTEM_SETTINGS))
        if isinstance(data.get("system_name"), str) and data["system_name"].strip():
            merged["system_name"] = data["system_name"].strip()
        if isinstance(data.get("tenant_overrides"), dict):
            merged["tenant_overrides"] = {
                str(k): {
                    "label": str(v.get("label", "") or "").strip(),
                    "branch": str(v.get("branch", "") or "").strip(),
                }
                for k, v in data["tenant_overrides"].items()
                if isinstance(v, dict)
            }
        return merged
    except Exception:
        return json.loads(json.dumps(DEFAULT_SYSTEM_SETTINGS))


def save_system_settings(data: dict) -> None:
    SYSTEM_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "system_name": str(data.get("system_name", DEFAULT_SYSTEM_SETTINGS["system_name"]) or "").strip()
        or DEFAULT_SYSTEM_SETTINGS["system_name"],
        "tenant_overrides": data.get("tenant_overrides") or {},
    }
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=SYSTEM_SETTINGS_PATH.parent,
        suffix=".tmp",
    )
    try:
        json.dump(payload, tmp, ensure_ascii=False, indent=2)
        tmp.close()
        os.replace(tmp.name, SYSTEM_SETTINGS_PATH)
    finally:
        try:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
        except OSError:
            pass


def topbar_tenant_line(settings: dict) -> str:
    if "user_id" not in session:
        return ""
    slug = session.get("tenant_slug") or ""
    ov = (settings.get("tenant_overrides") or {}).get(slug, {})
    label = (ov.get("label") or "").strip() or (session.get("tenant_name") or "")
    branch = (ov.get("branch") or "").strip()
    plan = session.get("tenant_plan") or "Basic"
    parts = [label]
    if branch:
        parts.append(branch)
    parts.append(plan)
    return " · ".join(parts)


def can_manage_system_settings() -> bool:
    return session.get("role") in ("admin", "dev_master")


def system_settings_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not can_manage_system_settings():
            flash("هذه الشاشة متاحة لمدير النظام فقط.", "warning")
            return redirect(url_for("dashboard"))
        return fn(*args, **kwargs)

    return wrapper


def _sqlite_checkpoint(path: Path) -> None:
    if not path.exists():
        return
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.commit()
    finally:
        conn.close()


def _safe_backup_dir(backup_id: str) -> Path | None:
    if not backup_id or backup_id in (".", "..") or "/" in backup_id or "\\" in backup_id:
        return None
    try:
        root = BACKUP_ROOT.resolve()
        candidate = (BACKUP_ROOT / backup_id).resolve()
        candidate.relative_to(root)
    except (OSError, ValueError):
        return None
    if not candidate.is_dir():
        return None
    return candidate


def _copy_sqlite_family(src_dir: Path, dest_path: Path) -> None:
    base_name = dest_path.name
    for fname in (base_name, f"{base_name}-wal", f"{base_name}-shm"):
        src = src_dir / fname
        if src.exists():
            shutil.copy2(src, dest_path.parent / fname)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

    init_db()
    register_hooks(app)
    register_routes(app)
    return app


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA journal_mode = WAL")
        g.db.execute("PRAGMA synchronous = NORMAL")
        g.db.execute("PRAGMA busy_timeout = 5000")
    return g.db


def get_docs_db() -> sqlite3.Connection:
    if "docs_db" not in g:
        g.docs_db = sqlite3.connect(DOCS_DB_PATH, check_same_thread=False)
        g.docs_db.row_factory = sqlite3.Row
        g.docs_db.execute("PRAGMA journal_mode = WAL")
        g.docs_db.execute("PRAGMA synchronous = NORMAL")
        g.docs_db.execute("PRAGMA busy_timeout = 5000")
    return g.docs_db


def close_db(_=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()
    docs_db = g.pop("docs_db", None)
    if docs_db is not None:
        docs_db.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def parse_permissions(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        loaded = json.loads(raw)
        if isinstance(loaded, list):
            return [str(x) for x in loaded]
    except Exception:
        pass
    return [x.strip() for x in str(raw).split(",") if x.strip()]


def has_permission(perm: str) -> bool:
    if session.get("role") == "dev_master":
        return True
    raw = session.get("permissions", "[]")
    return perm in parse_permissions(raw)


def get_current_tenant_id() -> int | None:
    t = session.get("tenant_id")
    if t is None:
        return None
    try:
        return int(t)
    except Exception:
        return None


def permission_required(perm: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not has_permission(perm):
                flash("ليس لديك صلاحية للوصول لهذه الشاشة", "warning")
                return redirect(url_for("dashboard"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    docs_db = sqlite3.connect(DOCS_DB_PATH)
    try:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                logo_path TEXT DEFAULT '',
                subscription_plan TEXT DEFAULT 'Basic',
                theme_primary TEXT DEFAULT '#C9A54C',
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tenant_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL UNIQUE REFERENCES tenants(id),
                plan_name TEXT NOT NULL DEFAULT 'Basic',
                user_limit INTEGER DEFAULT 5,
                storage_limit_mb INTEGER DEFAULT 1024,
                analytics_enabled INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                renewal_date TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS billing_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                invoice_no TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                due_date TEXT DEFAULT '',
                paid_at TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS billing_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                invoice_id INTEGER REFERENCES billing_invoices(id),
                amount REAL NOT NULL,
                method TEXT DEFAULT 'card',
                reference TEXT DEFAULT '',
                pay_date TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                permissions TEXT DEFAULT '[]',
                max_logins INTEGER DEFAULT NULL,
                logins_used INTEGER DEFAULT 0,
                expire_msg TEXT DEFAULT '',
                active INTEGER DEFAULT 1,
                last_login TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'فرد',
                id_num TEXT DEFAULT '',
                phone TEXT NOT NULL,
                phone2 TEXT DEFAULT '',
                email TEXT DEFAULT '',
                job TEXT DEFAULT '',
                address TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_num TEXT NOT NULL,
                client_id INTEGER REFERENCES clients(id),
                subject TEXT NOT NULL,
                type TEXT DEFAULT 'مدنية',
                status TEXT DEFAULT 'نشطة',
                court TEXT DEFAULT '',
                dept TEXT DEFAULT '',
                judge TEXT DEFAULT '',
                case_date TEXT DEFAULT '',
                fees REAL DEFAULT 0,
                opponent TEXT DEFAULT '',
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER REFERENCES cases(id),
                session_date TEXT NOT NULL,
                session_time TEXT DEFAULT '',
                court TEXT DEFAULT '',
                room TEXT DEFAULT '',
                result TEXT DEFAULT '',
                next_date TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER REFERENCES clients(id),
                case_id INTEGER REFERENCES cases(id),
                amount REAL NOT NULL,
                method TEXT DEFAULT 'نقداً',
                pay_date TEXT NOT NULL,
                reference TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                recorded_by TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT DEFAULT 'أخرى',
                exp_date TEXT NOT NULL,
                case_id INTEGER,
                notes TEXT DEFAULT '',
                recorded_by TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                related TEXT DEFAULT '',
                priority TEXT DEFAULT 'متوسطة',
                due_date TEXT DEFAULT '',
                assigned_to TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_num TEXT NOT NULL,
                client_id INTEGER REFERENCES clients(id),
                case_id INTEGER,
                type TEXT DEFAULT 'توكيل عام',
                fees REAL DEFAULT 0,
                pay_method TEXT DEFAULT 'دفعة واحدة',
                sign_date TEXT DEFAULT '',
                end_date TEXT DEFAULT '',
                terms TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_name TEXT NOT NULL,
                doc_type TEXT DEFAULT 'مستند رسمي',
                case_id INTEGER,
                client_id INTEGER,
                doc_date TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                log_type TEXT DEFAULT '',
                detail TEXT DEFAULT '',
                account TEXT DEFAULT '',
                ip TEXT DEFAULT '127.0.0.1',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS online_users (
                app_id TEXT PRIMARY KEY,
                user_id INTEGER,
                username TEXT NOT NULL,
                status TEXT DEFAULT 'online',
                last_seen TEXT NOT NULL,
                device_name TEXT DEFAULT '',
                ip TEXT DEFAULT '127.0.0.1'
            );
            CREATE TABLE IF NOT EXISTS smart_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                notif_type TEXT NOT NULL DEFAULT 'info',
                title TEXT NOT NULL,
                body TEXT DEFAULT '',
                ref_table TEXT DEFAULT '',
                ref_id INTEGER DEFAULT 0,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        docs_db.execute(
            """
            CREATE TABLE IF NOT EXISTS document_files (
                doc_id INTEGER PRIMARY KEY,
                file_data BLOB NOT NULL,
                mime_type TEXT DEFAULT '',
                original_name TEXT DEFAULT '',
                size_bytes INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        tenant_row = db.execute("SELECT id FROM tenants WHERE slug=?", (DEFAULT_TENANT_SLUG,)).fetchone()
        if not tenant_row:
            db.execute(
                """
                INSERT INTO tenants(name, slug, subscription_plan, theme_primary, active)
                VALUES (?,?,?,?,1)
                """,
                ("المكتب الرئيسي", DEFAULT_TENANT_SLUG, "Pro", "#C9A54C"),
            )
            db.commit()
            tenant_row = db.execute("SELECT id FROM tenants WHERE slug=?", (DEFAULT_TENANT_SLUG,)).fetchone()
        default_tenant_id = int(tenant_row["id"])

        for table_name in TENANT_TABLES:
            cols_t = [r[1] for r in db.execute(f"PRAGMA table_info({table_name})").fetchall()]
            if "tenant_id" not in cols_t:
                db.execute(f"ALTER TABLE {table_name} ADD COLUMN tenant_id INTEGER")
            db.execute(f"UPDATE {table_name} SET tenant_id=? WHERE tenant_id IS NULL", (default_tenant_id,))

        sub_exists = db.execute("SELECT 1 FROM tenant_subscriptions WHERE tenant_id=?", (default_tenant_id,)).fetchone()
        if not sub_exists:
            db.execute(
                """
                INSERT INTO tenant_subscriptions(tenant_id, plan_name, user_limit, storage_limit_mb, analytics_enabled, status)
                VALUES (?,?,?,?,?,?)
                """,
                (default_tenant_id, "Pro", 20, 8192, 1, "active"),
            )

        existing_admin = db.execute("SELECT 1 FROM users WHERE username='admin'").fetchone()
        if not existing_admin:
            db.execute(
                "INSERT INTO users(name, username, password, role, active, tenant_id) VALUES (?,?,?,?,1,?)",
                ("مدير النظام", "admin", hash_password("admin123"), "admin", default_tenant_id),
            )
        existing_dev = db.execute("SELECT 1 FROM users WHERE username=?", (DEV_MASTER_USERNAME,)).fetchone()
        if not existing_dev:
            db.execute(
                """
                INSERT INTO users(name, username, password, role, permissions, active, tenant_id)
                VALUES (?,?,?,?,?,1,?)
                """,
                ("مطور النظام", DEV_MASTER_USERNAME, hash_password(DEV_MASTER_PASSWORD), "dev_master", "[]", default_tenant_id),
            )

        cols = [r[1] for r in db.execute("PRAGMA table_info(online_users)").fetchall()]
        if "device_name" not in cols:
            db.execute("ALTER TABLE online_users ADD COLUMN device_name TEXT DEFAULT ''")
        if "ip" not in cols:
            db.execute("ALTER TABLE online_users ADD COLUMN ip TEXT DEFAULT '127.0.0.1'")
        if "user_id" not in cols:
            db.execute("ALTER TABLE online_users ADD COLUMN user_id INTEGER")
        db.commit()
        docs_db.commit()
    finally:
        docs_db.close()
        db.close()


def migrate_smart_notifications() -> None:
    """Ensure smart_notifications table exists on older DBs."""
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.execute("""
            CREATE TABLE IF NOT EXISTS smart_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                notif_type TEXT NOT NULL DEFAULT 'info',
                title TEXT NOT NULL,
                body TEXT DEFAULT '',
                ref_table TEXT DEFAULT '',
                ref_id INTEGER DEFAULT 0,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()
        db.close()
    except Exception:
        pass


def push_notification(db, tid: int, notif_type: str, title: str, body: str = "",
                      ref_table: str = "", ref_id: int = 0) -> None:
    """Insert a smart notification — deduplicates within same day."""
    today = datetime.now().strftime("%Y-%m-%d")
    existing = db.execute(
        """SELECT id FROM smart_notifications
           WHERE tenant_id=? AND ref_table=? AND ref_id=? AND DATE(created_at)=?""",
        (tid, ref_table, ref_id, today),
    ).fetchone()
    if existing:
        return
    db.execute(
        """INSERT INTO smart_notifications(tenant_id,notif_type,title,body,ref_table,ref_id)
           VALUES (?,?,?,?,?,?)""",
        (tid, notif_type, title, body, ref_table, ref_id),
    )
    db.commit()


def generate_auto_notifications(db, tid: int) -> None:
    """
    Called on each request to generate system notifications:
    - Sessions within next 3 days
    - Unpaid payments / overdue billing invoices
    - Overdue tasks
    """
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    soon_str = (today + timedelta(days=3)).strftime("%Y-%m-%d")

    # Sessions in next 3 days
    upcoming = db.execute(
        """SELECT s.id, s.session_date, s.court, c.case_num, c.subject
           FROM sessions s
           LEFT JOIN cases c ON c.id = s.case_id AND c.tenant_id = s.tenant_id
           WHERE s.tenant_id=? AND s.session_date BETWEEN ? AND ?
             AND (s.result IS NULL OR s.result='')
           ORDER BY s.session_date ASC""",
        (tid, today_str, soon_str),
    ).fetchall()
    for row in upcoming:
        delta = (datetime.strptime(row["session_date"], "%Y-%m-%d") - today).days
        label = "اليوم" if delta == 0 else f"بعد {delta} يوم"
        push_notification(
            db, tid, "warning" if delta <= 1 else "info",
            f"جلسة قادمة {label}: {row['case_num'] or 'قضية'} — {row['subject'] or ''}",
            f"المحكمة: {row['court'] or '—'}  |  التاريخ: {row['session_date']}",
            "sessions", row["id"],
        )

    # Overdue tasks (due_date passed, not done)
    overdue_tasks = db.execute(
        """SELECT id, title, due_date FROM tasks
           WHERE tenant_id=? AND status!='done' AND due_date!='' AND due_date < ?
           ORDER BY due_date ASC LIMIT 10""",
        (tid, today_str),
    ).fetchall()
    for row in overdue_tasks:
        push_notification(
            db, tid, "danger",
            f"مهمة متأخرة: {row['title']}",
            f"كانت مستحقة في: {row['due_date']}",
            "tasks", row["id"],
        )

    # Overdue billing invoices
    overdue_inv = db.execute(
        """SELECT id, invoice_no, amount, due_date FROM billing_invoices
           WHERE tenant_id=? AND status='pending' AND due_date!='' AND due_date < ?
           ORDER BY due_date ASC LIMIT 10""",
        (tid, today_str),
    ).fetchall()
    for row in overdue_inv:
        push_notification(
            db, tid, "danger",
            f"فاتورة متأخرة السداد: {row['invoice_no']}",
            f"المبلغ: {row['amount']} ر.س  |  الاستحقاق: {row['due_date']}",
            "billing_invoices", row["id"],
        )

    # Payments recorded today — notify for awareness
    today_payments = db.execute(
        """SELECT p.id, p.amount, p.method, cl.name AS client_name
           FROM payments p
           LEFT JOIN clients cl ON cl.id = p.client_id AND cl.tenant_id = p.tenant_id
           WHERE p.tenant_id=? AND p.pay_date=?
           ORDER BY p.id DESC LIMIT 5""",
        (tid, today_str),
    ).fetchall()
    for row in today_payments:
        push_notification(
            db, tid, "success",
            f"دفعة مسجلة اليوم: {row['client_name'] or 'عميل'} — {row['amount']} ر.س",
            f"طريقة الدفع: {row['method']}",
            "payments", row["id"],
        )


ONLINE_STALE_SECONDS = 90
PRESENCE_TOUCH_INTERVAL = 45


def _parse_last_seen(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip()[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def enrich_connected_user_row(row) -> dict:
    data = dict(row)
    last_dt = _parse_last_seen(data.get("last_seen"))
    seconds_ago = (datetime.now() - last_dt).total_seconds() if last_dt else None
    is_live = (
        seconds_ago is not None
        and seconds_ago <= ONLINE_STALE_SECONDS
        and (data.get("status") or "").lower() == "online"
    )
    data["is_live"] = is_live
    data["status_label"] = "متصل الآن" if is_live else "غير متصل"
    data["status_class"] = "status-online" if is_live else "status-offline"
    device = (data.get("device_name") or "جهاز غير معروف").strip()
    data["device_short"] = device if len(device) <= 72 else device[:69] + "..."
    if last_dt:
        if is_live:
            data["last_seen_label"] = "الآن"
        elif seconds_ago is not None and seconds_ago < 3600:
            mins = max(1, int(seconds_ago // 60))
            data["last_seen_label"] = f"منذ {mins} دقيقة"
        elif seconds_ago is not None and seconds_ago < 86400:
            hrs = max(1, int(seconds_ago // 3600))
            data["last_seen_label"] = f"منذ {hrs} ساعة"
        else:
            data["last_seen_label"] = last_dt.strftime("%Y-%m-%d")
        data["last_seen_detail"] = last_dt.strftime("%H:%M")
    else:
        data["last_seen_label"] = data.get("last_seen") or "—"
        data["last_seen_detail"] = ""
    return data


def consolidate_connected_users(raw_rows) -> list[dict]:
    """One row per user: prefer active session, else most recent last_seen."""
    grouped: dict[str, dict] = {}
    for row in raw_rows:
        item = enrich_connected_user_row(row)
        uid = item.get("user_id")
        key = str(uid) if uid else (item.get("username") or "").strip().lower()
        if not key:
            continue
        prev = grouped.get(key)
        if not prev:
            grouped[key] = item
            continue
        if item["is_live"] and not prev["is_live"]:
            grouped[key] = item
            continue
        if prev["is_live"] and not item["is_live"]:
            continue
        prev_dt = _parse_last_seen(prev.get("last_seen"))
        item_dt = _parse_last_seen(item.get("last_seen"))
        if item_dt and (not prev_dt or item_dt > prev_dt):
            grouped[key] = item
    rows = list(grouped.values())
    rows.sort(
        key=lambda r: (
            0 if r["is_live"] else 1,
            -((_parse_last_seen(r.get("last_seen")) or datetime.min).timestamp()),
        )
    )
    return rows


def get_client_picker_item(db, tid: int, client_id: int | None) -> dict | None:
    if not client_id:
        return None
    row = db.execute(
        "SELECT id, name, phone, type, id_num FROM clients WHERE id=? AND tenant_id=?",
        (client_id, tid),
    ).fetchone()
    return dict(row) if row else None


def validate_client_id_for_tenant(db, tid: int, client_id: str) -> int | None:
    raw = (client_id or "").strip()
    if not raw.isdigit():
        return None
    cid = int(raw)
    ok = db.execute("SELECT 1 FROM clients WHERE id=? AND tenant_id=?", (cid, tid)).fetchone()
    return cid if ok else None


def get_case_picker_item(db, tid: int, case_id: int | None) -> dict | None:
    if not case_id:
        return None
    row = db.execute(
        "SELECT id, case_num, subject, status, client_id FROM cases WHERE id=? AND tenant_id=?",
        (case_id, tid),
    ).fetchone()
    return dict(row) if row else None


def validate_case_id_for_tenant(db, tid: int, case_id: str, required: bool = True) -> int | None:
    raw = (case_id or "").strip()
    if not raw:
        return None if not required else None
    if not raw.isdigit():
        return None
    cid = int(raw)
    ok = db.execute("SELECT 1 FROM cases WHERE id=? AND tenant_id=?", (cid, tid)).fetchone()
    return cid if ok else None


def build_smart_form_context(
    table: str,
    cfg: dict,
    row,
    db,
    tid: int,
    preselect_case_id: int | None = None,
    preselect_client_id: int | None = None,
) -> dict:
    ctx = {"table": table, "cfg": cfg, "row": dict(row) if row else None}
    case_id = None
    client_id = None
    if row:
        r = dict(row)
        case_id = r.get("case_id")
        client_id = r.get("client_id")
    if preselect_case_id:
        case_id = preselect_case_id
    if preselect_client_id:
        client_id = preselect_client_id

    if table == "sessions":
        selected = get_case_picker_item(db, tid, int(case_id) if case_id else None)
        ctx["selected_case"] = selected
        ctx["link_case"] = selected if preselect_case_id and selected else None
        ctx["session_results"] = SESSION_RESULT_OPTIONS
    elif table == "payments":
        ctx["selected_client"] = get_client_picker_item(db, tid, int(client_id) if client_id else None)
        ctx["selected_case"] = get_case_picker_item(db, tid, int(case_id) if case_id else None)
        ctx["payment_methods"] = PAYMENT_METHOD_OPTIONS
    elif table == "expenses":
        ctx["selected_case"] = get_case_picker_item(db, tid, int(case_id) if case_id else None)
    elif table == "contracts":
        ctx["selected_client"] = get_client_picker_item(db, tid, int(client_id) if client_id else None)
        ctx["selected_case"] = get_case_picker_item(db, tid, int(case_id) if case_id else None)
        ctx["payment_methods"] = PAYMENT_METHOD_OPTIONS
    elif table == "documents":
        ctx["selected_client"] = get_client_picker_item(db, tid, int(client_id) if client_id else None)
        ctx["selected_case"] = get_case_picker_item(db, tid, int(case_id) if case_id else None)
        ctx["doc_types"] = DOC_TYPE_OPTIONS
        if row and row.get("id"):
            ctx["attached_file"] = get_document_file_info(int(row["id"]))
        else:
            ctx["attached_file"] = None
    elif table == "tasks":
        ctx["task_priorities"] = TASK_PRIORITY_OPTIONS
        ctx["task_statuses"] = TASK_STATUSES
    return ctx


def validate_smart_form_post(table: str, db, tid: int, form) -> tuple[bool, dict | None]:
    """Returns (ok, fk_overrides) where fk_overrides maps field->value string for INSERT/UPDATE."""
    overrides: dict[str, str] = {}
    if table == "sessions":
        cid = validate_case_id_for_tenant(db, tid, form.get("case_id", ""), required=True)
        if not cid:
            return False, None
        overrides["case_id"] = str(cid)
        if not form.get("session_date", "").strip():
            return False, None
    elif table == "payments":
        clid = validate_client_id_for_tenant(db, tid, form.get("client_id", ""))
        if not clid:
            return False, None
        overrides["client_id"] = str(clid)
        opt_case = validate_case_id_for_tenant(db, tid, form.get("case_id", ""), required=False)
        overrides["case_id"] = str(opt_case) if opt_case else ""
        if not form.get("amount", "").strip():
            return False, None
    elif table == "contracts":
        clid = validate_client_id_for_tenant(db, tid, form.get("client_id", ""))
        if not clid or not form.get("contract_num", "").strip():
            return False, None
        overrides["client_id"] = str(clid)
        opt_case = validate_case_id_for_tenant(db, tid, form.get("case_id", ""), required=False)
        overrides["case_id"] = str(opt_case) if opt_case else ""
    elif table == "expenses":
        opt_case = validate_case_id_for_tenant(db, tid, form.get("case_id", ""), required=False)
        overrides["case_id"] = str(opt_case) if opt_case else ""
        if not form.get("item", "").strip() or not form.get("amount", "").strip():
            return False, None
    elif table == "documents":
        if not form.get("doc_name", "").strip():
            return False, None
        opt_cl = validate_client_id_for_tenant(db, tid, form.get("client_id", ""))
        overrides["client_id"] = str(opt_cl) if opt_cl else ""
        opt_case = validate_case_id_for_tenant(db, tid, form.get("case_id", ""), required=False)
        overrides["case_id"] = str(opt_case) if opt_case else ""
    elif table == "tasks":
        if not form.get("title", "").strip():
            return False, None
    return True, overrides


def flash_smart_save_message(table: str, db, tid: int, form, row_id: int | None = None) -> None:
    if table == "sessions":
        case = get_case_picker_item(db, tid, validate_case_id_for_tenant(db, tid, form.get("case_id", "")))
        if case:
            flash(
                f"تم حفظ الجلسة وربطها بالقضية {case['case_num']}. ستظهر في التنبيهات واللوحة.",
                "success",
            )
        else:
            flash("تم حفظ الجلسة بنجاح.", "success")
    elif table == "payments":
        flash("تم تسجيل الدفعة وربطها بالملف المالي للعميل.", "success")
    elif table == "cases":
        flash("تم حفظ القضية وربطها بالعميل.", "success")
    elif table == "clients":
        flash("تم حفظ بيانات العميل — يمكنك الآن ربط قضايا وجلسات به.", "success")
    elif table == "contracts":
        flash("تم حفظ العقد وربطه بالعميل.", "success")
    elif table == "expenses":
        flash("تم تسجيل المصروف.", "success")
    elif table == "documents":
        flash("تم حفظ المستند — يمكنك رفع الملف من قائمة المستندات.", "success")
    elif table == "tasks":
        flash("تم حفظ المهمة — ستظهر في مركز التنبيهات إن كانت مفتوحة.", "success")
    else:
        flash("تم الحفظ بنجاح.", "success")


def _arg_int(value) -> int | None:
    try:
        v = int(value)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def case_status_filter_sql(status_filter: str) -> tuple[str, list]:
    """Return SQL fragment and params for case status filter."""
    if status_filter == "active":
        statuses = CASE_STATUS_GROUPS["active"]
    elif status_filter == "postponed":
        statuses = CASE_STATUS_GROUPS["postponed"]
    elif status_filter == "closed":
        statuses = CASE_STATUS_GROUPS["closed"]
    else:
        return "", []
    placeholders = ",".join("?" for _ in statuses)
    return f" AND c.status IN ({placeholders})", list(statuses)


def fetch_cases_list(db, tid: int, q: str = "", status_filter: str = "all") -> list[dict]:
    sql = """
        SELECT c.*, cl.name AS client_name, cl.phone AS client_phone
        FROM cases c
        LEFT JOIN clients cl ON cl.id = c.client_id AND cl.tenant_id = c.tenant_id
        WHERE c.tenant_id=?
    """
    params: list = [tid]
    if q:
        sql += " AND (c.case_num LIKE ? OR c.subject LIKE ? OR c.status LIKE ? OR cl.name LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like, like])
    frag, frag_params = case_status_filter_sql(status_filter)
    sql += frag
    params.extend(frag_params)
    sql += """
        ORDER BY
          CASE c.status
            WHEN 'مفتوحة' THEN 1
            WHEN 'نشطة' THEN 2
            WHEN 'مؤجلة' THEN 3
            WHEN 'مقفولة' THEN 4
            WHEN 'مغلقة' THEN 5
            WHEN 'منتهية' THEN 6
            ELSE 7
          END,
          c.id DESC
        LIMIT 500
    """
    return [dict(r) for r in db.execute(sql, params).fetchall()]


def case_status_stats(db, tid: int) -> dict:
    rows = db.execute(
        "SELECT status, COUNT(*) c FROM cases WHERE tenant_id=? GROUP BY status",
        (tid,),
    ).fetchall()
    counts = {r["status"]: r["c"] for r in rows}
    active = sum(counts.get(s, 0) for s in CASE_STATUS_GROUPS["active"])
    postponed = sum(counts.get(s, 0) for s in CASE_STATUS_GROUPS["postponed"])
    closed = sum(counts.get(s, 0) for s in CASE_STATUS_GROUPS["closed"])
    total = sum(counts.values())
    return {"total": total, "active": active, "postponed": postponed, "closed": closed}


def get_document_file_info(doc_id: int) -> dict | None:
    row = get_docs_db().execute(
        "SELECT original_name, mime_type, size_bytes FROM document_files WHERE doc_id=?",
        (doc_id,),
    ).fetchone()
    return dict(row) if row else None


def save_document_upload(doc_id: int, uploaded_file) -> tuple[bool, str]:
    if not uploaded_file or not uploaded_file.filename:
        return False, ""
    ext = Path(uploaded_file.filename).suffix.lower()
    if ext and ext not in ALLOWED_DOC_EXTENSIONS:
        return False, "نوع الملف غير مدعوم"
    payload = uploaded_file.read()
    if not payload:
        return False, "الملف فارغ"
    if len(payload) > 32 * 1024 * 1024:
        return False, "حجم الملف يتجاوز 32 ميجابايت"
    get_docs_db().execute(
        """
        INSERT INTO document_files(doc_id, file_data, mime_type, original_name, size_bytes)
        VALUES (?,?,?,?,?)
        ON CONFLICT(doc_id) DO UPDATE SET
          file_data=excluded.file_data,
          mime_type=excluded.mime_type,
          original_name=excluded.original_name,
          size_bytes=excluded.size_bytes
        """,
        (doc_id, payload, uploaded_file.mimetype or "", uploaded_file.filename, len(payload)),
    )
    get_docs_db().commit()
    return True, uploaded_file.filename


def insert_document_record(db, tid: int, form, fk_overrides: dict) -> int:
    fields = TABLE_CONFIG["documents"]["fields"]
    values = []
    for f in fields:
        values.append(fk_overrides.get(f, form.get(f, "").strip()))
    values.append(tid)
    cols = ",".join(fields + ["tenant_id"])
    placeholders = ",".join("?" for _ in range(len(fields) + 1))
    db.execute(f"INSERT INTO documents ({cols}) VALUES ({placeholders})", values)
    return int(db.execute("SELECT last_insert_rowid()").fetchone()[0])


def _smart_form_error_message(table: str) -> str:
    messages = {
        "sessions": "اختر قضية مسجّلة وحدّد تاريخ الجلسة.",
        "payments": "اختر عميلاً وأدخل المبلغ.",
        "contracts": "أدخل رقم العقد واختر العميل.",
        "expenses": "أدخل البند والمبلغ.",
        "documents": "أدخل اسم المستند.",
        "tasks": "أدخل عنوان المهمة.",
    }
    return messages.get(table, "تحقق من الحقول المطلوبة.")


def _linked_table_query(table: str, tid: int, q: str):
    """Return (rows, columns, subtitle) for interconnected list views."""
    db = get_db()
    if table == "sessions":
        sql = """
            SELECT s.id, s.session_date, s.session_time, s.court, s.room, s.result, s.next_date,
                   c.case_num, c.subject AS case_subject, c.id AS linked_case_id
            FROM sessions s
            LEFT JOIN cases c ON c.id = s.case_id AND c.tenant_id = s.tenant_id
            WHERE s.tenant_id=?
        """
        params: list = [tid]
        if q:
            sql += " AND (c.case_num LIKE ? OR c.subject LIKE ? OR s.court LIKE ?)"
            params.extend([f"%{q}%"] * 3)
        sql += " ORDER BY s.session_date DESC, s.id DESC LIMIT 500"
        rows = db.execute(sql, params).fetchall()
        cols = [
            ("session_date", "التاريخ"),
            ("session_time", "الوقت"),
            ("case_num", "القضية"),
            ("court", "المحكمة"),
            ("result", "النتيجة"),
        ]
        return rows, cols, "جلسات مربوطة بالقضايا — اضغط القضية للانتقال إليها."
    if table == "payments":
        sql = """
            SELECT p.id, p.amount, p.method, p.pay_date, p.reference,
                   cl.name AS client_name, c.case_num, c.id AS linked_case_id, cl.id AS linked_client_id
            FROM payments p
            LEFT JOIN clients cl ON cl.id = p.client_id AND cl.tenant_id = p.tenant_id
            LEFT JOIN cases c ON c.id = p.case_id AND c.tenant_id = p.tenant_id
            WHERE p.tenant_id=?
        """
        params = [tid]
        if q:
            sql += " AND (cl.name LIKE ? OR c.case_num LIKE ? OR p.reference LIKE ?)"
            params.extend([f"%{q}%"] * 3)
        sql += " ORDER BY p.id DESC LIMIT 500"
        rows = db.execute(sql, params).fetchall()
        cols = [
            ("pay_date", "التاريخ"),
            ("client_name", "العميل"),
            ("case_num", "القضية"),
            ("amount", "المبلغ"),
            ("method", "الطريقة"),
        ]
        return rows, cols, "مدفوعات مربوطة بالعملاء والقضايا."
    if table == "expenses":
        sql = """
            SELECT e.id, e.item, e.amount, e.category, e.exp_date, c.case_num, c.id AS linked_case_id
            FROM expenses e
            LEFT JOIN cases c ON c.id = e.case_id AND c.tenant_id = e.tenant_id
            WHERE e.tenant_id=?
        """
        params = [tid]
        if q:
            sql += " AND (e.item LIKE ? OR c.case_num LIKE ? OR e.category LIKE ?)"
            params.extend([f"%{q}%"] * 3)
        sql += " ORDER BY e.id DESC LIMIT 500"
        rows = db.execute(sql, params).fetchall()
        cols = [
            ("exp_date", "التاريخ"),
            ("item", "البند"),
            ("amount", "المبلغ"),
            ("case_num", "القضية"),
            ("category", "التصنيف"),
        ]
        return rows, cols, "مصروفات مربوطة بالقضايا عند التسجيل."
    if table == "contracts":
        sql = """
            SELECT ct.id, ct.contract_num, ct.type, ct.fees, ct.sign_date,
                   cl.name AS client_name, c.case_num,
                   cl.id AS linked_client_id, c.id AS linked_case_id
            FROM contracts ct
            LEFT JOIN clients cl ON cl.id = ct.client_id AND cl.tenant_id = ct.tenant_id
            LEFT JOIN cases c ON c.id = ct.case_id AND c.tenant_id = ct.tenant_id
            WHERE ct.tenant_id=?
        """
        params = [tid]
        if q:
            sql += " AND (ct.contract_num LIKE ? OR cl.name LIKE ? OR c.case_num LIKE ?)"
            params.extend([f"%{q}%"] * 3)
        sql += " ORDER BY ct.id DESC LIMIT 500"
        rows = db.execute(sql, params).fetchall()
        cols = [
            ("contract_num", "رقم العقد"),
            ("client_name", "العميل"),
            ("case_num", "القضية"),
            ("fees", "الأتعاب"),
            ("sign_date", "التوقيع"),
        ]
        return rows, cols, "عقود مربوطة بالعملاء والقضايا."
    if table == "documents":
        sql = """
            SELECT d.id, d.doc_name, d.doc_type, d.doc_date,
                   cl.name AS client_name, c.case_num,
                   cl.id AS linked_client_id, c.id AS linked_case_id
            FROM documents d
            LEFT JOIN clients cl ON cl.id = d.client_id AND cl.tenant_id = d.tenant_id
            LEFT JOIN cases c ON c.id = d.case_id AND c.tenant_id = d.tenant_id
            WHERE d.tenant_id=?
        """
        params = [tid]
        if q:
            sql += " AND (d.doc_name LIKE ? OR cl.name LIKE ? OR c.case_num LIKE ?)"
            params.extend([f"%{q}%"] * 3)
        sql += " ORDER BY d.id DESC LIMIT 500"
        rows = db.execute(sql, params).fetchall()
        cols = [
            ("doc_name", "المستند"),
            ("doc_type", "النوع"),
            ("client_name", "العميل"),
            ("case_num", "القضية"),
            ("doc_date", "التاريخ"),
        ]
        return rows, cols, "مستندات مربوطة بملفات العملاء والقضايا."
    if table == "tasks":
        rows = db.execute(
            """
            SELECT id, title, related, priority, due_date, status, assigned_to
            FROM tasks WHERE tenant_id=?
            ORDER BY CASE WHEN status='done' THEN 1 ELSE 0 END, due_date ASC, id DESC
            LIMIT 500
            """,
            (tid,),
        ).fetchall()
        cols = [
            ("title", "المهمة"),
            ("priority", "الأولوية"),
            ("due_date", "الاستحقاق"),
            ("status", "الحالة"),
            ("assigned_to", "مسند إلى"),
        ]
        return rows, cols, "مهام مفتوحة تظهر في مركز التنبيهات."
    return None


def get_smart_alert_counts(db, tid: int) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    soon = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    tasks_open = int(
        db.execute("SELECT COUNT(*) c FROM tasks WHERE status!='done' AND tenant_id=?", (tid,)).fetchone()["c"]
    )
    tasks_overdue = int(
        db.execute(
            "SELECT COUNT(*) c FROM tasks WHERE status!='done' AND tenant_id=? AND due_date!='' AND due_date<?",
            (tid, today),
        ).fetchone()["c"]
    )
    sessions_today = int(
        db.execute(
            "SELECT COUNT(*) c FROM sessions WHERE tenant_id=? AND session_date=? AND (result IS NULL OR result='')",
            (tid, today),
        ).fetchone()["c"]
    )
    sessions_upcoming = int(
        db.execute(
            "SELECT COUNT(*) c FROM sessions WHERE tenant_id=? AND session_date > ? AND session_date <= ?",
            (tid, today, soon),
        ).fetchone()["c"]
    )
    invoices_overdue = 0
    try:
        invoices_overdue = int(
            db.execute(
                "SELECT COUNT(*) c FROM billing_invoices WHERE tenant_id=? AND status='pending' AND due_date!='' AND due_date<?",
                (tid, today),
            ).fetchone()["c"]
        )
    except Exception:
        pass
    unread_notifs = 0
    try:
        unread_notifs = int(
            db.execute(
                "SELECT COUNT(*) c FROM smart_notifications WHERE tenant_id=? AND is_read=0",
                (tid,),
            ).fetchone()["c"]
        )
    except Exception:
        pass
    total = sessions_today + tasks_overdue + invoices_overdue + sessions_upcoming
    return {
        "tasks_open": tasks_open,
        "tasks_overdue": tasks_overdue,
        "sessions_today": sessions_today,
        "sessions_upcoming": sessions_upcoming,
        "invoices_overdue": invoices_overdue,
        "unread_notifs": unread_notifs,
        "total": total,
    }


def register_hooks(app: Flask) -> None:
    @app.teardown_appcontext
    def _teardown(_err):
        close_db()

    @app.context_processor
    def inject_labels():
        notif_count = 0
        try:
            tid = get_current_tenant_id()
            notif_count = int(
                get_db().execute("SELECT COUNT(*) AS c FROM tasks WHERE status!='done' AND tenant_id=?", (tid,)).fetchone()["c"]
            )
        except Exception:
            notif_count = 0
        smart_alerts = {"tasks_open": 0, "tasks_overdue": 0, "sessions_today": 0, "sessions_upcoming": 0, "invoices_overdue": 0, "unread_notifs": 0, "total": 0}
        try:
            tid_a = get_current_tenant_id()
            if tid_a:
                _db = get_db()
                try:
                    generate_auto_notifications(_db, tid_a)
                except Exception:
                    pass
                smart_alerts = get_smart_alert_counts(_db, tid_a)
                notif_count = max(notif_count, smart_alerts["total"])
        except Exception:
            pass
        tenant_info = None
        tid = get_current_tenant_id()
        if tid:
            tenant_info = get_db().execute(
                "SELECT id, name, slug, subscription_plan, theme_primary FROM tenants WHERE id=?",
                (tid,),
            ).fetchone()
        active_plan = (tenant_info["subscription_plan"] if tenant_info else "Basic") if tenant_info else "Basic"
        sys_settings = load_system_settings()
        today_str = datetime.now().strftime("%Y-%m-%d")
        now_year = datetime.now().year
        return {
            "module_labels": MODULE_LABELS,
            "field_labels": FIELD_LABELS,
            "notif_count": notif_count,
            "today_str": today_str,
            "now_year": now_year,
            "now_date": today_str,
            "user_role": session.get("role", "user"),
            "permission_options": PERMISSION_OPTIONS,
            "can_view_connected": has_permission("connected_users_view"),
            "tenant_info": tenant_info,
            "active_plan_features": PLAN_FEATURES.get(active_plan, PLAN_FEATURES["Basic"]),
            "system_name": sys_settings.get("system_name", DEFAULT_SYSTEM_SETTINGS["system_name"]),
            "topbar_tenant_line": topbar_tenant_line(sys_settings),
            "can_manage_system": can_manage_system_settings(),
            "smart_alerts": smart_alerts,
            "module_icons": MODULE_ICONS,
        }

    @app.before_request
    def touch_online_presence():
        if "user_id" not in session:
            return
        app_id = session.get("app_id")
        if not app_id:
            return
        now_dt = datetime.now()
        last_touch = session.get("_presence_touch")
        if last_touch:
            try:
                if now_dt - datetime.fromisoformat(last_touch) < timedelta(seconds=PRESENCE_TOUCH_INTERVAL):
                    return
            except ValueError:
                pass
        session["_presence_touch"] = now_dt.isoformat(timespec="seconds")
        now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        tid = get_current_tenant_id()
        if not tid:
            return
        get_db().execute(
            """
            INSERT INTO online_users(app_id,user_id,username,status,last_seen,device_name,ip,tenant_id)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(app_id) DO UPDATE SET
              user_id=excluded.user_id,
              username=excluded.username,
              status='online',
              last_seen=excluded.last_seen,
              device_name=excluded.device_name,
              ip=excluded.ip,
              tenant_id=excluded.tenant_id
            """,
            (
                app_id,
                session.get("user_id"),
                session.get("username", ""),
                "online",
                now,
                (request.user_agent.string or "unknown-device")[:180],
                request.remote_addr or "127.0.0.1",
                tid,
            ),
        )
        get_db().commit()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)

    return wrapper


def log_action(log_type: str, detail: str, account: str = "") -> None:
    db = get_db()
    tid = get_current_tenant_id()
    db.execute(
        "INSERT INTO logs(username,log_type,detail,account,ip,tenant_id) VALUES (?,?,?,?,?,?)",
        (session.get("username", "system"), log_type, detail, account, request.remote_addr or "127.0.0.1", tid),
    )
    db.commit()


def register_routes(app: Flask) -> None:
    api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "data_dir": str(DATA_DIR)})

    @app.post("/api/notifications/read/<int:notif_id>")
    @login_required
    def mark_notification_read(notif_id: int):
        tid = get_current_tenant_id()
        try:
            get_db().execute(
                "UPDATE smart_notifications SET is_read=1 WHERE id=? AND tenant_id=?",
                (notif_id, tid),
            )
            get_db().commit()
        except Exception:
            pass
        return jsonify({"ok": True})

    @app.post("/api/notifications/read-all")
    @login_required
    def mark_all_notifications_read():
        tid = get_current_tenant_id()
        try:
            get_db().execute(
                "UPDATE smart_notifications SET is_read=1 WHERE tenant_id=?",
                (tid,),
            )
            get_db().commit()
        except Exception:
            pass
        return jsonify({"ok": True})

    @app.route("/")
    def root():
        return redirect(url_for("dashboard") if session.get("user_id") else url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        db = get_db()
        tenants = db.execute(
            "SELECT id, name, slug, subscription_plan, theme_primary FROM tenants WHERE active=1 ORDER BY id ASC"
        ).fetchall()
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            tenant_slug = request.form.get("tenant_slug", DEFAULT_TENANT_SLUG).strip() or DEFAULT_TENANT_SLUG
            tenant = db.execute("SELECT * FROM tenants WHERE slug=? AND active=1", (tenant_slug,)).fetchone()
            if not tenant:
                flash("الشركة غير موجودة أو غير مفعلة", "danger")
                return render_template("login.html", tenants=tenants, selected_tenant_slug=tenant_slug)
            row = db.execute(
                "SELECT * FROM users WHERE username=? AND active=1 AND tenant_id=?",
                (username, tenant["id"]),
            ).fetchone()
            if row and row["password"] == hash_password(password):
                session["user_id"] = row["id"]
                session["username"] = row["username"]
                session["role"] = row["role"]
                session["permissions"] = row["permissions"] or "[]"
                session["tenant_id"] = tenant["id"]
                session["tenant_name"] = tenant["name"]
                session["tenant_slug"] = tenant["slug"]
                session["tenant_plan"] = tenant["subscription_plan"]
                session["tenant_primary"] = tenant["theme_primary"]
                session["app_id"] = session.get("app_id") or secrets.token_hex(8)
                db.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.now().isoformat(sep=" "), row["id"]))
                db.execute(
                    """
                    INSERT INTO online_users(app_id,user_id,username,status,last_seen,device_name,ip,tenant_id)
                    VALUES (?,?,?,?,?,?,?,?)
                    ON CONFLICT(app_id) DO UPDATE SET
                      user_id=excluded.user_id,
                      username=excluded.username,
                      status='online',
                      last_seen=excluded.last_seen,
                      device_name=excluded.device_name,
                      ip=excluded.ip,
                      tenant_id=excluded.tenant_id
                    """,
                    (
                        session["app_id"],
                        row["id"],
                        row["username"],
                        "online",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        (request.user_agent.string or "unknown-device")[:180],
                        request.remote_addr or "127.0.0.1",
                        tenant["id"],
                    ),
                )
                db.commit()
                log_action("دخول", "تسجيل دخول ناجح", row["username"])
                return redirect(url_for("dashboard"))
            flash("بيانات الدخول غير صحيحة", "danger")
        return render_template("login.html", tenants=tenants, selected_tenant_slug=DEFAULT_TENANT_SLUG)

    @app.route("/logout")
    def logout():
        if session.get("username"):
            log_action("خروج", "تسجيل خروج", session.get("username", ""))
        if session.get("app_id"):
            get_db().execute(
                "DELETE FROM online_users WHERE app_id=? AND tenant_id=?",
                (session.get("app_id"), get_current_tenant_id()),
            )
            get_db().commit()
        session.clear()
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        db = get_db()
        tid = get_current_tenant_id()
        stats = {
            "clients": db.execute("SELECT COUNT(*) c FROM clients WHERE tenant_id=?", (tid,)).fetchone()["c"],
            "cases": db.execute("SELECT COUNT(*) c FROM cases WHERE tenant_id=?", (tid,)).fetchone()["c"],
            "sessions": db.execute("SELECT COUNT(*) c FROM sessions WHERE tenant_id=?", (tid,)).fetchone()["c"],
            "tasks_pending": db.execute("SELECT COUNT(*) c FROM tasks WHERE status!='done' AND tenant_id=?", (tid,)).fetchone()["c"],
            "income": db.execute("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE tenant_id=?", (tid,)).fetchone()["s"],
            "expenses": db.execute("SELECT COALESCE(SUM(amount),0) s FROM expenses WHERE tenant_id=?", (tid,)).fetchone()["s"],
        }
        upcoming_sessions = db.execute(
            """
            SELECT s.id, s.session_date, s.session_time, s.result, c.case_num, c.subject
            FROM sessions s
            LEFT JOIN cases c ON c.id = s.case_id
            WHERE s.session_date IS NOT NULL AND s.session_date != '' AND s.tenant_id=?
            ORDER BY s.session_date ASC, s.id DESC
            LIMIT 8
            """
            , (tid,)
        ).fetchall()
        urgent_cases = db.execute(
            """
            SELECT id, case_num, subject, status, type, court
            FROM cases
            WHERE tenant_id=?
            ORDER BY id DESC
            LIMIT 6
            """
            , (tid,)
        ).fetchall()
        recent_activity = db.execute(
            """
            SELECT id, log_type, detail, created_at, username
            FROM logs
            WHERE tenant_id=?
            ORDER BY id DESC
            LIMIT 10
            """
            , (tid,)
        ).fetchall()
        done_tasks = db.execute("SELECT COUNT(*) c FROM tasks WHERE status='done' AND tenant_id=?", (tid,)).fetchone()["c"]
        total_tasks = db.execute("SELECT COUNT(*) c FROM tasks WHERE tenant_id=?", (tid,)).fetchone()["c"] or 1
        insight = {
            "tasks_completion": round((done_tasks / total_tasks) * 100, 1),
            "case_pressure": "مرتفع" if stats["tasks_pending"] > 10 else ("متوسط" if stats["tasks_pending"] > 4 else "منخفض"),
            "net_balance": float(stats["income"] or 0) - float(stats["expenses"] or 0),
        }
        return render_template(
            "dashboard.html",
            stats=stats,
            upcoming_sessions=upcoming_sessions,
            urgent_cases=urgent_cases,
            recent_activity=recent_activity,
            insight=insight,
        )

    @app.route("/notifications")
    @login_required
    def notifications():
        db = get_db()
        tid = get_current_tenant_id()
        task_rows = db.execute(
            """
            SELECT id, title, due_date, priority, status, created_at
            FROM tasks
            WHERE status!='done' AND tenant_id=?
            ORDER BY
              CASE WHEN due_date IS NULL OR due_date='' THEN 1 ELSE 0 END,
              due_date ASC,
              id DESC
            LIMIT 30
            """
            , (tid,)
        ).fetchall()
        log_rows = db.execute(
            """
            SELECT id, log_type, detail, created_at
            FROM logs
            WHERE tenant_id=?
            ORDER BY id DESC
            LIMIT 20
            """
            , (tid,)
        ).fetchall()
        today = datetime.now().strftime("%Y-%m-%d")
        session_rows = db.execute(
            """
            SELECT s.id, s.session_date, s.session_time, s.result, s.court,
                   c.case_num, c.subject AS case_subject, c.id AS case_ref_id
            FROM sessions s
            LEFT JOIN cases c ON c.id = s.case_id AND c.tenant_id = s.tenant_id
            WHERE s.tenant_id=?
              AND (s.session_date >= ? OR (s.session_date IS NULL OR s.session_date = ''))
            ORDER BY s.session_date ASC, s.id DESC
            LIMIT 25
            """
            , (tid, today),
        ).fetchall()
        smart_counts = get_smart_alert_counts(db, tid)
        # Load smart notifications
        smart_notifs = []
        try:
            smart_notifs = db.execute(
                """SELECT id, notif_type, title, body, ref_table, ref_id, is_read, created_at
                   FROM smart_notifications
                   WHERE tenant_id=?
                   ORDER BY is_read ASC, id DESC
                   LIMIT 60""",
                (tid,),
            ).fetchall()
        except Exception:
            pass
        return render_template(
            "notifications.html",
            tasks=task_rows,
            logs=log_rows,
            session_rows=session_rows,
            smart_counts=smart_counts,
            smart_notifs=smart_notifs,
        )

    @app.get("/brand-logo.png")
    def brand_logo():
        if BRAND_LOGO_PATH.exists():
            return send_file(BRAND_LOGO_PATH, mimetype="image/png")
        return ("Brand logo not found", 404)

    @app.get("/billing")
    @login_required
    def billing():
        tid = get_current_tenant_id()
        db = get_db()
        invoices = db.execute(
            """
            SELECT id, invoice_no, amount, status, due_date, paid_at, created_at
            FROM billing_invoices
            WHERE tenant_id=?
            ORDER BY id DESC
            LIMIT 50
            """,
            (tid,),
        ).fetchall()
        payments = db.execute(
            """
            SELECT id, invoice_id, amount, method, reference, pay_date, created_at
            FROM billing_payments
            WHERE tenant_id=?
            ORDER BY id DESC
            LIMIT 50
            """,
            (tid,),
        ).fetchall()
        # Stats for billing page
        total_invoiced = sum(float(r["amount"] or 0) for r in invoices)
        total_paid = sum(float(r["amount"] or 0) for r in payments)
        pending_count = sum(1 for r in invoices if r["status"] == "pending")
        overdue_count = 0
        today_str = datetime.now().strftime("%Y-%m-%d")
        overdue_count = sum(
            1 for r in invoices
            if r["status"] == "pending" and r["due_date"] and r["due_date"] < today_str
        )
        # Also pull payments with client/case info
        payments_rich = []
        try:
            payments_rich = db.execute(
                """SELECT p.id, p.amount, p.method, p.pay_date, p.reference, p.notes,
                          cl.name AS client_name, ca.case_num
                   FROM payments p
                   LEFT JOIN clients cl ON cl.id=p.client_id AND cl.tenant_id=p.tenant_id
                   LEFT JOIN cases ca ON ca.id=p.case_id AND ca.tenant_id=p.tenant_id
                   WHERE p.tenant_id=?
                   ORDER BY p.id DESC LIMIT 30""",
                (tid,),
            ).fetchall()
        except Exception:
            pass
        billing_stats = {
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "outstanding": total_invoiced - total_paid,
            "pending_count": pending_count,
            "overdue_count": overdue_count,
        }
        return render_template(
            "billing.html",
            invoices=invoices,
            payments=payments,
            payments_rich=payments_rich,
            billing_stats=billing_stats,
            today_str=datetime.now().strftime("%Y-%m-%d"),
            now_year=datetime.now().year,
        )

    @app.route("/settings/system", methods=["GET", "POST"])
    @login_required
    @system_settings_required
    def settings_system():
        if request.method == "POST":
            action = (request.form.get("action") or "").strip()
            if action == "save_settings":
                settings = load_system_settings()
                name = (request.form.get("system_name") or "").strip()
                if name:
                    settings["system_name"] = name
                overrides: dict[str, dict[str, str]] = {}
                db = get_db()
                tenant_rows = db.execute(
                    "SELECT id, slug FROM tenants WHERE active=1 ORDER BY id ASC"
                ).fetchall()
                for row in tenant_rows:
                    tid = row["id"]
                    label = (request.form.get(f"tenant_label_{tid}") or "").strip()
                    branch = (request.form.get(f"tenant_branch_{tid}") or "").strip()
                    if label or branch:
                        overrides[row["slug"]] = {"label": label, "branch": branch}
                settings["tenant_overrides"] = overrides
                save_system_settings(settings)
                log_action("إعدادات", "تحديث اسم النظام وتسميات الفروع", session.get("username", ""))
                flash("تم حفظ إعدادات النظام.", "success")
                return redirect(url_for("settings_system"))

            if action == "create_backup":
                BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest = BACKUP_ROOT / stamp
                try:
                    dest.mkdir(parents=False)
                except FileExistsError:
                    flash("تعذر إنشاء مجلد النسخة الاحتياطية.", "danger")
                    return redirect(url_for("settings_system"))
                close_db()
                try:
                    for path in (DB_PATH, DOCS_DB_PATH):
                        if path.exists():
                            _sqlite_checkpoint(path)
                            shutil.copy2(path, dest / path.name)
                            for ext in ("-wal", "-shm"):
                                w = Path(str(path) + ext)
                                if w.exists():
                                    shutil.copy2(w, dest / w.name)
                    if SYSTEM_SETTINGS_PATH.exists():
                        shutil.copy2(SYSTEM_SETTINGS_PATH, dest / "system_settings.json")
                    manifest = {
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                        "main_db": DB_PATH.name,
                        "docs_db": DOCS_DB_PATH.name,
                    }
                    (dest / "backup_manifest.json").write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                except OSError as exc:
                    flash(f"فشل إنشاء النسخة الاحتياطية: {exc}", "danger")
                    return redirect(url_for("settings_system"))
                log_action("نسخ احتياطي", f"إنشاء نسخة {stamp}", session.get("username", ""))
                flash(f"تم إنشاء نسخة احتياطية: {stamp}", "success")
                return redirect(url_for("settings_system"))

            if action == "restore_backup":
                backup_id = (request.form.get("backup_id") or "").strip()
                confirm = (request.form.get("restore_confirm") or "").strip()
                if confirm != "استعادة":
                    flash('للتأكيد اكتب كلمة "استعادة" في حقل التأكيد.', "warning")
                    return redirect(url_for("settings_system"))
                src = _safe_backup_dir(backup_id)
                if not src or not (src / DB_PATH.name).exists():
                    flash("نسخة احتياطية غير صالحة أو ناقصة.", "danger")
                    return redirect(url_for("settings_system"))
                close_db()
                try:
                    for path in (DB_PATH, DOCS_DB_PATH):
                        if (src / path.name).exists():
                            for ext in ("-wal", "-shm"):
                                w = path.parent / f"{path.name}{ext}"
                                if w.exists():
                                    try:
                                        w.unlink()
                                    except OSError:
                                        pass
                            _copy_sqlite_family(src, path)
                    ss = src / "system_settings.json"
                    if ss.exists():
                        shutil.copy2(ss, SYSTEM_SETTINGS_PATH)
                except OSError as exc:
                    flash(f"فشل الاستعادة: {exc}", "danger")
                    return redirect(url_for("settings_system"))
                log_action("استعادة", f"استعادة نسخة {backup_id}", session.get("username", ""))
                flash("تم استعادة النسخة الاحتياطية. يُفضّل إعادة تحميل الصفحة أو إعادة تشغيل الخادم إن لزم.", "success")
                return redirect(url_for("settings_system"))

            flash("إجراء غير معروف.", "warning")
            return redirect(url_for("settings_system"))

        db = get_db()
        tenants = db.execute(
            "SELECT id, name, slug, subscription_plan FROM tenants WHERE active=1 ORDER BY id ASC"
        ).fetchall()
        settings = load_system_settings()
        overrides = settings.get("tenant_overrides") or {}
        backup_entries = []
        if BACKUP_ROOT.exists():
            for p in sorted(BACKUP_ROOT.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                if not p.is_dir():
                    continue
                manifest = {}
                mf = p / "backup_manifest.json"
                if mf.exists():
                    try:
                        manifest = json.loads(mf.read_text(encoding="utf-8"))
                    except Exception:
                        manifest = {}
                backup_entries.append(
                    {
                        "id": p.name,
                        "created_at": manifest.get("created_at", ""),
                        "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                    }
                )
        return render_template(
            "system_settings.html",
            title="إعدادات النظام",
            settings=settings,
            tenants=tenants,
            overrides=overrides,
            backups=backup_entries,
            db_main_name=DB_PATH.name,
            db_docs_name=DOCS_DB_PATH.name,
        )

    @app.get("/settings/system/backup/<backup_id>.zip")
    @login_required
    @system_settings_required
    def settings_backup_download(backup_id: str):
        src = _safe_backup_dir(backup_id)
        if not src:
            flash("نسخة غير صالحة.", "danger")
            return redirect(url_for("settings_system"))
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(src.rglob("*")):
                if path.is_file():
                    zf.write(path, arcname=str(path.relative_to(src)))
        buf.seek(0)
        return send_file(
            buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"law_office_backup_{backup_id}.zip",
        )

    @app.get("/api/v1/tenant/summary")
    @login_required
    def api_tenant_summary():
        tid = get_current_tenant_id()
        db = get_db()
        tenant = db.execute(
            "SELECT id, name, slug, subscription_plan, theme_primary FROM tenants WHERE id=?",
            (tid,),
        ).fetchone()
        if not tenant:
            return jsonify({"error": "tenant not found"}), 404
        usage = {
            "users": db.execute("SELECT COUNT(*) c FROM users WHERE tenant_id=?", (tid,)).fetchone()["c"],
            "cases": db.execute("SELECT COUNT(*) c FROM cases WHERE tenant_id=?", (tid,)).fetchone()["c"],
            "storage_docs": db.execute("SELECT COUNT(*) c FROM documents WHERE tenant_id=?", (tid,)).fetchone()["c"],
        }
        return jsonify(
            {
                "tenant": dict(tenant),
                "plan_features": PLAN_FEATURES.get(tenant["subscription_plan"], PLAN_FEATURES["Basic"]),
                "usage": usage,
            }
        )

    @api_v1.get("/auth/me")
    @login_required
    def api_auth_me():
        tid = get_current_tenant_id()
        db = get_db()
        user = db.execute(
            "SELECT id, name, username, role, email, phone, tenant_id FROM users WHERE id=? AND tenant_id=?",
            (session.get("user_id"), tid),
        ).fetchone()
        if not user:
            return jsonify({"error": "user not found"}), 404
        tenant = db.execute(
            "SELECT id, name, slug, subscription_plan, theme_primary FROM tenants WHERE id=?",
            (tid,),
        ).fetchone()
        return jsonify(
            {
                "user": dict(user),
                "tenant": dict(tenant) if tenant else None,
                "permissions": parse_permissions(session.get("permissions", "[]")),
            }
        )

    @api_v1.get("/tenants")
    def api_tenants():
        rows = get_db().execute(
            "SELECT id, name, slug, subscription_plan, theme_primary, active FROM tenants ORDER BY id ASC"
        ).fetchall()
        return jsonify({"items": [dict(r) for r in rows]})

    @api_v1.get("/billing/invoices")
    @login_required
    def api_billing_invoices():
        tid = get_current_tenant_id()
        rows = get_db().execute(
            """
            SELECT id, invoice_no, amount, status, due_date, paid_at, created_at
            FROM billing_invoices
            WHERE tenant_id=?
            ORDER BY id DESC
            LIMIT 200
            """,
            (tid,),
        ).fetchall()
        return jsonify({"items": [dict(r) for r in rows]})

    @api_v1.get("/billing/payments")
    @login_required
    def api_billing_payments():
        tid = get_current_tenant_id()
        rows = get_db().execute(
            """
            SELECT id, invoice_id, amount, method, reference, pay_date, created_at
            FROM billing_payments
            WHERE tenant_id=?
            ORDER BY id DESC
            LIMIT 200
            """,
            (tid,),
        ).fetchall()
        return jsonify({"items": [dict(r) for r in rows]})

    @api_v1.get("/modules/<table>")
    @login_required
    def api_module_rows(table: str):
        cfg = TABLE_CONFIG.get(table)
        if not cfg:
            return jsonify({"error": "unsupported table"}), 400
        tid = get_current_tenant_id()
        rows = get_db().execute(
            f"SELECT * FROM {table} WHERE tenant_id=? ORDER BY {cfg['pk']} DESC LIMIT 500",
            (tid,),
        ).fetchall()
        return jsonify(
            {
                "table": table,
                "title": cfg["title"],
                "pk": cfg["pk"],
                "fields": cfg["fields"],
                "items": [dict(r) for r in rows],
            }
        )

    @app.route("/billing/invoice/new", methods=["GET", "POST"])
    @login_required
    def billing_invoice_new():
        tid = get_current_tenant_id()
        db = get_db()
        if request.method == "POST":
            invoice_no = request.form.get("invoice_no", "").strip()
            amount = request.form.get("amount", "0").strip()
            due_date = request.form.get("due_date", "").strip()
            status = request.form.get("status", "pending").strip()
            if not invoice_no or not amount:
                flash("رقم الفاتورة والمبلغ مطلوبان", "warning")
                return redirect(url_for("billing"))
            try:
                amount_f = float(amount)
            except ValueError:
                flash("المبلغ يجب أن يكون رقماً", "warning")
                return redirect(url_for("billing"))
            db.execute(
                """INSERT INTO billing_invoices(tenant_id, invoice_no, amount, status, due_date)
                   VALUES (?,?,?,?,?)""",
                (tid, invoice_no, amount_f, status, due_date),
            )
            db.commit()
            log_action("فوترة", f"إنشاء فاتورة {invoice_no} بمبلغ {amount_f} ر.س")
            flash(f"تم إنشاء الفاتورة {invoice_no} بنجاح.", "success")
            return redirect(url_for("billing"))
        return redirect(url_for("billing"))

    @app.route("/billing/invoice/<int:inv_id>/pay", methods=["POST"])
    @login_required
    def billing_invoice_pay(inv_id: int):
        tid = get_current_tenant_id()
        db = get_db()
        invoice = db.execute(
            "SELECT * FROM billing_invoices WHERE id=? AND tenant_id=?", (inv_id, tid)
        ).fetchone()
        if not invoice:
            flash("الفاتورة غير موجودة", "danger")
            return redirect(url_for("billing"))
        amount = request.form.get("amount", str(invoice["amount"])).strip()
        method = request.form.get("method", "card").strip()
        reference = request.form.get("reference", "").strip()
        pay_date = request.form.get("pay_date", datetime.now().strftime("%Y-%m-%d")).strip()
        try:
            amount_f = float(amount)
        except ValueError:
            amount_f = float(invoice["amount"])
        db.execute(
            """INSERT INTO billing_payments(tenant_id, invoice_id, amount, method, reference, pay_date)
               VALUES (?,?,?,?,?,?)""",
            (tid, inv_id, amount_f, method, reference, pay_date),
        )
        db.execute(
            "UPDATE billing_invoices SET status='paid', paid_at=? WHERE id=? AND tenant_id=?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), inv_id, tid),
        )
        db.commit()
        log_action("فوترة", f"تسجيل دفع فاتورة #{inv_id} بمبلغ {amount_f} ر.س")
        # Push success notification
        try:
            push_notification(
                db, tid, "success",
                f"تم سداد الفاتورة {invoice['invoice_no']} — {amount_f} ر.س",
                f"طريقة الدفع: {method}",
                "billing_invoices", inv_id,
            )
        except Exception:
            pass
        flash(f"تم تسجيل دفعة {amount_f} ر.س للفاتورة {invoice['invoice_no']}.", "success")
        return redirect(url_for("billing"))

    @app.route("/billing/invoice/<int:inv_id>/delete", methods=["POST"])
    @login_required
    def billing_invoice_delete(inv_id: int):
        tid = get_current_tenant_id()
        db = get_db()
        db.execute("DELETE FROM billing_invoices WHERE id=? AND tenant_id=?", (inv_id, tid))
        db.execute("DELETE FROM billing_payments WHERE invoice_id=? AND tenant_id=?", (inv_id, tid))
        db.commit()
        log_action("فوترة", f"حذف فاتورة #{inv_id}")
        flash("تم حذف الفاتورة.", "success")
        return redirect(url_for("billing"))

    @app.route("/about")
    @login_required
    def about():
        return render_template("about.html", title="حول البرنامج")

    @app.route("/connected-users")
    @login_required
    @permission_required("connected_users_view")
    def connected_users():
        tid = get_current_tenant_id()
        raw_rows = get_db().execute(
            """
            SELECT user_id, username, status, last_seen, device_name, ip
            FROM online_users
            WHERE tenant_id=?
            ORDER BY last_seen DESC
            """
            , (tid,)
        ).fetchall()
        rows = consolidate_connected_users(raw_rows)
        online_count = sum(1 for r in rows if r["is_live"])
        offline_count = len(rows) - online_count
        return render_template(
            "connected_users.html",
            rows=rows,
            online_count=online_count,
            offline_count=offline_count,
            title="المتصلون",
        )

    @app.route("/table/<table>")
    @login_required
    def table_list(table: str):
        cfg = TABLE_CONFIG.get(table)
        if not cfg:
            flash("الجدول غير مدعوم", "warning")
            return redirect(url_for("dashboard"))
        q = (request.args.get("q") or "").strip()
        db = get_db()
        tid = get_current_tenant_id()
        if table == "cases":
            status_filter = (request.args.get("status") or "all").strip()
            if status_filter not in {k for k, _ in CASE_STATUS_FILTERS}:
                status_filter = "all"
            case_rows = fetch_cases_list(db, tid, q, status_filter)
            case_stats = case_status_stats(db, tid)
            return render_template(
                "cases_page.html",
                table=table,
                cfg=cfg,
                rows=case_rows,
                q=q,
                status_filter=status_filter,
                status_filters=CASE_STATUS_FILTERS,
                case_stats=case_stats,
            )

        linked = _linked_table_query(table, tid, q)
        if linked:
            rows, columns, subtitle = linked
            rows = [dict(r) for r in rows]
            return render_template(
                "smart_list.html",
                table=table,
                cfg=cfg,
                rows=rows,
                q=q,
                list_columns=columns,
                list_subtitle=subtitle,
                module_icon=MODULE_ICONS.get(table, "📋"),
            )
        if q and table in ("clients", "cases", "users"):
            if table == "clients":
                rows = db.execute(
                    "SELECT * FROM clients WHERE tenant_id=? AND (name LIKE ? OR phone LIKE ? OR email LIKE ?) ORDER BY id DESC LIMIT 500",
                    (tid, f"%{q}%", f"%{q}%", f"%{q}%"),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM cases WHERE tenant_id=? AND (case_num LIKE ? OR subject LIKE ? OR status LIKE ?) ORDER BY id DESC LIMIT 500",
                    (tid, f"%{q}%", f"%{q}%", f"%{q}%"),
                ).fetchall()
            if table == "users":
                rows = db.execute(
                    """
                    SELECT * FROM users
                    WHERE role!='dev_master' AND tenant_id=?
                      AND (name LIKE ? OR username LIKE ? OR role LIKE ?)
                    ORDER BY id DESC LIMIT 500
                    """,
                    (tid, f"%{q}%", f"%{q}%", f"%{q}%"),
                ).fetchall()
        else:
            if table == "users":
                rows = db.execute(
                    "SELECT * FROM users WHERE role!='dev_master' AND tenant_id=? ORDER BY id DESC LIMIT 500",
                    (tid,),
                ).fetchall()
            else:
                rows = db.execute(f"SELECT * FROM {table} WHERE tenant_id=? ORDER BY {cfg['pk']} DESC LIMIT 500", (tid,)).fetchall()

        if table == "clients":
            return render_template("clients_page.html", table=table, cfg=cfg, rows=rows, q=q)
        if table == "users":
            return render_template("users_page.html", table=table, cfg=cfg, rows=rows, q=q, roles=USER_ROLES)
        return render_template("list.html", table=table, cfg=cfg, rows=rows, q=q)

    @app.get("/api/search")
    @login_required
    def api_search():
        q = (request.args.get("q") or "").strip()
        if not q:
            return jsonify({"results": []})
        db = get_db()
        tid = get_current_tenant_id()
        out = []
        clients = db.execute(
            "SELECT id, name, phone FROM clients WHERE tenant_id=? AND (name LIKE ? OR phone LIKE ?) ORDER BY id DESC LIMIT 5",
            (tid, f"%{q}%", f"%{q}%"),
        ).fetchall()
        for r in clients:
            out.append({"type": "عميل", "title": r["name"], "subtitle": r["phone"] or "", "url": url_for("table_edit", table="clients", row_id=r["id"])})
        cases = db.execute(
            "SELECT id, case_num, subject FROM cases WHERE tenant_id=? AND (case_num LIKE ? OR subject LIKE ?) ORDER BY id DESC LIMIT 5",
            (tid, f"%{q}%", f"%{q}%"),
        ).fetchall()
        for r in cases:
            out.append({"type": "قضية", "title": r["case_num"], "subtitle": r["subject"] or "", "url": url_for("table_edit", table="cases", row_id=r["id"])})
        return jsonify({"results": out[:10]})

    @app.get("/api/clients/picker")
    @login_required
    def api_clients_picker():
        tid = get_current_tenant_id()
        q = (request.args.get("q") or "").strip()
        db = get_db()
        if q:
            like = f"%{q}%"
            rows = db.execute(
                """
                SELECT id, name, phone, type, id_num
                FROM clients
                WHERE tenant_id=? AND active=1
                  AND (name LIKE ? OR phone LIKE ? OR phone2 LIKE ? OR id_num LIKE ? OR email LIKE ?)
                ORDER BY name ASC
                LIMIT 25
                """,
                (tid, like, like, like, like, like),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT id, name, phone, type, id_num
                FROM clients
                WHERE tenant_id=? AND active=1
                ORDER BY name ASC
                LIMIT 30
                """,
                (tid,),
            ).fetchall()
        return jsonify(
            {
                "clients": [
                    {
                        "id": r["id"],
                        "name": r["name"],
                        "phone": r["phone"] or "",
                        "type": r["type"] or "",
                        "id_num": r["id_num"] or "",
                        "label": f"{r['name']} — {r['phone'] or 'بدون هاتف'}",
                    }
                    for r in rows
                ]
            }
        )

    @app.get("/api/cases/picker")
    @login_required
    def api_cases_picker():
        tid = get_current_tenant_id()
        q = (request.args.get("q") or "").strip()
        db = get_db()
        if q:
            like = f"%{q}%"
            rows = db.execute(
                """
                SELECT id, case_num, subject, status, court
                FROM cases
                WHERE tenant_id=?
                  AND (case_num LIKE ? OR subject LIKE ? OR court LIKE ? OR status LIKE ?)
                ORDER BY id DESC
                LIMIT 25
                """,
                (tid, like, like, like, like),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT id, case_num, subject, status, court
                FROM cases
                WHERE tenant_id=?
                ORDER BY id DESC
                LIMIT 30
                """,
                (tid,),
            ).fetchall()
        return jsonify(
            {
                "cases": [
                    {
                        "id": r["id"],
                        "case_num": r["case_num"],
                        "subject": r["subject"] or "",
                        "status": r["status"] or "",
                        "court": r["court"] or "",
                        "label": f"{r['case_num']} — {r['subject'] or 'بدون موضوع'}",
                    }
                    for r in rows
                ]
            }
        )

    @app.route("/table/<table>/new", methods=["GET", "POST"])
    @login_required
    def table_create(table: str):
        cfg = TABLE_CONFIG.get(table)
        if not cfg:
            return redirect(url_for("dashboard"))
        tid = get_current_tenant_id()
        if table == "users":
            if request.method == "POST":
                selected_perms = request.form.getlist("permissions")
                if session.get("role") != "dev_master":
                    selected_perms = [p for p in selected_perms if p != "connected_users_view"]
                role = request.form.get("role", "assistant").strip() or "assistant"
                if role not in {"admin", "lawyer", "assistant"}:
                    role = "assistant"
                get_db().execute(
                    """
                    INSERT INTO users(name,username,password,role,email,phone,permissions,expire_msg,active,tenant_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        request.form.get("name", "").strip(),
                        request.form.get("username", "").strip(),
                        hash_password(request.form.get("password", "123456")),
                        role,
                        request.form.get("email", "").strip(),
                        request.form.get("phone", "").strip(),
                        json.dumps(selected_perms, ensure_ascii=False),
                        request.form.get("expire_msg", "").strip(),
                        int(request.form.get("active", "1") == "1"),
                        tid,
                    ),
                )
                get_db().commit()
                log_action("إضافة مستخدم", "إضافة مستخدم جديد", request.form.get("username", ""))
                return redirect(url_for("table_list", table="users"))
            return render_template("user_form.html", row=None, roles=USER_ROLES, permission_options=PERMISSION_OPTIONS)
        if request.method == "POST":
            db = get_db()
            if table == "clients":
                name = request.form.get("name", "").strip()
                phone = request.form.get("phone", "").strip()
                if not name or not phone:
                    flash("الاسم والهاتف مطلوبان", "warning")
                    return render_template(
                        "client_form.html",
                        table=table,
                        cfg=cfg,
                        row=None,
                        client_types=CLIENT_TYPE_OPTIONS,
                    )
            if table == "cases":
                cid = validate_client_id_for_tenant(db, tid, request.form.get("client_id", ""))
                if not cid:
                    flash("يجب اختيار عميل مسجّل من النظام", "warning")
                    return render_template(
                        "case_form.html",
                        table=table,
                        cfg=cfg,
                        row=None,
                        selected_client=get_client_picker_item(db, tid, None),
                        case_statuses=CASE_STATUS_OPTIONS,
                        case_types=CASE_TYPE_OPTIONS,
                    )
            if table == "documents":
                ok, fk_overrides_doc = validate_smart_form_post(table, db, tid, request.form)
                if not ok:
                    flash(_smart_form_error_message(table), "warning")
                    return render_template(
                        SMART_FORM_TEMPLATES[table],
                        **build_smart_form_context(table, cfg, None, db, tid),
                    )
                doc_id = insert_document_record(db, tid, request.form, fk_overrides_doc)
                db.commit()
                uploaded = request.files.get("file")
                if uploaded and uploaded.filename:
                    ok_up, msg = save_document_upload(doc_id, uploaded)
                    if ok_up:
                        flash(f"تم حفظ المستند ورفع الملف ({msg}) بنجاح.", "success")
                    else:
                        flash(f"تم حفظ المستند. تعذّر رفع الملف: {msg}", "warning")
                else:
                    flash("تم حفظ المستند. يمكنك رفع الملف من صفحة التعديل.", "success")
                log_action("مستندات", f"إضافة مستند #{doc_id}")
                return redirect(url_for("table_list", table="documents"))
            fk_overrides: dict[str, str] = {}
            if table in SMART_FORM_TEMPLATES:
                ok, fk_overrides = validate_smart_form_post(table, db, tid, request.form)
                if not ok:
                    flash(_smart_form_error_message(table), "warning")
                    pre_case = _arg_int(request.args.get("case_id"))
                    return render_template(
                        SMART_FORM_TEMPLATES[table],
                        **build_smart_form_context(table, cfg, None, db, tid, preselect_case_id=pre_case),
                    )
            fields = cfg["fields"][:]
            values = []
            for f in fields:
                if f in fk_overrides:
                    values.append(fk_overrides[f])
                elif table == "cases" and f == "client_id":
                    values.append(str(cid))
                else:
                    values.append(request.form.get(f, "").strip())
            if table == "users":
                fields.append("password")
                values.append(hash_password(request.form.get("password", "123456")))
            fields.append("tenant_id")
            values.append(tid)
            placeholders = ",".join("?" for _ in fields)
            get_db().execute(f"INSERT INTO {table} ({','.join(fields)}) VALUES ({placeholders})", values)
            get_db().commit()
            log_action("إضافة", f"إضافة سجل جديد في {table}")
            flash_smart_save_message(table, db, tid, request.form)
            return redirect(url_for("table_list", table=table))
        pre_case = _arg_int(request.args.get("case_id"))
        if table == "clients":
            return render_template(
                "client_form.html",
                table=table,
                cfg=cfg,
                row=None,
                client_types=CLIENT_TYPE_OPTIONS,
            )
        if table == "cases":
            return render_template(
                "case_form.html",
                table=table,
                cfg=cfg,
                row=None,
                selected_client=None,
                case_statuses=CASE_STATUS_OPTIONS,
                case_types=CASE_TYPE_OPTIONS,
            )
        if table in SMART_FORM_TEMPLATES:
            return render_template(
                SMART_FORM_TEMPLATES[table],
                **build_smart_form_context(table, cfg, None, get_db(), tid, preselect_case_id=pre_case),
            )
        return render_template("form.html", table=table, cfg=cfg, row=None)

    @app.route("/table/<table>/<int:row_id>/edit", methods=["GET", "POST"])
    @login_required
    def table_edit(table: str, row_id: int):
        cfg = TABLE_CONFIG.get(table)
        if not cfg:
            return redirect(url_for("dashboard"))
        db = get_db()
        tid = get_current_tenant_id()
        row = db.execute(f"SELECT * FROM {table} WHERE {cfg['pk']}=? AND tenant_id=?", (row_id, tid)).fetchone()
        if not row:
            flash("السجل غير موجود", "warning")
            return redirect(url_for("table_list", table=table))
        if table == "users" and row["role"] == "dev_master" and session.get("role") != "dev_master":
            flash("غير مسموح بالوصول لهذا المستخدم", "warning")
            return redirect(url_for("table_list", table="users"))
        if request.method == "POST":
            if table == "users":
                if row["role"] == "dev_master":
                    flash("لا يمكن تعديل حساب مطور النظام من هذه الشاشة", "warning")
                    return redirect(url_for("table_list", table="users"))
                selected_perms = request.form.getlist("permissions")
                if session.get("role") != "dev_master":
                    # غير المطور لا يقدر يمنح شاشة المتصلين
                    selected_perms = [p for p in selected_perms if p != "connected_users_view"]
                role = request.form.get("role", "assistant").strip() or "assistant"
                if role not in {"admin", "lawyer", "assistant"}:
                    role = row["role"]
                vals = [
                    request.form.get("name", "").strip(),
                    request.form.get("username", "").strip(),
                    role,
                    request.form.get("email", "").strip(),
                    request.form.get("phone", "").strip(),
                    json.dumps(selected_perms, ensure_ascii=False),
                    request.form.get("expire_msg", "").strip(),
                    int(request.form.get("active", "1") == "1"),
                ]
                sql = """
                    UPDATE users
                    SET name=?, username=?, role=?, email=?, phone=?, permissions=?, expire_msg=?, active=?
                """
                if request.form.get("password", "").strip():
                    sql += ", password=?"
                    vals.append(hash_password(request.form.get("password", "").strip()))
                sql += " WHERE id=? AND tenant_id=?"
                vals.append(row_id)
                vals.append(tid)
                db.execute(sql, vals)
                db.commit()
                log_action("تعديل مستخدم", f"تعديل المستخدم #{row_id}", row["username"])
                return redirect(url_for("table_list", table="users"))
            if table == "clients":
                name = request.form.get("name", "").strip()
                phone = request.form.get("phone", "").strip()
                if not name or not phone:
                    flash("الاسم والهاتف مطلوبان", "warning")
                    return render_template(
                        "client_form.html",
                        table=table,
                        cfg=cfg,
                        row=row,
                        client_types=CLIENT_TYPE_OPTIONS,
                    )
            cid = None
            if table == "cases":
                cid = validate_client_id_for_tenant(db, tid, request.form.get("client_id", ""))
                if not cid:
                    flash("يجب اختيار عميل مسجّل من النظام", "warning")
                    return render_template(
                        "case_form.html",
                        table=table,
                        cfg=cfg,
                        row=row,
                        selected_client=get_client_picker_item(db, tid, row["client_id"]),
                        case_statuses=CASE_STATUS_OPTIONS,
                        case_types=CASE_TYPE_OPTIONS,
                    )
            fk_overrides: dict[str, str] = {}
            if table in SMART_FORM_TEMPLATES:
                ok, fk_overrides = validate_smart_form_post(table, db, tid, request.form)
                if not ok:
                    flash(_smart_form_error_message(table), "warning")
                    return render_template(
                        SMART_FORM_TEMPLATES[table],
                        **build_smart_form_context(table, cfg, row, db, tid),
                    )
            updates = []
            values = []
            for f in cfg["fields"]:
                updates.append(f"{f}=?")
                if f in fk_overrides:
                    val = fk_overrides[f]
                elif table == "cases" and f == "client_id":
                    val = str(cid)
                else:
                    val = request.form.get(f, "").strip()
                values.append(val)
            if table == "users" and request.form.get("password", "").strip():
                updates.append("password=?")
                values.append(hash_password(request.form["password"].strip()))
            values.append(row_id)
            values.append(tid)
            db.execute(f"UPDATE {table} SET {', '.join(updates)} WHERE {cfg['pk']}=? AND tenant_id=?", values)
            db.commit()
            if table == "documents":
                uploaded = request.files.get("file")
                if uploaded and uploaded.filename:
                    ok_up, msg = save_document_upload(row_id, uploaded)
                    if ok_up:
                        flash(f"تم تحديث المستند واستبدال الملف ({msg}).", "success")
                    else:
                        flash(f"تم التحديث. تعذّر رفع الملف: {msg}", "warning")
                else:
                    flash_smart_save_message(table, db, tid, request.form, row_id)
            else:
                flash_smart_save_message(table, db, tid, request.form, row_id)
            log_action("تعديل", f"تعديل سجل #{row_id} في {table}")
            return redirect(url_for("table_list", table=table))
        if table == "users":
            return render_template(
                "user_form.html",
                row=row,
                roles=USER_ROLES,
                permission_options=PERMISSION_OPTIONS,
                user_permissions=parse_permissions(row["permissions"]),
            )
        if table == "clients":
            return render_template(
                "client_form.html",
                table=table,
                cfg=cfg,
                row=row,
                client_types=CLIENT_TYPE_OPTIONS,
            )
        if table == "cases":
            return render_template(
                "case_form.html",
                table=table,
                cfg=cfg,
                row=row,
                selected_client=get_client_picker_item(db, tid, row["client_id"]),
                case_statuses=CASE_STATUS_OPTIONS,
                case_types=CASE_TYPE_OPTIONS,
            )
        if table in SMART_FORM_TEMPLATES:
            return render_template(
                SMART_FORM_TEMPLATES[table],
                **build_smart_form_context(table, cfg, row, db, tid),
            )
        return render_template("form.html", table=table, cfg=cfg, row=row)

    @app.post("/table/<table>/<int:row_id>/delete")
    @login_required
    def table_delete(table: str, row_id: int):
        cfg = TABLE_CONFIG.get(table)
        if not cfg:
            return redirect(url_for("dashboard"))
        db = get_db()
        tid = get_current_tenant_id()
        if table == "users":
            row_u = db.execute("SELECT role FROM users WHERE id=? AND tenant_id=?", (row_id, tid)).fetchone()
            if row_u and row_u["role"] == "dev_master":
                flash("لا يمكن حذف حساب مطور النظام", "warning")
                return redirect(url_for("table_list", table="users"))
        db.execute(f"DELETE FROM {table} WHERE {cfg['pk']}=? AND tenant_id=?", (row_id, tid))
        if table == "documents":
            get_docs_db().execute("DELETE FROM document_files WHERE doc_id=?", (row_id,))
            get_docs_db().commit()
        db.commit()
        log_action("حذف", f"حذف سجل #{row_id} من {table}")
        return redirect(url_for("table_list", table=table))

    @app.post("/documents/<int:doc_id>/upload")
    @login_required
    def upload_doc_file(doc_id: int):
        f = request.files.get("file")
        if not f or not f.filename:
            flash("اختر ملفا صالحا", "warning")
            return redirect(url_for("table_list", table="documents"))
        tid = get_current_tenant_id()
        has_doc = get_db().execute("SELECT 1 FROM documents WHERE id=? AND tenant_id=?", (doc_id, tid)).fetchone()
        if not has_doc:
            flash("المستند غير متاح لهذه الشركة", "warning")
            return redirect(url_for("table_list", table="documents"))
        payload = f.read()
        get_docs_db().execute(
            """
            INSERT INTO document_files(doc_id, file_data, mime_type, original_name, size_bytes)
            VALUES (?,?,?,?,?)
            ON CONFLICT(doc_id) DO UPDATE SET
            file_data=excluded.file_data,
            mime_type=excluded.mime_type,
            original_name=excluded.original_name,
            size_bytes=excluded.size_bytes
            """,
            (doc_id, payload, f.mimetype or "", f.filename, len(payload)),
        )
        get_docs_db().commit()
        log_action("مستندات", f"رفع ملف للمستند #{doc_id}")
        return redirect(url_for("table_list", table="documents"))

    @app.get("/documents/<int:doc_id>/download")
    @login_required
    def download_doc_file(doc_id: int):
        tid = get_current_tenant_id()
        has_doc = get_db().execute("SELECT 1 FROM documents WHERE id=? AND tenant_id=?", (doc_id, tid)).fetchone()
        if not has_doc:
            flash("المستند غير متاح لهذه الشركة", "warning")
            return redirect(url_for("table_list", table="documents"))
        row = get_docs_db().execute(
            "SELECT file_data, mime_type, original_name FROM document_files WHERE doc_id=?",
            (doc_id,),
        ).fetchone()
        if not row:
            flash("لا يوجد ملف مرفق لهذا المستند", "warning")
            return redirect(url_for("table_list", table="documents"))
        return send_file(
            BytesIO(row["file_data"]),
            mimetype=row["mime_type"] or "application/octet-stream",
            as_attachment=True,
            download_name=row["original_name"] or f"document_{doc_id}",
        )

    app.register_blueprint(api_v1)


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
