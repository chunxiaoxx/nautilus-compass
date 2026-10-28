# Security Fixes Deployment Checklist

## Quick Deployment Guide for Security Fixes (Task #37)

This is a focused checklist for deploying the security fixes. For full production deployment, see `DEPLOYMENT_CHECKLIST.md`.

---

## Pre-Deployment (15 minutes)

### 1. Verify Fixes
- [x] All security fixes verified: `python verify_security_fixes.py`
- [x] 8/8 checks passed

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
- [ ] asteval>=0.9.31 installed
- [ ] eth-account>=0.10.0 installed
- [ ] All other dependencies up to date

### 3. Infrastructure Check
- [ ] Redis server running: `redis-cli ping` returns PONG
- [ ] Redis accessible from application
- [ ] Network access to api.pwnedpasswords.com verified

### 4. Environment Variables
- [ ] `REDIS_HOST` set (default: localhost)
- [ ] `REDIS_PORT` set (default: 6379)
- [ ] No new environment variables required

---

## Testing (10 minutes)

### Run Security Tests
```bash
pytest tests/test_security_fixes.py -v
```

Expected results:
- [ ] test_compute_executor_safe_evaluation PASSED
- [ ] test_compute_executor_blocks_code_injection PASSED
- [ ] test_agent_registration_rate_limit PASSED
- [ ] test_wallet_generation_uses_eth_account PASSED
- [ ] test_oauth_state_stored_in_redis PASSED
- [ ] test_oauth_callback_validates_state PASSED
- [ ] test_password_validation_checks_hibp PASSED
- [ ] test_password_validation_strong_password PASSED
- [ ] test_password_validation_requirements PASSED

### Run All Tests (Optional)
```bash
pytest tests/ -v
```
- [ ] All tests passing
- [ ] No new test failures introduced

---

## Deployment (5 minutes)

### 1. Backup
- [ ] Current code backed up
- [ ] Database backed up (if applicable)

### 2. Deploy Code
```bash
git pull origin main
pip install -r requirements.txt
```

### 3. Restart Services
```bash
# Example commands (adjust for your setup)
systemctl restart nautilus-backend
# OR
docker-compose restart backend
# OR
supervisorctl restart nautilus
```

### 4. Verify Services Started
- [ ] Application running
- [ ] No startup errors in logs
- [ ] Health check endpoint responding

---

## Post-Deployment Verification (10 minutes)

### 1. Smoke Tests

**Test 1: Code Injection Prevention**
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"expression": "__import__(\"os\").system(\"ls\")"}'
```
- [ ] Request rejected with error (not executed)

**Test 2: Rate Limiting**
```bash
# Make 4 registration requests rapidly
for i in {1..4}; do
  curl -X POST http://localhost:8000/api/agents/register \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"Test$i\",\"email\":\"test$i@example.com\"}"
done
```
- [ ] 4th request returns 429 (Too Many Requests)

**Test 3: Wallet Generation**
```bash
curl -X POST http://localhost:8000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{"name":"TestAgent","email":"test@example.com"}'
```
- [ ] Returns valid wallet address (0x + 40 hex chars)

**Test 4: OAuth State Validation**
```bash
curl http://localhost:8000/api/auth/github/callback?code=test
```
- [ ] Returns 400 error (Missing state parameter)

**Test 5: Password Breach Check**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"Password123!"}'
```
- [ ] Returns validation error (password too common)

### 2. Monitor Logs
```bash
tail -f /var/log/nautilus/backend.log
```
- [ ] No errors related to asteval
- [ ] No errors related to eth_account
- [ ] No Redis connection errors
- [ ] No HIBP API errors

### 3. Check Redis
```bash
redis-cli
> KEYS oauth_state:*
```
- [ ] OAuth states being stored
- [ ] States expire after 10 minutes

---

## Monitoring (First 24 hours)

### Metrics to Watch

1. **Rate Limiting**
   - [ ] Monitor rate limit hits
   - [ ] Alert on unusual patterns
   - [ ] Track blocked IPs

2. **OAuth Security**
   - [ ] Monitor invalid state attempts
   - [ ] Track OAuth success rate
   - [ ] Alert on CSRF attempts

3. **Password Security**
   - [ ] Log breached password attempts (count only)
   - [ ] Monitor HIBP API response times
   - [ ] Track API failures

4. **Compute Executor**
   - [ ] Monitor expression evaluation errors
   - [ ] Track suspicious patterns
   - [ ] Alert on injection attempts

5. **Wallet Generation**
   - [ ] Monitor generation rate
   - [ ] Verify uniqueness
   - [ ] Track failures

---

## Rollback Plan

If critical issues detected:

### 1. Immediate Rollback
```bash
git checkout <previous-commit>
pip install -r requirements.txt
systemctl restart nautilus-backend
```

### 2. Verify Rollback
- [ ] Application running
- [ ] Core functionality working
- [ ] No errors in logs

### 3. Document Issues
- [ ] Issue description
- [ ] Error logs captured
- [ ] Steps to reproduce
- [ ] Create bug ticket

---

## Success Criteria

Deployment is successful when:
- [x] All security fixes verified
- [ ] All tests passing
- [ ] Services running without errors
- [ ] Smoke tests passing
- [ ] No critical errors in logs (first hour)
- [ ] Rate limiting working
- [ ] OAuth state validation working
- [ ] Password breach checking working
- [ ] Code injection blocked
- [ ] Wallet generation secure

---

## Communication

### Before Deployment
- [ ] Team notified
- [ ] Deployment window scheduled
- [ ] Stakeholders informed

### After Deployment
- [ ] Deployment completed notification sent
- [ ] Summary shared with team
- [ ] Documentation links shared
- [ ] Ticket updated/closed

---

## Sign-off

**Deployed By**: ___________________
**Date**: ___________________
**Time**: ___________________
**Status**: [ ] Success [ ] Rollback Required

**Verified By**: ___________________
**Date**: ___________________

---

## Notes

```
Add deployment-specific notes here:




```

---

**Deployment Duration**: _____ minutes
**Issues Encountered**: [ ] None [ ] Minor [ ] Major
**Rollback Required**: [ ] Yes [ ] No
