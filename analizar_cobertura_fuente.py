"""
Analizar cobertura solo de archivos de código fuente (sin tests)
"""

with open('branch_cov.txt', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Buscar líneas de cobertura
codigo_fuente = []
codigo_tests = []

lines = content.split('\n')
for line in lines:
    # Buscar líneas que tienen apps\ y métricas numéricas
    if 'apps\\' in line and '%' in line:
        parts = line.split()
        if len(parts) >= 5:
            archivo = parts[0]
            
            # Filtrar solo líneas con métricas
            try:
                # Buscar columnas numéricas
                for i, part in enumerate(parts[1:], 1):
                    if part.isdigit():
                        stmts = int(parts[i])
                        miss = int(parts[i+1])
                        break
                else:
                    continue
                
                # Separar código fuente de tests
                if 'test' in archivo.lower():
                    codigo_tests.append((archivo, stmts, miss))
                else:
                    # Código fuente
                    codigo_fuente.append((archivo, stmts, miss))
            except:
                pass

# Calcular estadísticas
total_lineas_fuente = sum(stmts for _, stmts, _ in codigo_fuente)
total_miss_fuente = sum(miss for _, _, miss in codigo_fuente)
cob_fuente = ((total_lineas_fuente - total_miss_fuente) / total_lineas_fuente * 100) if total_lineas_fuente > 0 else 0

total_lineas_tests = sum(stmts for _, stmts, _ in codigo_tests)
total_miss_tests = sum(miss for _, _, miss in codigo_tests)
cob_tests = ((total_lineas_tests - total_miss_tests) / total_lineas_tests * 100) if total_lineas_tests > 0 else 0

print("="*80)
print("ANALISIS DE COBERTURA - CODIGO FUENTE VS TESTS")
print("="*80)

print(f"\nCODIGO FUENTE (models.py, views.py, services.py, etc.):")
print(f"  Total líneas:      {total_lineas_fuente:,}")
print(f"  Líneas sin cubrir: {total_miss_fuente:,}")
print(f"  Cobertura:         {cob_fuente:.2f}%")

print(f"\nARCHIVOS DE TESTS:")
print(f"  Total líneas:      {total_lineas_tests:,}")
print(f"  Líneas sin cubrir: {total_miss_tests:,}")
print(f"  Cobertura:         {cob_tests:.2f}%")

# Encontrar archivos de código fuente con menor cobertura
fuente_con_gaps = []
for archivo, stmts, miss in codigo_fuente:
    if miss > 0:
        cob = ((stmts - miss) / stmts * 100) if stmts > 0 else 0
        fuente_con_gaps.append((archivo, stmts, miss, cob))

# Ordenar por cobertura (menor primero)
fuente_con_gaps.sort(key=lambda x: x[3])

print(f"\n{'='*80}")
print("TOP 20 ARCHIVOS DE CODIGO FUENTE CON MENOR COBERTURA")
print("="*80)
print(f"{'Archivo':<50} {'Líneas':>8} {'Miss':>6} {'Cob%':>7}")
print("-"*80)

for i, (archivo, stmts, miss, cob) in enumerate(fuente_con_gaps[:20], 1):
    # Simplificar nombre
    nombre = archivo.split('apps\\')[-1] if 'apps\\' in archivo else archivo
    print(f"{i:2}. {nombre:<47} {stmts:8} {miss:6} {cob:6.1f}%")

print("\n" + "="*80)
print("RESUMEN")
print("="*80)
print(f"""
Para alcanzar 100% en CODIGO FUENTE:
  - Necesitamos cubrir {total_miss_fuente} líneas adicionales
  - Actualmente en {cob_fuente:.2f}%
  - Objetivo: 100%
  - Gap: {100 - cob_fuente:.2f}%

Los archivos de tests tienen {cob_tests:.2f}% de cobertura,
pero eso es menos crítico (los tests prueban tests).
""")

print("="*80)
