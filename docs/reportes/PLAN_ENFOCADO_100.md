# PLAN ENFOCADO PARA 100% EN CODIGO FUENTE

## Objetivo: Completar cobertura en archivos de código productivo

### Archivos de código fuente con gaps (ordenados por impacto):

1. **clientes/models.py** - 93.45% (9 líneas)
   - Líneas: 106, 128, 171, 195, 311, 348, 353, 398, 436
   - Prob: Métodos `__str__`, `save()`, propiedades
   
2. **almuerzos/validators.py** - 95.38% (18 líneas) 
   - Líneas: 220, 503, 530, 534-539, 549, 584, 588-593, 601, 729, 796, 840, 845-846, 1080
   - Prob: Branches de validación no cubiertas
   
3. **almuerzos/models.py** - 95.28% (5 líneas)
   - Líneas: 124, 146, 173, 192, 213
   - Prob: Métodos especiales
   
4. **api_integrations/validators.py** - 98.64% (8 líneas)
   - Líneas: 161, 335, 438, 642, 715, 786, 1031, 1034
   - Prob: Casos edge de validación
   
5. **api_integrations/bancard_service.py** - 96.64% (4 líneas)
   - Líneas: 428-432
   - Prob: Manejo de errores
   
6. **clientes/validators.py** - 98.82% (3 líneas)
   - Líneas: 148, 158, 202
   - Prob: Casos edge
   
7. **common/permissions.py** - 95.56% (4 líneas)
   - Líneas: 63-64, 88-89
   
8. **almuerzos/views.py** - 98.04% (1 línea)
   - Línea: 112
   
9. **api_integrations/views.py** - 95.45% (2 líneas)
   - Líneas: 104-106

**TOTAL: ~54 líneas en código fuente productivo**

### Estrategia:

**FASE 1:** Completar models.py (14 líneas total)
- clientes/models.py: Agregar tests para métodos `__str__`, `clean()`, `save()` 
- almuerzos/models.py: Idem

**FASE 2:** Completar validators.py (29 líneas total)
- almuerzos/validators.py: Casos edge de validaciones
- api_integrations/validators.py: Casos edge
- clientes/validators.py: Casos edge

**FASE 3:** Completar services y views (7 líneas total)
- bancard_service.py: Tests de manejo de errores
- almuerzos/views.py: Branch faltante
- api_integrations/views.py: Branches faltantes

**FASE 4:** Completar permissions (4 líneas)
- common/permissions.py: Tests de permisos

**Tiempo estimado: 2-3 horas para CODIGO FUENTE al 100%**

Una vez completado esto, el código productivo estará al 100%.
El resto del gap (1,046 líneas) está en archivos de TESTS, que es menos crítico.
