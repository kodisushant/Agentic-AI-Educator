.PHONY: dev test contracts clean

dev:
	@echo "Starting backend in MOCK_MODE..."
	MOCK_MODE=true python -m uvicorn backend.agent.main:app --host 0.0.0.0 --port 8000 --reload

test:
	python backend/agent/test_agent.py

contracts:
	python backend/agent/export_contracts.py
