# Test script for AI service agents
# Make sure Docker Desktop is running and containers are up:
# docker-compose -f docker-compose.test.yml up -d

Write-Host "Waiting for services to be ready..."
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "=== Testing Health Endpoint ==="
curl -s http://localhost:8000/healthz | ConvertFrom-Json | ConvertTo-Json

Write-Host ""
Write-Host "=== Testing Agents List ==="
curl -s http://localhost:8000/v1/agents | ConvertFrom-Json | ConvertTo-Json

Write-Host ""
Write-Host "=== Testing Economist Agent with OpenAI ==="
$body = @{
    agent = "economist"
    input = "What are the key factors affecting inflation?"
    provider = "openai"
} | ConvertTo-Json
curl -s -X POST http://localhost:8000/v1/chat -H "Content-Type: application/json" -d $body | ConvertFrom-Json | ConvertTo-Json

Write-Host ""
Write-Host "=== Testing Strategist Agent with OpenAI ==="
$body = @{
    agent = "strategist"
    input = "How should a company approach market expansion?"
    provider = "openai"
} | ConvertTo-Json
curl -s -X POST http://localhost:8000/v1/chat -H "Content-Type: application/json" -d $body | ConvertFrom-Json | ConvertTo-Json

Write-Host ""
Write-Host "=== Testing Entrepreneur Agent with OpenAI ==="
$body = @{
    agent = "entrepreneur"
    input = "What are the most important things to consider when starting a business?"
    provider = "openai"
} | ConvertTo-Json
curl -s -X POST http://localhost:8000/v1/chat -H "Content-Type: application/json" -d $body | ConvertFrom-Json | ConvertTo-Json

Write-Host ""
Write-Host "=== Testing Startup Agent with OpenAI ==="
$body = @{
    agent = "startup"
    input = "How do I validate my startup idea?"
    provider = "openai"
} | ConvertTo-Json
curl -s -X POST http://localhost:8000/v1/chat -H "Content-Type: application/json" -d $body | ConvertFrom-Json | ConvertTo-Json

Write-Host ""
Write-Host "=== Testing Auto Agent Selection with OpenAI ==="
$body = @{
    agent = "auto"
    input = "What is the best pricing strategy for a SaaS product?"
    provider = "openai"
} | ConvertTo-Json
curl -s -X POST http://localhost:8000/v1/chat -H "Content-Type: application/json" -d $body | ConvertFrom-Json | ConvertTo-Json

Write-Host ""
Write-Host "=== All tests completed ==="

