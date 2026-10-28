# Nautilus Phase 3 - Automated Test Suite

## Overview

Comprehensive automated test suite for Nautilus Phase 3 Backend, covering API integration, end-to-end workflows, performance, and security testing.

## Test Coverage

### 1. API Integration Tests (`test_api_integration.py`)
- **Health Endpoints**: Root, health check, metrics
- **Agents API**: Create, read, update, get stats
- **Tasks API**: Create, read, filter by status/type
- **Rewards API**: Get rewards, agent rewards
- **Auth API**: Register, login, get current user
- **Cache Endpoints**: Stats, clear cache
- **Performance Endpoints**: Stats, database pool
- **CSRF Protection**: Token generation

**Coverage**: All major API endpoints

### 2. End-to-End Workflow Tests (`test_e2e_workflow.py`)
- **Complete Task Workflow**: Register → Create agent → Create task → Accept → Complete
- **Multi-Agent Workflow**: Multiple agents competing for tasks
- **Error Handling**: Unauthorized operations, invalid operations
- **Reputation System**: Reputation updates on task completion
- **Concurrent Operations**: Concurrent task creation

**Coverage**: Complete user journeys

### 3. Performance Tests (`test_performance_suite.py`)
- **Response Time**: Health check, GET tasks, GET agents, single task
- **Concurrent Requests**: 100 concurrent requests with 20 workers
- **Database Performance**: Query performance with filters, pagination
- **Cache Performance**: Cache hit rate improvement
- **Throughput**: Mixed workload throughput (20+ req/s target)

**Performance Targets**:
- Average response time: < 1s
- P95 response time: < 2s
- Success rate: ≥ 95%
- Throughput: ≥ 20 req/s

### 4. Security Tests (`test_security_suite.py`)
- **Authentication**: Valid/invalid credentials, token validation
- **Authorization**: Access control, resource ownership
- **Input Validation**: SQL injection, XSS, invalid formats
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
- **Rate Limiting**: Rate limit enforcement
- **Password Security**: Weak password rejection, no password leakage
- **CSRF Protection**: Token generation
- **Data Leakage**: Error messages, user enumeration prevention

**Coverage**: OWASP Top 10 security concerns

## Running Tests

### Quick Tests (Fast Feedback)
```bash
cd backend
python tests/run_quick_test.py
```

Runs: API Integration + E2E Workflow + Security (stops on first failure)

### Full Test Suite with Coverage
```bash
cd backend
python tests/run_test_suite.py
```

Runs all tests and generates coverage report in `htmlcov/index.html`

### Individual Test Suites
```bash
# API Integration Tests
pytest tests/test_api_integration.py -v

# E2E Workflow Tests
pytest tests/test_e2e_workflow.py -v

# Performance Tests
pytest tests/test_performance_suite.py -v

# Security Tests
pytest tests/test_security_suite.py -v
```

### With Coverage
```bash
pytest tests/test_api_integration.py tests/test_e2e_workflow.py \
  --cov=. --cov-report=html --cov-report=term-missing
```

## CI/CD Integration

### GitHub Actions
Tests run automatically on:
- Push to `master`, `main`, `develop` branches
- Pull requests to these branches

Workflow file: `.github/workflows/tests.yml`

Services:
- PostgreSQL 15
- Redis 7

### Coverage Requirements
- Minimum coverage: 80%
- Coverage reports uploaded to Codecov
- HTML report available as artifact

## Test Configuration

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --tb=short --strict-markers --disable-warnings
asyncio_mode = auto
```

### .coveragerc
```ini
[run]
source = api, models, utils, nexus_protocol, nexus_server, websocket_server
omit = tests/*, main.py

[report]
exclude_lines = pragma: no cover, def __repr__, raise NotImplementedError
```

## Test Database

Tests use in-memory SQLite database:
- Fast execution
- Isolated from production
- Automatic cleanup

Configuration:
```python
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
```

## Fixtures

### Common Fixtures
- `setup_database`: Creates test database schema
- `client`: FastAPI TestClient
- `test_user`: Creates test user
- `auth_token`: Generates JWT token
- `test_agent`: Creates test agent
- `api_key`: Generates API key

## Performance Benchmarks

### Response Time Targets
| Endpoint | Average | P95 | P99 |
|----------|---------|-----|-----|
| Health Check | < 100ms | < 200ms | < 500ms |
| GET /api/tasks | < 500ms | < 1s | < 2s |
| GET /api/agents | < 500ms | < 1s | < 2s |
| GET /api/tasks/{id} | < 200ms | < 500ms | < 1s |

### Throughput Targets
- Single endpoint: ≥ 50 req/s
- Mixed workload: ≥ 20 req/s
- Concurrent users: 20+ simultaneous

### Success Rate
- Target: ≥ 95%
- Critical endpoints: ≥ 99%

## Security Testing

### Authentication Tests
- ✅ Valid credentials accepted
- ✅ Invalid credentials rejected
- ✅ Token validation
- ✅ Protected endpoint access control

### Authorization Tests
- ✅ Resource ownership enforcement
- ✅ Cross-user access prevention
- ✅ Duplicate operation prevention

### Input Validation Tests
- ✅ SQL injection prevention
- ✅ XSS prevention
- ✅ Email format validation
- ✅ Wallet address validation
- ✅ Negative value rejection
- ✅ Empty field rejection

### Security Headers
- ✅ X-Content-Type-Options: nosniff
- ✅ X-Frame-Options: DENY
- ✅ X-XSS-Protection: 1; mode=block
- ✅ CORS configuration

## Troubleshooting

### Tests Failing
1. Check environment variables in `.env`
2. Ensure `TESTING=true` is set
3. Verify database connection
4. Check for port conflicts

### Coverage Below 80%
1. Run with `--cov-report=term-missing` to see uncovered lines
2. Add tests for uncovered code paths
3. Check `.coveragerc` for excluded files

### Performance Tests Failing
1. Check system resources (CPU, memory)
2. Close other applications
3. Run tests individually
4. Adjust performance thresholds if needed

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure tests pass: `python tests/run_quick_test.py`
3. Check coverage: `pytest --cov=. --cov-report=term-missing`
4. Run full suite: `python tests/run_test_suite.py`
5. Commit with tests

## Test Metrics

Current test suite metrics:
- **Total Tests**: 100+
- **Test Files**: 4 main suites
- **Coverage Target**: 80%+
- **Execution Time**: ~2-5 minutes (full suite)
- **Quick Tests**: ~30-60 seconds

## Future Enhancements

- [ ] Load testing with Locust
- [ ] Chaos engineering tests
- [ ] Contract testing for blockchain
- [ ] Visual regression testing
- [ ] Mutation testing
- [ ] Fuzz testing for input validation
