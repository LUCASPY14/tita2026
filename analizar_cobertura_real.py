"""
Análisis preciso de cobertura: código fuente vs tests
"""

import re

with open('branch_cov.txt', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

codigo_fuente = []
codigo_tests = []

# Buscar líneas que contengan .py y métricas numéricas
for line in lines:
    if 'apps\\' in line and '.py' in line and '%' in line:
        # Dividir por espacios múltiples
        parts = line.split()
        if len(parts) >= 6:
            try:
                archivo = parts[0]
                stmts = int(parts[1])
                miss = int(parts[2])
                # El porcentaje está en la posición -1 (última), quitar el %
                cov = float(parts[-1].replace('%', ''))
                
                # Separar código fuente de tests
                if 'test' in archivo.lower():
                    codigo_tests.append((archivo, stmts, miss, cov))
                else:
                    codigo_fuente.append((archivo, stmts, miss, cov))
            except (ValueError, IndexError):
                pass

# Calcular totales
total_lineas_fuente = sum(stmts for _, stmts, _, _ in codigo_fuente)
total_miss_fuente = sum(miss for _, _, miss, _ in codigo_fuente)
cob_fuente = ((total_lineas_fuente - total_miss_fuente) / total_lineas_fuente * 100) if total_lineas_fuente > 0 else 0

total_lineas_tests = sum(stmts for _, stmts, _, _ in codigo_tests)
total_miss_tests = sum(miss for _, _, miss, _ in codigo_tests)
cob_tests = ((total_lineas_tests - total_miss_tests) / total_lineas_tests * 100) if total_lineas_tests > 0 else 0

print("="*80)
print("ANALISIS DE COBERTURA - CODIGO FUENTE VS TESTS")
print("="*80)

print(f"\nCODIGO FUENTE (models.py, views.py, services.py, validators.py, etc.):")
print(f"  Archivos:          {len(codigo_fuente)}")
print(f"  Total líneas:      {total_lineas_fuente:,}")
print(f"  Líneas sin cubrir: {total_miss_fuente:,}")
print(f"  Cobertura:         {cob_fuente:.2f}%")

print(f"\nARCHIVOS DE TESTS:")
print(f"  Archivos:          {len(codigo_tests)}")
print(f"  Total líneas:      {total_lineas_tests:,}")
print(f"  Líneas sin cubrir: {total_miss_tests:,}")
print(f"  Cobertura:         {cob_tests:.2f}%")

# Encontrar archivos de código fuente con gaps
fuente_con_gaps = [(a, s, m, c) for a, s, m, c in codigo_fuente if m > 0]
fuente_con_gaps.sort(key=lambda x: x[3])  # Ordenar por cobertura

print(f"\n{'='*80}")
print(f"ARCHIVOS DE CODIGO FUENTE CON GAPS (Total: {len(fuente_con_gaps)})")
print("="*80)
print(f"{'Archivo':<60} {'Miss':>6} {'Cob%':>7}")
print("-"*80)

for i, (archivo, stmts, miss, cov) in enumerate(fuente_con_gaps, 1):
    nombre = archivo.split('apps\\')[-1] if 'apps\\' in archivo else archivo
    print(f"{i:2}. {nombre:<57} {miss:6} {cov:6.1f}%")
    if i >= 30:  # Limitar a 30
        print(f"... y {len(fuente_con_gaps) - 30} archivos más")
        break

print("\n" + "="*80)
print("RESUMEN PARA 100% EN CODIGO FUENTE")
print("="*80)

# Calcular impacto de cada archivo
gap_total = 100 - cob_fuente
print(f"""
Cobertura actual del código fuente: {cob_fuente:.2f}%
Objetivo: 100%
Gap: {gap_total:.2f}%
Líneas faltantes: {total_miss_fuente}

Top 5 archivos de mayor impacto (más líneas sin cubrir):
""")

fuente_por_impacto = sorted(fuente_con_gaps, key=lambda x: x[2], reverse=True)[:5]
for i, (archivo, stmts, miss, cov) in enumerate(fuente_por_impacto, 1):
    nombre = archivo.split('apps\\')[-1]
    impacto = (miss / total_miss_fuente * 100) if total_miss_fuente > 0 else 0
    print(f"  {i}. {nombre:45} {miss:3} líneas ({impacto:4.1f}% del gap)")

print("\n" + "="*80)
