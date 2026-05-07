# Guía Rápida - Rama `desarrollo`

## 📁 Estructura del Proyecto

⚠️ **IMPORTANTE**: La rama `desarrollo` tiene una estructura diferente a `main`:

```
tita2026/
├── backend/              ← Django está AQUÍ (no en cantina_tita/backend/)
│   ├── manage.py        ✅ Archivo principal de Django
│   ├── venv/            ← Entorno virtual de desarrollo
│   ├── apps/
│   ├── backend/
│   └── ...
├── frontend/            ← React está AQUÍ (no en cantina_tita/frontend/)
│   ├── package.json    ✅ Archivo principal de React
│   ├── src/
│   └── ...
└── cantina_tita/        ⚠️ Esta carpeta está IGNORADA en .gitignore
    └── (archivos de rama main)
```

### Diferencias entre ramas:
- **Rama `main`**: Usa `cantina_tita/backend/` y `cantina_tita/frontend/`
- **Rama `desarrollo`**: Usa `backend/` y `frontend/` directamente en la raíz

---

## 🚀 Inicio Rápido

### Opción 1: Scripts PowerShell (Recomendado)

**Backend:**
```powershell
cd D:\tita2026\backend
.\run-dev-server.ps1
```

**Frontend:**
```powershell
cd D:\tita2026\frontend
.\run-dev-frontend.ps1
```

### Opción 2: Manual

**Backend:**
```powershell
cd D:\tita2026\backend
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```powershell
cd D:\tita2026\frontend
npm install  # Solo la primera vez
npm start
```

---

## ⚠️ Errores Comunes

### Error: `can't open file 'D:\tita2026\cantina_tita\backend\manage.py'`

**Causa:** Estás en el directorio incorrecto.

**Solución:**
```powershell
# ❌ NO ejecutes desde aquí:
cd D:\tita2026\cantina_tita\backend

# ✅ Ejecuta desde aquí:
cd D:\tita2026\backend
```

### Error: `venv not found` o `python: command not found`

**Solución:**
```powershell
# Activa el entorno virtual explícitamente:
D:\tita2026\cantina_tita\venv\Scripts\Activate.ps1

# O usa el script automático:
.\run-dev-server.ps1
```

---

## 🔧 Configuración Inicial

### Primera vez en la rama `desarrollo`:

1. **Crear entorno virtual** (si no existe):
```powershell
cd D:\tita2026\backend
python -m venv venv
```

2. **Instalar dependencias backend**:
```powershell
cd D:\tita2026\backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. **Configurar variables de entorno**:
```powershell
# Copiar .env.example a .env
cd D:\tita2026\backend
copy .env.example .env
```

4. **Ejecutar migraciones**:
```powershell
python manage.py migrate
```

5. **Instalar dependencias frontend**:
```powershell
cd D:\tita2026\frontend
npm install
```

---

## 📝 Notas Adicionales

- El entorno virtual (`venv`) está en `backend/venv/` específico para rama desarrollo
- Los scripts `run-dev-*.ps1` activan automáticamente el entorno virtual correcto
- La carpeta `cantina_tita/` completa está en `.gitignore` para evitar conflictos

---

## 🌐 URLs del Sistema

- **Backend API**: http://127.0.0.1:8000
- **Frontend**: http://localhost:3000
- **Admin Django**: http://127.0.0.1:8000/admin

---

## 📚 Documentación Adicional

- Ver `backend/API_ENDPOINTS.md` para endpoints disponibles
- Ver `README.md` en la raíz para documentación completa del proyecto
