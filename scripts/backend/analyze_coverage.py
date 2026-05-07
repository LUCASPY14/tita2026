#!/usr/bin/env python3
"""
Análisis de cobertura de tests del backend
Identifica archivos sin tests y calcula métricas de cobertura
"""

import os
import glob
from pathlib import Path

def analyze_test_coverage():
    """Analiza cobertura de tests en el proyecto Django"""
    
    # Configurar directorios
    backend_dir = Path('.')
    apps_dir = backend_dir / 'apps'
    
    results = {
        'apps': {},
        'summary': {
            'total_apps': 0,
            'total_files': 0,
            'files_with_tests': 0,
            'files_without_tests': 0,
            'test_files': 0
        }
    }
    
    # Analizar cada app
    for app_dir in apps_dir.iterdir():
        if app_dir.is_dir() and app_dir.name != '__pycache__':
            app_name = app_dir.name
            results['apps'][app_name] = {
                'files': [],
                'test_files': [],
                'untested_files': [],
                'coverage_score': 0
            }
            
            # Buscar archivos Python (excluyendo __init__ y tests_*)
            py_files = [f for f in app_dir.glob('*.py') 
                       if not f.name.startswith('__') 
                       and not f.name.startswith('tests_')
                       and f.name != 'tests.py']
            
            # Buscar archivos de test
            test_files = [f for f in app_dir.glob('test*.py')]
            
            results['apps'][app_name]['files'] = [f.name for f in py_files]
            results['apps'][app_name]['test_files'] = [f.name for f in test_files]
            
            # Identificar archivos sin tests
            for py_file in py_files:
                base_name = py_file.stem
                has_test = any(
                    f.name == f'tests_{base_name}.py' or 
                    f.name == f'test_{base_name}.py' or
                    f.name == 'tests.py'
                    for f in test_files
                )
                
                if not has_test:
                    results['apps'][app_name]['untested_files'].append(base_name)
            
            # Calcular score de cobertura
            total_files = len(py_files)
            untested_files = len(results['apps'][app_name]['untested_files'])
            if total_files > 0:
                coverage = ((total_files - untested_files) / total_files) * 100
                results['apps'][app_name]['coverage_score'] = round(coverage, 1)
            
            # Actualizar summary
            results['summary']['total_files'] += total_files
            results['summary']['files_without_tests'] += untested_files
            results['summary']['test_files'] += len(test_files)
    
    results['summary']['total_apps'] = len(results['apps'])
    results['summary']['files_with_tests'] = (
        results['summary']['total_files'] - results['summary']['files_without_tests']
    )
    
    # Calcular cobertura general
    if results['summary']['total_files'] > 0:
        overall_coverage = (results['summary']['files_with_tests'] / 
                          results['summary']['total_files']) * 100
        results['summary']['overall_coverage'] = round(overall_coverage, 1)
    
    return results

def print_coverage_report(results):
    """Imprime reporte de cobertura formateado"""
    
    print("=" * 60)
    print("📊 REPORTE DE COBERTURA DE TESTS - CANTINA TITA")
    print("=" * 60)
    
    # Summary
    summary = results['summary']
    print(f"\\n🎯 RESUMEN GENERAL:")
    print(f"   Apps analizadas: {summary['total_apps']}")
    print(f"   Archivos Python: {summary['total_files']}")
    print(f"   Archivos con tests: {summary['files_with_tests']}")
    print(f"   Archivos sin tests: {summary['files_without_tests']}")
    print(f"   Archivos de test: {summary['test_files']}")
    print(f"   Cobertura general: {summary.get('overall_coverage', 0):.1f}%")
    
    print(f"\\n📋 DETALLE POR APLICACIÓN:")
    print("-" * 60)
    
    # Ordenar apps por cobertura (peor primero)
    sorted_apps = sorted(results['apps'].items(), 
                        key=lambda x: x[1]['coverage_score'])
    
    for app_name, app_data in sorted_apps:
        coverage = app_data['coverage_score']
        status = "🔴" if coverage < 50 else "🟡" if coverage < 80 else "🟢"
        
        print(f"{status} {app_name.upper()}: {coverage}% cobertura")
        print(f"   Archivos: {len(app_data['files'])}")
        print(f"   Tests: {len(app_data['test_files'])}")
        
        if app_data['untested_files']:
            print(f"   ⚠️  Sin tests: {', '.join(app_data['untested_files'])}")
        print()
    
    print("=" * 60)
    print("🎯 PRIORITY TARGETS PARA 100% COBERTURA:")
    print("=" * 60)
    
    # Identificar prioridades
    high_priority = []
    medium_priority = []
    
    for app_name, app_data in results['apps'].items():
        if app_data['coverage_score'] < 50:
            high_priority.append((app_name, app_data))
        elif app_data['coverage_score'] < 90:
            medium_priority.append((app_name, app_data))
    
    print("\\n🔥 ALTA PRIORIDAD (< 50% cobertura):")
    for app_name, app_data in high_priority:
        print(f"   • {app_name}: {app_data['untested_files']}")
    
    print("\\n⚡ MEDIA PRIORIDAD (50-90% cobertura):")
    for app_name, app_data in medium_priority:
        print(f"   • {app_name}: {app_data['untested_files']}")

if __name__ == "__main__":
    results = analyze_test_coverage()
    print_coverage_report(results)