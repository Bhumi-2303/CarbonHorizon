#!/bin/bash
TOKEN=$(curl -s -X POST https://carbonhorizon-backend-tvxxkekeuq-el.a.run.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test_coach_deploy@example.com","password":"password123","full_name":"Test User"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  TOKEN=$(curl -s -X POST https://carbonhorizon-backend-tvxxkekeuq-el.a.run.app/api/v1/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test_coach_deploy@example.com&password=password123" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
fi

echo "TOKEN=$TOKEN"
curl -s -X POST https://carbonhorizon-backend-tvxxkekeuq-el.a.run.app/api/v1/coach/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"test"}'
