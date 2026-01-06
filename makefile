.PHONY: start start-dev stop clean install start-app-server start-model-server start-app-server-dev start-frontend-dev start-model-server-dev build-frontend build-backend

# 모든 서버를 개발 모드로 시작 (병렬 실행)
start: build-frontend build-backend
	@echo "🚀 Starting all servers..."
	@make -j2 start-app-server start-model-server

# 개발 모드로 시작 (프론트엔드 + 백엔드 + AI 서버)
start-dev:
	@echo "🚀 Starting all servers in dev mode..."
	@make -j3 start-frontend-dev start-app-server-dev start-model-server-dev

# App Server 시작 (프로덕션)
start-app-server: build-frontend build-backend
	@echo "📦 Starting App Server..."
	@cd app-server/backend && pnpm start

# App Server 개발 모드 (Backend + Frontend 동시 실행)
start-app-server-dev:
	@echo "📦 Starting App Server (dev mode)..."
	@make -j2 start-frontend-dev start-backend-dev

# Backend 개발 모드
start-backend-dev:
	@echo "🔧 Starting Backend (dev mode)..."
	@cd app-server/backend && pnpm start:dev

# Frontend 개발 모드
start-frontend-dev:
	@echo "🎨 Starting Frontend (dev mode)..."
	@cd app-server/frontend && pnpm run dev

# Model Server 시작
start-model-server:
	@echo "🐍 Starting Model Server..."
	@cd model-server && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Model Server 개발 모드 (reload)
start-model-server-dev:
	@echo "🐍 Starting Model Server (dev mode)..."
	@cd model-server && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend 빌드
build-frontend:
	@echo "🎨 Building Frontend..."
	@cd app-server/frontend && pnpm build

# Backend 빌드
build-backend:
	@echo "🔧 Building Backend..."
	@cd app-server/backend && pnpm run build

# 의존성 설치
install:
	@echo "📥 Installing dependencies..."
	@cd app-server/backend && pnpm install
	@cd app-server/frontend && pnpm install
	@cd model-server && poetry install

# 정리
clean:
	@echo "🧹 Cleaning..."
	@cd app-server/backend && rm -rf dist node_modules
	@cd app-server/frontend && rm -rf dist node_modules
	@cd model-server && poetry env remove --all || true
