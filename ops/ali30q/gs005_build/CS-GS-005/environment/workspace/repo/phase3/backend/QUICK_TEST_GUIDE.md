# Quick Test Guide

Fast reference for running tests in Nautilus Phase 3 Backend.

---

## Quick Commands

### Fastest Validation (2 min)
```bash
python tests/run_smoke_test.py
```

### Core Tests (5-10 min)
```bash
python tests/run_quick_test.py
```

### Full Suite (15-20 min)
```bash
python tests/run_test_suite.py
```

### Coverage Analysis (45-60 min)
```bash
pytest tests/ --cov=. --cov-report=html --tb=short
```

---

## Using Test Scripts

### Linux/Mac
```bash
# Quick tests
bash tests/TEST_EXECUTION_SCRIPT.sh quick

# Full suite
bash tests/TEST_EXECUTION_SCRIPT.sh full

# Coverage
bash tests/TEST_EXECUTION_SCRIPT.sh coverage
```

### Windows
```cmd
REM Quick tests
tests\TEST_EXECUTION_SCRIPT.bat quick

REM Full suite
tests\TEST_EXECUTION_SCRIPT.bat full

REM Coverage
tests\TEST_EXECUTION_SCRIPT.bat coverage
```

---

## Specific Test Categories

### Blockchain Tests
```bash
# Linux/Mac
bash tests/TEST_EXECUTION_SCRIPT.sh blockchain

# Windows
tests\TEST_EXECUTION_SCRIPT.bat blockchain
```

### Week 4 Integration
```bash
# Linux/Mac
bash tests/TEST_EXECUTION_SCRIPT.sh week4

# Windows
tests\TEST_EXECUTION_SCRIPT.bat week4
```

### Week 5 EvoMap
```bash
# Linux/Mac
bash tests/TEST_EXECUTION_SCRIPT.sh evomap

# Windows
tests\TEST_EXECUTION_SCRIPT.bat evomap
```

### Performance Tests
```bash
# Linux/Mac
bash tests/TEST_EXECUTION_SCRIPT.sh performance

# Windows
tests\TEST_EXECUTION_SCRIPT.bat performance
```

### Security Tests
```bash
# Linux/Mac
bash tests/TEST_EXECUTION_SCRIPT.sh security

# Windows
tests\TEST_EXECUTION_SCRIPT.bat security
```

---

## Manual pytest Commands

### Run Specific Test File
```bash
pytest tests/test_api_integration.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_api_integration.py::TestHealthEndpoints -v
```

### Run Specific Test Function
```bash
pytest tests/test_api_integration.py::TestHealthEndpoints::test_health_check -v
```

### Run with Coverage
```bash
pytest tests/test_api_integration.py --cov=api --cov-report=html
```

### Stop on First Failure
```bash
pytest tests/ -x
```

### Show Print Statements
```bash
pytest tests/ -s
```

### Verbose Output
```bash
pytest tests/ -vv
```

---

## Test Markers

### Run Only Fast Tests
```bash
pytest tests/ -m "not slow"
```

### Run Only Blockchain Tests
```bash
pytest tests/ -m blockchain
```

### Run Mock Tests (No Real Blockchain)
```bash
pytest tests/ -m mock
```

---

## Coverage Reports

### Generate HTML Report
```bash
pytest tests/ --cov=. --cov-report=html
# Open: htmlcov/index.html
```

### Terminal Report
```bash
pytest tests/ --cov=. --cov-report=term-missing
```

### JSON Report
```bash
pytest tests/ --cov=. --cov-report=json
# Output: coverage.json
```

---

## Troubleshooting

### Tests Hanging
```bash
# Use timeout
pytest tests/ --timeout=300
```

### Import Errors
```bash
# Ensure you're in backend directory
cd backend
python -m pytest tests/
```

### Database Errors
```bash
# Check environment variables
echo $DATABASE_URL
echo $TESTING
```

### Clear Cache
```bash
# Remove pytest cache
rm -rf .pytest_cache
rm -rf tests/__pycache__
```

---

## CI/CD Integration

### GitHub Actions
Tests run automatically on push/PR to main branches.

### Local Pre-commit
```bash
# Run before committing
python tests/run_quick_test.py
```

---

## Test Results

### View Last Results
```bash
# JSON results
cat tests/test_results_*.json
```

### Coverage Summary
```bash
# After running with coverage
coverage report
```

---

## Quick Reference Table

| Command | Time | Purpose |
|---------|------|---------|
| `python tests/run_smoke_test.py` | 2 min | Environment check |
| `python tests/run_quick_test.py` | 5-10 min | Core validation |
| `python tests/run_test_suite.py` | 15-20 min | Full suite |
| `pytest tests/ --cov=.` | 45-60 min | Coverage analysis |

---

**For detailed information, see**: `TEST_PREPARATION_STATUS.md`
