# Política de deprecación de API — Cantina Tita

## Esquema de versiones

La API usa versionado por ruta URL:

```
/api/v1/   ← versión actual (estable)
/api/v2/   ← próxima versión mayor (cuando exista)
```

Los tokens JWT (`/api/token/`) y los health checks (`/api/health/`) no llevan
prefijo de versión porque son invariantes entre versiones.

---

## Ciclo de vida de un endpoint

```
Estable → Deprecado → Eliminado
            ↑
       mínimo 6 meses de aviso
```

1. **Estable** — en producción, sin restricciones.
2. **Deprecado** — funciona pero está marcado para eliminación.
   Todas las respuestas incluyen dos headers extra:
   ```
   Deprecation: true
   Sunset: Sat, 01 Jan 2027 00:00:00 GMT
   ```
3. **Eliminado** — el endpoint devuelve `HTTP 410 Gone`.

---

## Cómo deprecar un endpoint

### Paso 1 — Registrar en el middleware

Editar `backend/common/middleware.py`, clase `APIVersionHeaderMiddleware`:

```python
_DEPRECATED_PREFIXES: dict[str, str] = {
    "/api/v1/old-endpoint/": "Sat, 01 Jan 2027 00:00:00 GMT",
}
```

El middleware inyecta automáticamente los headers `Deprecation` y `Sunset`
en todas las respuestas de esa ruta.

### Paso 2 — Documentar en el changelog

Añadir entrada en `CHANGELOG.md`:

```markdown
## [Deprecado] 2026-06-22

### /api/v1/old-endpoint/
- **Motivo:** Reemplazado por /api/v2/new-endpoint/ con paginación mejorada.
- **Sunset:** 2027-01-01
- **Migración:** Ver docs/migrations/v1-v2-old-endpoint.md
```

### Paso 3 — Notificar a clientes internos

Los únicos clientes de esta API son el frontend React y los scripts de
integración Bancard. Actualizar ambos antes del sunset:

- Frontend: `grep -r "old-endpoint" frontend/src/`
- Scripts: `grep -r "old-endpoint" scripts/`

### Paso 4 — Eliminar al llegar el sunset

Reemplazar el handler con una respuesta `410 Gone`:

```python
# Después del sunset, mantener la ruta pero devolver 410
@api_view(["GET", "POST"])
@permission_classes([])
def old_endpoint_gone(request):
    return Response(
        {"detail": "Este endpoint fue eliminado el 2027-01-01. Usar /api/v2/new-endpoint/."},
        status=status.HTTP_410_GONE,
    )
```

Mantener el 410 durante **3 meses adicionales** antes de eliminar la ruta
completamente, para detectar clientes rezagados.

---

## Reglas de compatibilidad

| Cambio | ¿Requiere nueva versión? |
|--------|--------------------------|
| Agregar campo opcional a respuesta | No — retrocompatible |
| Agregar endpoint nuevo | No — retrocompatible |
| Renombrar/eliminar campo | Sí — deprecar primero |
| Cambiar semántica de campo existente | Sí — deprecar primero |
| Cambiar código de status HTTP | Sí — deprecar primero |
| Cambiar formato de paginación | Sí — deprecar primero |

---

## Headers de versión en cada respuesta

`APIVersionHeaderMiddleware` (en `common/middleware.py`) añade:

```
X-API-Version: 1.0.0
```

a todas las respuestas bajo `/api/`. Esto permite que los clientes detecten
la versión en tiempo de ejecución sin parsear la URL.

---

## Estado actual (junio 2026)

| Versión | Estado | Sunset |
|---------|--------|--------|
| `/api/v1/` | Estable | Sin fecha |

No hay endpoints deprecados actualmente.
