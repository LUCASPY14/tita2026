# 🪝 Pre-commit Hooks - Guía de Uso

Sistema de validación automática de código antes de cada commit.

## 🚀 Instalación

### 1. Instalar pre-commit

```bash
# Usando pip
pip install pre-commit

# O con pipx (recomendado)
pipx install pre-commit
```

### 2. Instalar los hooks en el repositorio

```bash
cd d:\tita2026
pre-commit install
pre-commit install --hook-type commit-msg
```

✅ **Listo!** Los hooks se ejecutarán automáticamente en cada `git commit`

## 🎯 ¿Qué Verifican los Hooks?

### 📋 Verificaciones Generales
- ✂️ Elimina espacios en blanco al final de líneas
- 📝 Asegura que archivos terminen con nueva línea
- ⚠️ Detecta claves privadas accidentalmente commiteadas
- 🔀 Detecta conflictos de merge sin resolver
- 📏 Previene archivos muy grandes (>1MB)
- ✅ Valida sintaxis de YAML y JSON

### 🐍 Python

#### Black (Formatting)
- Formatea código automáticamente
- Línea máxima: 120 caracteres
- Estilo consistente

#### isort (Import Sorting)
- Organiza imports alfabéticamente
- Agrupa por tipo (stdlib, terceros, locales)

#### Flake8 (Linting)
- Detecta errores de sintaxis
- Verifica PEP 8
- Complejidad ciclomática máxima: 15

#### Bandit (Security)
- Escanea vulnerabilidades de seguridad
- Detecta uso inseguro de funciones

#### Django Check
- Valida configuración de Django
- Solo en `git push` (no en commit)

### ⚛️ JavaScript/TypeScript

#### ESLint
- Detecta errores de código
- Aplica reglas de estilo
- Auto-fix cuando es posible

#### Prettier
- Formatea código JS/TS/JSON/CSS
- Estilo consistente

### 📝 Mensajes de Commit

#### Commitizen
- Valida formato de mensajes de commit
- Ejemplo: `feat: agregar validación de email`

## 🏃 Uso

### Commit Normal

```bash
git add .
git commit -m "feat: nueva funcionalidad"
```

Los hooks se ejecutan automáticamente. Si hay errores:
- ❌ Commit bloqueado
- 🔧 Archivos modificados automáticamente (si es posible)
- 📋 Lista de errores a corregir manualmente

### Ejecutar Manualmente

```bash
# Todos los archivos
pre-commit run --all-files

# Solo archivos staged
pre-commit run

# Hook específico
pre-commit run black --all-files
pre-commit run flake8 --all-files
```

### Saltar Hooks (No Recomendado)

```bash
git commit -m "mensaje" --no-verify
```

⚠️ **Advertencia:** Solo usar en emergencias

## 🔧 Actualizar Hooks

```bash
# Actualizar a últimas versiones
pre-commit autoupdate

# Reinstalar hooks
pre-commit install --install-hooks --overwrite
```

## 📊 Ejemplo de Ejecución

```
$ git commit -m "feat: nueva funcionalidad"

Trim Trailing Whitespace.................................................Passed
Fix End of Files.........................................................Passed
Check Yaml...............................................................Passed
Check JSON...............................................................Passed
Check for added large files..............................................Passed
Check for merge conflicts................................................Passed
Detect Private Key.......................................................Passed
Mixed line ending........................................................Passed
Format Python code with Black............................................Passed
Sort Python imports with isort...........................................Passed
Lint Python with Flake8..................................................Failed
- hook id: flake8
- exit code: 1

backend/apps/ventas/views.py:42:80: E501 line too long (130 > 120 characters)

# Corregir el error y volver a intentar
```

## 🎨 Formateo Automático

Algunos hooks modifican archivos automáticamente:
- **Black:** Formatea Python
- **isort:** Ordena imports
- **Prettier:** Formatea JS/TS/CSS

Si un archivo es modificado:
1. El commit se detiene
2. Revisa los cambios con `git diff`
3. Vuelve a hacer `git add` si estás de acuerdo
4. Intenta el commit nuevamente

## 🚫 Archivos Excluidos

Los hooks NO se ejecutan en:
- `migrations/` - Migraciones de Django
- `node_modules/` - Dependencias Node
- `.venv/`, `venv/` - Entornos virtuales
- `__pycache__/` - Bytecode Python
- `temp_logs/`, `logs/` - Logs
- `*.txt`, `*.log` - Archivos de texto/logs
- `build/`, `dist/` - Builds

## 🔍 Configuración

### Python
- **Black:** `.pre-commit-config.yaml` y `pyproject.toml`
- **Flake8:** `backend/.flake8`
- **isort:** `pyproject.toml`

### JavaScript
- **ESLint:** `frontend/.eslintrc.js`
- **Prettier:** `frontend/.prettierrc`

## 💡 Tips

### 1. Commit Parcial
```bash
# Stagear solo algunos cambios
git add -p archivo.py
git commit -m "fix: corregir bug"
```

### 2. Ver Qué Se Ejecutará
```bash
pre-commit run --all-files --verbose
```

### 3. Deshabilitar Hook Específico
Editar `.pre-commit-config.yaml` y comentar el hook

### 4. CI/CD Integration
Los mismos checks se ejecutan en GitHub Actions, por lo que:
- ✅ Si pasa localmente, pasará en CI
- ❌ Si falla en CI, ejecuta `pre-commit run --all-files` localmente

## 🆘 Problemas Comunes

### "command not found: pre-commit"
```bash
pip install pre-commit
pre-commit install
```

### Hooks no se ejecutan
```bash
pre-commit uninstall
pre-commit install
```

### "This hook has been modified"
```bash
pre-commit clean
pre-commit install --install-hooks --overwrite
```

### Error en Django check
Solo se ejecuta en push, no en commit. Asegúrate de tener las variables de entorno configuradas.

## 📚 Recursos

- [Pre-commit Documentation](https://pre-commit.com/)
- [Black](https://black.readthedocs.io/)
- [Flake8](https://flake8.pycqa.org/)
- [ESLint](https://eslint.org/)
- [Prettier](https://prettier.io/)
