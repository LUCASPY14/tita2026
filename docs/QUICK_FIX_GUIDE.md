# Quick Fix Guide - VS Code Diagnostic Warnings

## 🎯 TL;DR - Fast Solutions

### .coveragerc File Showing Python Errors?
1. **Quick Fix**: Click language indicator (bottom-right) → Select "INI"
2. **Permanent Fix**: Already configured in `.vscode/settings.json`
3. **If persists**: Reload window (Ctrl+Shift+P → "Developer: Reload Window")

### GitHub Actions Workflow Warnings?
- ✅ **Safe to ignore** - These are intentional
- Warnings indicate optional features (Cypress recording, Slack notifications)
- Workflow runs fine without them
- Add secrets in repository settings to enable features

### Performance Tests Import Errors?
1. **Check**: Python interpreter is `venv/Scripts/python.exe`
2. **Fix**: Restart Pylance (Ctrl+Shift+P → "Python: Restart Language Server")
3. **If persists**: Already configured in `pyrightconfig.json` - just reload window

## 📋 One-Command Fixes

### Reload Everything
```powershell
# In VS Code integrated terminal
# This will clear cache and restart
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force
```
Then: Ctrl+Shift+P → "Developer: Reload Window"

### Verify Configuration Loaded
```powershell
# Check if settings are applied
cat .vscode/settings.json
cat pyrightconfig.json
```

## 🔍 Understanding the Warnings

| Warning Type | Severity | Action |
|-------------|----------|--------|
| `.coveragerc` syntax errors | False positive | Ignore - it's INI, not Python |
| `environment: production` | Configuration | Comment stays until repo setup |
| `CYPRESS_RECORD_KEY` access | Info only | Optional secret - safe to ignore |
| `SLACK_WEBHOOK_URL` access | Info only | Optional secret - safe to ignore |
| Performance test imports | Info only | Runtime works - Pylance caching |

## ✅ Verification Steps

After applying fixes:

1. **Check File Type**: 
   - Open `.coveragerc`
   - Bottom-right should show "INI" (not "Python")

2. **Check Python Path**:
   - Look at bottom-left status bar
   - Should show: `Python 3.14.x ('venv')`

3. **Run Tests**: 
   ```powershell
   cd backend
   pytest tests/api/test_api_performance.py -v
   ```

4. **If All Pass**: Configuration is correct ✅

## 🚀 When to Take Action

**Ignore warnings for**:
- File type associations (INI files)
- Optional GitHub secrets
- Import warnings in `performance_tests/` (runtime works)

**Fix immediately if you see**:
- Actual test failures
- Runtime import errors
- Django configuration errors
- Database connection issues

## 📞 Need Help?

See comprehensive documentation: [docs/VSCODE_CONFIGURATION.md](VSCODE_CONFIGURATION.md)

---
**Last Updated**: March 6, 2026
**Sprint**: 5 - CI/CD & Performance Testing
