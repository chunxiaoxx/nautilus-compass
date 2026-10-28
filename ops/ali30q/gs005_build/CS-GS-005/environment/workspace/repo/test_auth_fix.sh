#!/bin/bash

echo "=== Testing API Authentication Fix ==="
echo ""

# 1. Login to get JWT token
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST http://43.160.239.61:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user_new_20260220","password":"password123"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
echo "Token obtained: ${TOKEN:0:50}..."
echo ""

# 2. Check if user has an agent
echo "2. Checking user's agent..."
AGENTS=$(curl -s http://43.160.239.61:8000/api/agents)
echo "Found agents: $(echo $AGENTS | grep -o '"agent_id":[0-9]*' | wc -l)"
echo ""

# 3. Try to accept a task with JWT token
echo "3. Attempting to accept task #4 with JWT token..."
ACCEPT_RESPONSE=$(curl -s -X POST http://43.160.239.61:8000/api/tasks/4/accept \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "Response: $ACCEPT_RESPONSE"
echo ""

# Check if successful
if echo "$ACCEPT_RESPONSE" | grep -q '"status":"Accepted"'; then
  echo "✅ SUCCESS: Task accepted with JWT token!"
elif echo "$ACCEPT_RESPONSE" | grep -q '"detail":"No agent found"'; then
  echo "⚠️  User needs to register an agent first"
elif echo "$ACCEPT_RESPONSE" | grep -q '"detail":"Task is not open"'; then
  echo "⚠️  Task is already accepted (expected if testing multiple times)"
else
  echo "❌ FAILED: $ACCEPT_RESPONSE"
fi

echo ""
echo "=== Test Complete ==="
