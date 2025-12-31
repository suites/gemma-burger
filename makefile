.PHONY: start start-dev stop clean install start-app-server start-model-server start-app-server-dev start-model-server-dev

# 모든 서버를 개발 모드로 시작 (병렬 실행)
start:
	@echo "🚀 Starting all servers..."
	@make -j2 start-app-server start-model-server

# 개발 모드로 시작
start-dev:
	@echo "🚀 Starting all servers in dev mode..."
	@make -j2 start-app-server-dev start-model-server-dev

# App Server 시작
start-app-server:
	@echo "📦 Starting App Server..."
	@cd app-server && pnpm start

# App Server 개발 모드
start-app-server-dev:
	@echo "📦 Starting App Server (dev mode)..."
	@cd app-server && pnpm start:dev

# Model Server 시작
start-model-server:
	@echo "🐍 Starting Model Server..."
	@cd model-server && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Model Server 개발 모드 (reload)
start-model-server-dev:
	@echo "🐍 Starting Model Server (dev mode)..."
	@cd model-server && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 의존성 설치
install:
	@echo "📥 Installing dependencies..."
	@cd app-server && pnpm install
	@cd model-server && poetry install

# 정리
clean:
	@echo "🧹 Cleaning..."
	@cd app-server && rm -rf dist node_modules
	@cd model-server && poetry env remove --all || true