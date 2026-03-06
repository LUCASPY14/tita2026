# VS Code Configuration & Diagnostic Handling

## Overview
This document explains the VS Code workspace configuration and how to handle diagnostic warnings for the Cantina Tita project.

## Configuration Files

### `.vscode/settings.json`
Workspace-specific settings for Python development:
- **Python Analysis**: Configured to use the backend folder as extra path for imports
- **File Associations**: `.coveragerc` files are recognized as INI format (not Python)
- **Excludes**: Excludes `__pycache__`, `.coveragerc` from Python analysis
- **Testing**: Pytest configured for the backend directory
- **YAML Schema**: GitHub Actions workflow validation enabled

### `pyrightconfig.json`
Python type checking and analysis configuration:
- **Include Paths**: Backend apps, tests, and performance_tests directories
- **Extra Paths**: Backend directory added for import resolution
- **Ignore Patterns**: Configuration files like `.coveragerc` excluded from analysis
- **Type Checking**: Basic mode with sensible warning levels

## Common Diagnostic Warnings & Solutions

### 1. `.coveragerc` File - Pylance Syntax Errors

**Issue**: Pylance incorrectly treats `.coveragerc` as Python code and shows syntax errors.

**Root Cause**: `.coveragerc` is an INI-style configuration file, not Python code.

**Solutions Implemented**:
- ✅ Added file association mapping `.coveragerc` → `ini` in settings.json
- ✅ Excluded `.coveragerc` from Python analysis in pyrightconfig.json
- ✅ Added mode hints at top of .coveragerc file (`# -*- mode: conf -*-`)
- ✅ Added explicit comment: "NOT Python code - do not analyze with Pylance/Pyright"

**Expected Behavior**: These warnings should disappear after VS Code reloads the window or restarts.

### 2. GitHub Actions Workflow - Environment Not Valid

**Issue**: `environment: production` shows validation error in workflow YAML.

**Root Cause**: GitHub requires environments to be configured in repository settings before they can be referenced in workflows.

**Solution Implemented**:
- ✅ Commented out `environment: production` line
- ✅ Added explanatory comment about repository settings requirement
- ✅ Added echo message in deployment step noting environment configuration

**Action Required**: 
- Set up environment in GitHub repository settings: Settings → Environments → New environment
- Uncomment the `environment: production` line once configured

### 3. GitHub Actions - Context Access Warnings

**Issue**: Warnings for `secrets.CYPRESS_RECORD_KEY` and `secrets.SLACK_WEBHOOK_URL` context access.

**Root Cause**: GitHub Actions YAML validator warns about potentially undefined secrets.

**Solution Implemented**:
- ✅ Updated to use explicit null-check pattern: `secrets.SECRET != '' && secrets.SECRET || ''`
- ✅ Added comments marking secrets as optional
- ✅ Provides empty string fallback for missing secrets instead of 'none'

**Expected Behavior**: These are optional secrets - workflow will run without them. Add secrets in repository settings to enable features.

### 4. Performance Tests - Missing Imports

**Issue**: `apps.clientes.models`, `apps.productos.models`, etc. show as unresolved imports in `performance_tests/`.

**Root Cause**: Performance tests are outside the backend directory but need to import Django apps.

**Solution Implemented**:
- ✅ Added Django setup code in `performance_tests/database_performance.py`
- ✅ Added `backend` to sys.path dynamically
- ✅ Configured `extraPaths` in pyrightconfig.json to include backend directory
- ✅ Set `DJANGO_SETTINGS_MODULE` environment variable

**Expected Behavior**: Imports should resolve correctly. If warnings persist, restart Pylance language server.

## Reloading Configuration

After configuration changes, you may need to:

1. **Reload Window**: 
   - Command Palette (Ctrl+Shift+P)
   - Type "Developer: Reload Window"

2. **Restart Pylance**:
   - Command Palette (Ctrl+Shift+P)
   - Type "Python: Restart Language Server"

3. **Clear Python Cache**:
   ```powershell
   Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force
   Get-ChildItem -Path . -Filter "*.pyc" -Recurse -File | Remove-Item -Force
   ```

## Optional Secrets Configuration

The following secrets can be configured in GitHub repository settings for enhanced CI/CD features:

### Required for Production
- `DB_PASSWORD` - Database password for production deployment
- `SECRET_KEY` - Django secret key for production

### Optional CI/CD Enhancements
- `CYPRESS_RECORD_KEY` - Enable Cypress cloud recording and dashboard
- `SLACK_WEBHOOK_URL` - Enable Slack notifications for build status
- `DOCKER_USERNAME` - Docker Hub credentials for image publishing
- `DOCKER_PASSWORD` - Docker Hub credentials for image publishing

**Note**: Workflows will run successfully without optional secrets; features will be skipped gracefully.

## File Type Associations

The workspace is configured to recognize:
- `.coveragerc` → INI configuration file
- `.yml` in `.github/workflows/` → GitHub Actions workflow (with schema validation)
- `pytest.ini` → INI configuration file
- `setup.cfg` → INI configuration file

## Troubleshooting

### Persistent .coveragerc Errors
If Pylance still shows errors for .coveragerc:
1. Close the .coveragerc file
2. Reload VS Code window
3. Verify file shows as "INI" in bottom-right status bar (not "Python")
4. If still showing as Python, manually select language: Click language indicator → Select "INI"

### Import Resolution Issues
If imports still show as unresolved:
1. Verify virtual environment is activated
2. Check Python interpreter path in bottom-left status bar
3. Ensure it points to: `venv/Scripts/python.exe`
4. Restart Pylance language server
5. Check `pyrightconfig.json` paths are correct

### GitHub Actions Validation
If workflow validation shows errors:
1. Ensure GitHub Actions extension is installed
2. Check YAML syntax with: Command Palette → "YAML: Validate"
3. Consult GitHub Actions schema: https://json.schemastore.org/github-workflow.json

## Best Practices

1. **Don't Edit Configuration Files in Python Mode**: Always ensure .coveragerc, pytest.ini show correct file type
2. **Restart After Config Changes**: Always reload window after modifying settings.json or pyrightconfig.json
3. **Check File Associations**: Verify status bar shows correct file type for configuration files
4. **Use Explicit Paths**: Prefer absolute paths in configuration over relative paths
5. **Document Secrets**: Always document which secrets are required vs optional

## Additional Resources

- [Pylance Configuration Docs](https://github.com/microsoft/pylance-release/blob/main/TROUBLESHOOTING.md)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Coverage.py Configuration](https://coverage.readthedocs.io/en/latest/config.html)
- [Pytest Configuration](https://docs.pytest.org/en/latest/reference/customize.html)
