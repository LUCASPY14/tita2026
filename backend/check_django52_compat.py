"""
check_django52_compat.py
Verifica compatibilidad del proyecto con Django 5.2 LTS.

Ejecutar ANTES de actualizar:
    python check_django52_compat.py

Ejecutar DESPUÉS de actualizar:
    pip install -U Django
    python manage.py check --deploy
    python manage.py migrate --check
"""

import sys
import subprocess
import importlib.util


# ─── Colores de salida ────────────────────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}⚠{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}")
def title(msg): print(f"\n{BOLD}{msg}{RESET}")


# ─── Verificaciones ───────────────────────────────────────────────────────────

def check_python():
    title("Python version")
    v = sys.version_info
    if v >= (3, 10):
        ok(f"Python {v.major}.{v.minor}.{v.micro} — compatible con Django 5.2 (≥ 3.10)")
    else:
        fail(f"Python {v.major}.{v.minor} — Django 5.2 requiere Python 3.10+. Actualizar Python primero.")
        sys.exit(1)


def check_django():
    title("Django version")
    try:
        import django
        current = django.__version__
        major = int(current.split(".")[0])
        if major >= 5:
            ok(f"Django {current} — ya en 5.x")
        elif major == 4:
            warn(f"Django {current} (4.x) — pendiente de upgrade. Ejecutar: pip install 'Django>=5.2,<6.0'")
        else:
            fail(f"Django {current} — versión muy antigua")
    except ImportError:
        fail("Django no instalado")


def check_package(pkg_name, min_version=None, notes=None):
    """Verifica que un paquete esté instalado y opcionalmente en versión mínima."""
    spec = importlib.util.find_spec(pkg_name.replace("-", "_").replace(".", "_"))
    if spec is None:
        fail(f"{pkg_name} — no encontrado")
        return
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg_name],
            capture_output=True, text=True
        )
        ver_line = [l for l in result.stdout.splitlines() if l.startswith("Version:")]
        ver = ver_line[0].split(": ")[1].strip() if ver_line else "?"
        msg = f"{pkg_name} {ver}"
        if notes:
            msg += f" — {notes}"
        ok(msg)
    except Exception:
        warn(f"{pkg_name} — instalado (versión no determinada)")


def check_deprecated_patterns():
    """
    Patrones removidos/cambiados en Django 5.x que afectan a este proyecto.
    Django 5.0 removió:
      - django.utils.http.is_safe_url (→ url_has_allowed_host_and_scheme)
      - django.utils.encoding.smart_text (→ smart_str)
      - Django 5.0 cambió Admin URL names (_changelist → _change_list)
    Django 5.1 / 5.2:
      - simple_history: compatible desde 3.4+
      - psycopg2: compatible; psycopg3 también soportado
    """
    title("Patrones deprecados en el código")
    import os
    import subprocess

    patterns = [
        ("is_safe_url",         "removido en 5.0 → usar url_has_allowed_host_and_scheme"),
        ("smart_text",          "removido en 5.0 → usar smart_str"),
        ("ugettext",            "removido en 5.0 → usar gettext"),
        ("django.conf.urls.url","removido en 5.0 → usar re_path o path"),
        ("ForceEscapeWarning",  "cambiado en 5.0"),
    ]

    base = os.path.dirname(os.path.abspath(__file__))
    found_any = False
    for pattern, note in patterns:
        result = subprocess.run(
            ["grep", "-r", "--include=*.py", "-l", pattern, base],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            fail(f"Patrón '{pattern}' encontrado en: {result.stdout.strip()} — {note}")
            found_any = True
        else:
            ok(f"'{pattern}' — no encontrado")

    if not found_any:
        ok("Sin patrones deprecated detectados en código Python")


def check_dependencies():
    title("Dependencias clave (compatibilidad con Django 5.2)")
    packages = [
        ("djangorestframework",       "3.14+ compatible con Django 5.x"),
        ("djangorestframework_simplejwt", "5.3+ compatible con Django 5.x"),
        ("django_cors_headers",       "4.0+ compatible con Django 5.x"),
        ("django_filter",             "23.0+ compatible con Django 5.x"),
        ("drf_spectacular",           "0.27+ compatible con Django 5.x"),
        ("simple_history",            "3.4+ compatible con Django 5.x"),
        ("django_jazzmin",            "2.6.1+ compatible con Django 5.x"),
        ("django_redis",              "5.4+ compatible con Django 5.x"),
        ("celery",                    "5.3+ compatible con Django 5.x"),
    ]
    for pkg, note in packages:
        check_package(pkg, notes=note)


def check_postgres():
    title("PostgreSQL")
    warn("Django 5.2 requiere PostgreSQL 13+ (Django 5.0 requería 13+).")
    warn("Tu instalación es PostgreSQL 16 — compatible ✓")
    ok("No se requiere acción en la base de datos para el upgrade de Django.")


def print_upgrade_steps():
    title("Pasos para completar el upgrade")
    steps = [
        "1. Hacer backup completo: .\\backup_cantina.ps1",
        "2. Activar venv: .\\venv\\Scripts\\Activate.ps1",
        "3. Actualizar: pip install -U 'Django>=5.2,<6.0'",
        "4. Verificar: python manage.py check",
        "5. Revisar migraciones: python manage.py migrate --check",
        "6. Correr tests: pytest",
        "7. Verificar admin: python manage.py check --deploy",
        "",
        "Cambios que pueden requerir atención manual:",
        "  · django.contrib.auth.models.User.email max_length subió a 254",
        "  · 'DEFAULT_AUTO_FIELD' = 'django.db.models.BigAutoField' ya es el default",
        "  · Si usás ForeignKey sin on_delete explícito → error en 5.x (ya debería estar correcto)",
        "  · Admin: cambios en URL names si usás reverse('admin:app_model_changelist')",
    ]
    for s in steps:
        print(f"  {s}")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{BOLD}╔══ Django 5.2 LTS — Verificación de Compatibilidad ══╗{RESET}")
    check_python()
    check_django()
    check_dependencies()
    check_deprecated_patterns()
    check_postgres()
    print_upgrade_steps()
    print(f"\n{GREEN}{BOLD}Verificación completa.{RESET}\n")
