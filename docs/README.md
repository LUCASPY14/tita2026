# Documentation Index - Cantina Tita

## 📚 Available Documentation

### Development & Configuration
- **[VSCODE_CONFIGURATION.md](VSCODE_CONFIGURATION.md)** - Complete VS Code setup and diagnostic handling guide
- **[QUICK_FIX_GUIDE.md](QUICK_FIX_GUIDE.md)** - Fast solutions for common VS Code warnings

### Sprint Deliverables
- **[../SPRINT5_COMPLETION_REPORT.md](../SPRINT5_COMPLETION_REPORT.md)** - Sprint 5 CI/CD and Performance Testing completion report

### Testing & Performance
- **Backend Tests**: `backend/tests/`
  - API Performance Tests: `backend/tests/api/test_api_performance.py`
  - Critical Performance Tests: `backend/tests/api/test_critical_performance.py`
  - Database Performance: `backend/tests/database/test_database_performance.py`

- **Performance Testing**: `performance_tests/`
  - API Performance: `performance_tests/api_performance.py`
  - Database Performance: `performance_tests/database_performance.py`
  - Test Runner: `performance_tests/run_performance_tests.py`

### CI/CD & Infrastructure
- **GitHub Actions**: `.github/workflows/advanced-ci-cd.yml`
- **Docker Configuration**: `docker/`
- **Coverage Configuration**: `backend/.coveragerc`
- **Pytest Configuration**: `backend/pytest.ini`

## 🚀 Quick Start

### For Developers
1. Read [QUICK_FIX_GUIDE.md](QUICK_FIX_GUIDE.md) for common VS Code issues
2. Check [VSCODE_CONFIGURATION.md](VSCODE_CONFIGURATION.md) for detailed setup

### For DevOps/CI/CD
1. Review [Sprint 5 Report](../SPRINT5_COMPLETION_REPORT.md) for complete infrastructure overview
2. Configure GitHub repository secrets (see VSCODE_CONFIGURATION.md → Optional Secrets)
3. Set up environments in GitHub repository settings

### For QA/Testing
1. Run performance tests: `cd backend && pytest tests/api/test_api_performance.py -v`
2. Run load tests: `cd performance_tests && python run_performance_tests.py`
3. View coverage reports: `backend/htmlcov/index.html`

## 📋 Document Purpose Summary

| Document | Purpose | Audience |
|----------|---------|----------|
| VSCODE_CONFIGURATION.md | Complete VS Code setup guide with troubleshooting | All developers |
| QUICK_FIX_GUIDE.md | Fast reference for common warnings | All developers |
| SPRINT5_COMPLETION_REPORT.md | Sprint 5 deliverables and status | Project managers, DevOps |

## 🔗 External Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Coverage.py Docs](https://coverage.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Locust Documentation](https://docs.locust.io/)

## 📝 Notes

- All paths in documentation are relative to workspace root (`cantina_tita/`)
- PowerShell commands assume Windows environment
- Configuration files use absolute paths where possible for reliability

---
**Project**: Cantina Tita Management System  
**Last Updated**: March 6, 2026  
**Sprint**: 5 - CI/CD Integration & Performance Testing
