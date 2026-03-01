"""
Script para corregir default=1 y default=0 en BooleanField a default=True y default=False
"""
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(BASE_DIR, 'apps')

def fix_boolean_defaults(content):
    """Corrige default=1 a default=True y default=0 a default=False en BooleanField"""
    # Reemplazar default=1 con default=True
    content = re.sub(
        r'(models\.BooleanField\([^)]*?)default=1([^)]*?\))',
        r'\1default=True\2',
        content
    )
    
    # Reemplazar default=0 con default=False
    content = re.sub(
        r'(models\.BooleanField\([^)]*?)default=0([^)]*?\))',
        r'\1default=False\2',
        content
    )
    
    return content

def process_file(filepath):
    """Procesa un archivo models.py"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = fix_boolean_defaults(content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    print("=" * 70)
    print("🔧 CORRIGIENDO VALORES DEFAULT DE BOOLEANFIELD")
    print("=" * 70)
    
    apps = os.listdir(APPS_DIR)
    total_fixed = 0
    
    for app in apps:
        app_path = os.path.join(APPS_DIR, app)
        models_path = os.path.join(app_path, 'models.py')
        
        if os.path.exists(models_path):
            if process_file(models_path):
                print(f"✅ {app}/models.py - Corregido")
                total_fixed += 1
            else:
                print(f"ℹ️  {app}/models.py - Sin cambios")
    
    print("=" * 70)
    print(f"Total de archivos corregidos: {total_fixed}")
    print("=" * 70)

if __name__ == '__main__':
    main()
