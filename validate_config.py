"""
Script de Validación de Configuración
Verifica que el proyecto esté listo para deployment
"""
import os
import sys
from pathlib import Path

# Colores para terminal
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}{text}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

def check_item(condition, message, warning=False):
    if condition:
        print(f"{GREEN}✓{RESET} {message}")
        return True
    else:
        color = YELLOW if warning else RED
        symbol = "⚠" if warning else "✗"
        print(f"{color}{symbol}{RESET} {message}")
        return False

def check_backend_settings():
    print_header("Backend Configuration")
    
    base_path = Path(__file__).parent / 'backend'
    
    # Check .env file
    env_exists = (base_path / '.env').exists()
    check_item(env_exists, ".env file exists", warning=True)
    
    # Check settings files
    settings_path = base_path / 'backend' / 'settings'
    check_item((settings_path / 'base.py').exists(), "settings/base.py exists")
    check_item((settings_path / 'development.py').exists(), "settings/development.py exists")
    check_item((settings_path / 'production.py').exists(), "settings/production.py exists")
    check_item((settings_path / 'test.py').exists(), "settings/test.py exists")
    
    # Check for insecure SECRET_KEY in production
    if (settings_path / 'base.py').exists():
        with open(settings_path / 'base.py', 'r', encoding='utf-8') as f:
            content = f.read()
            insecure = 'django-insecure' in content
            check_item(not insecure, "SECRET_KEY is not insecure default", warning=True)
    
    # Check requirements
    requirements = base_path / 'requirements.txt'
    check_item(requirements.exists(), "requirements.txt exists")
    
    # Check tests
    tests_path = base_path / 'tests'
    integration_tests = tests_path / 'integration'
    check_item(integration_tests.exists(), "Integration tests directory exists")
    
    test_files = list(integration_tests.glob('test_*.py')) if integration_tests.exists() else []
    check_item(len(test_files) >= 3, f"At least 3 test files ({len(test_files)} found)")

def check_frontend_config():
    print_header("Frontend Configuration")
    
    frontend_path = Path(__file__).parent / 'frontend'
    
    # Check essential files
    check_item((frontend_path / 'package.json').exists(), "package.json exists")
    check_item((frontend_path / 'tsconfig.json').exists(), "tsconfig.json exists")
    check_item((frontend_path / '.env').exists(), ".env file exists", warning=True)
    
    # Check source structure
    src_path = frontend_path / 'src'
    check_item((src_path / 'services').exists(), "services/ directory exists")
    check_item((src_path / 'components').exists(), "components/ directory exists")
    check_item((src_path / 'contexts').exists(), "contexts/ directory exists")
    
    # Check tests
    tests_path = frontend_path / 'tests'
    check_item(tests_path.exists(), "tests/ directory exists")
    
    test_files = list(tests_path.glob('**/*.test.ts*')) if tests_path.exists() else []
    check_item(len(test_files) >= 5, f"At least 5 test files ({len(test_files)} found)")

def check_docker_config():
    print_header("Docker Configuration")
    
    docker_path = Path(__file__).parent / 'docker'
    
    check_item(docker_path.exists(), "docker/ directory exists")
    check_item((docker_path / 'docker-compose.yml').exists(), "docker-compose.yml exists")

def check_documentation():
    print_header("Documentation")
    
    base_path = Path(__file__).parent
    
    check_item((base_path / 'README.md').exists(), "README.md exists")
    check_item((base_path / 'VALIDATION_REPORT.md').exists(), "VALIDATION_REPORT.md exists")
    check_item((base_path / 'backend' / 'tests' / 'README.md').exists(), "Backend tests README exists")

def run_validation():
    print_header("🔍 Cantina Tita - Configuration Validation")
    
    check_backend_settings()
    check_frontend_config()
    check_docker_config()
    check_documentation()
    
    print_header("Summary")
    print(f"{GREEN}Validation complete!{RESET}")
    print(f"\n{YELLOW}Review warnings above and ensure production configs are secure.{RESET}")
    print(f"{BOLD}Next steps:{RESET}")
    print("  1. Fix any ✗ red items")
    print("  2. Review ⚠ warnings")
    print("  3. Run tests: cd backend && pytest tests/integration/")
    print("  4. Check VALIDATION_REPORT.md for detailed analysis\n")

if __name__ == '__main__':
    run_validation()
