# Agentic Guidelines for Gemma Burger

Welcome, Agent. This repository is a hybrid AI service combining **NestJS** (Application Gateway) and **Python/FastAPI** (Local LLM Inference & RAG). This project implements an AI-powered restaurant concierge ("Gemma Burger") that handles English orders from international customers using local LLM inference.

## 1. Project Overview & Architecture
- **Hybrid Architecture**: 
  - **NestJS (Gateway)**: Handles HTTP requests, static file hosting for the React frontend, and acts as an SSE (Server-Sent Events) proxy.
  - **Python (AI Brain)**: Manages local inference using Apple MLX, orchestrates complex agent logic with LangGraph, and performs RAG (Retrieval-Augmented Generation) with Pinecone.
- **Local First**: Built specifically for Apple Silicon (Metal) acceleration. Avoid using external LLM APIs (OpenAI, etc.) for core inference.
- **Microservices**: The two servers communicate via HTTP, but the NestJS server is the primary entry point for users (port 3000).

## 2. Global Commands (Root Makefile)
The root directory contains a `makefile` to streamline development:
- `make install`: Installs dependencies for both `app-server/backend` (NestJS), `app-server/frontend` (React), and `model-server` (Python).
- `make start-dev`: Starts both servers concurrently in watch/reload mode.
- `make start-app-server-dev`: Starts only the NestJS server (dev mode).
- `make start-model-server-dev`: Starts only the FastAPI server (dev mode).
- `make build-frontend`: Builds the React frontend (Vite).
- `make build-backend`: Builds the NestJS backend.
- `make clean`: Wipes build artifacts (`dist`), dependencies (`node_modules`), and poetry environments.

---

## 3. App Server Structure (Frontend + Backend)
Located in `app-server/`. This directory contains two independent projects:

### 📂 Directory Structure
```
app-server/
├── backend/              # NestJS Backend (API Gateway)
│   ├── src/
│   │   ├── chat/        # Chat proxy logic
│   │   ├── app.module.ts
│   │   └── main.ts
│   ├── dist/            # Build output
│   ├── test/            # E2E tests
│   ├── package.json     # Backend dependencies (pnpm)
│   ├── tsconfig.json
│   └── nest-cli.json
└── frontend/            # React Frontend (Vite + TypeScript)
    ├── src/
    │   ├── App.tsx      # Main chat component
    │   └── main.tsx
    ├── dist/            # Build output (served by NestJS)
    ├── package.json     # Frontend dependencies (pnpm)
    └── vite.config.ts
```

---

## 4. Backend (TypeScript / NestJS)
Located in `app-server/backend/`. This server serves the React app and proxies AI requests.

### 🛠 Commands
**All commands must be run from `app-server/backend/` directory:**
- **Install Dependencies**: `pnpm install`
- **Production Build**: `pnpm run build`
- **Linting & Formatting**: `pnpm run lint` (ESLint) and `pnpm run format` (Prettier).
- **Start Development**: `pnpm run start:dev`
- **Run All Tests**: `pnpm run test`
- **Run Single Test**: `pnpm exec jest src/path/to/file.spec.ts`
- **E2E Tests**: `pnpm run test:e2e`

### 🎨 Code Style & Guidelines
- **Naming Conventions**:
    - **Files**: `kebab-case.extension` (e.g., `chat.controller.ts`).
    - **Classes**: `PascalCase` with role-based suffix (`ChatService`, `AppModule`, `ChatController`).
    - **Methods & Variables**: `camelCase`.
- **Imports**:
    - **Relative**: Use `./` or `../` for internal files.
    - **Absolute**: Use `@nestjs/common`, `@nestjs/core`, etc. for framework packages.
- **Type Safety**:
    - **Strictness**: `noImplicitAny: false` is set in `tsconfig.json`, but you should strive for explicit types. **Never use `any`** when a DTO or Interface can be defined.
    - **Import Types**: Use `import type { Response } from 'express'` when importing types only (required for `isolatedModules: true`).
- **Error Handling**:
    - Use NestJS built-in `HttpException` variants (e.g., `InternalServerErrorException`, `BadRequestException`).
    - Always wrap external service calls (especially to the Python server) in `try-catch` blocks and log the error before throwing.
- **Patterns**:
    - **SSE 중계**: Since the AI server streams tokens, the NestJS service must return a `Readable` stream using `Axios` with `responseType: 'stream'`. Use `rxjs`'s `lastValueFrom` to handle the observable response.
    - **Separation of Concerns**: Controllers should only handle request/response mapping. All business logic must reside in `@Injectable()` services.
    - **Static Serving**: The `frontend/dist/` directory is served at the root URL by `ServeStaticModule`.

---

## 5. Frontend (TypeScript / React)
Located in `app-server/frontend/`. This is a modern React SPA built with Vite.

### 🛠 Commands
**All commands must be run from `app-server/frontend/` directory:**
- **Install Dependencies**: `pnpm install`
- **Development Server**: `pnpm run dev` (runs on port 5173 with HMR)
- **Production Build**: `pnpm run build` (outputs to `dist/`)

### 🎨 Code Style & Guidelines
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **Naming Conventions**:
    - **Components**: `PascalCase.tsx` (e.g., `App.tsx`)
    - **Hooks**: `camelCase` with `use` prefix (e.g., `useChat`)
    - **Utilities**: `camelCase.ts`
- **State Management**: React hooks (`useState`, `useEffect`, `useRef`)
- **Styling**: CSS Modules or plain CSS (currently using `App.css`)
- **API Communication**: Fetch API with streaming support for `/chat` endpoint

### 🔗 Integration with Backend
- **Development Mode**: Vite dev server proxies `/chat` requests to `http://localhost:3000` (NestJS)
- **Production Mode**: NestJS serves the built React app from `app-server/frontend/dist/`

---

## 6. Model Server (Python / FastAPI)
Located in `model-server/`. This server runs the LLM and RAG logic.

### 🛠 Commands
- **Install Dependencies**: `poetry install`
- **Start Development**: `poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Linting**: `poetry run ruff check . --fix`
- **Formatting**: `poetry run ruff format .`
- **Data Ingestion**: `poetry run python scripts/ingest.py` (Loads `menu.json` into Pinecone).
- **Fine-tuning**: `poetry run python scripts/train_with_mlflow.py` (Orchestrates LoRA training).

### 🎨 Code Style & Guidelines
- **Coding Standards**: Follow **PEP 8** strictly. Double quotes for strings are preferred by the project's Ruff config.
- **Naming Conventions**:
    - **Files, Functions, Variables**: `snake_case`.
    - **Classes**: `PascalCase`.
    - **Constants**: `UPPER_SNAKE_CASE`.
- **Type Hinting**:
    - **Mandatory**: Every function signature must have type hints for arguments and return values.
    - **Pydantic**: Use for all request/response schemas to ensure validation at the API boundary.
    - **LangGraph State**: Use `TypedDict` and `Annotated` for state definitions (see `app/agent/state.py`).
- **Error Handling**:
    - Use `fastapi.HTTPException` for API-level responses.
    - Catch specific domain errors (e.g., `PineconeException`, `MLXError`) rather than generic `Exception`.
- **Architecture**:
    - **LangGraph**: Logic is split into `router.py` (intent classification) and `handlers.py` (intent processing).
    - **MLX Engine**: Model loading and generation logic should stay in `app/engine.py`.
    - **RAG**: Vector search logic should stay in `app/rag.py`.

### 🧩 LangGraph Component Breakdown
- **`state.py`**: Defines the `AgentState` TypedDict. Includes `messages`, `current_intent`, and `final_response`.
- **`router.py`**: Uses a lightweight chain to classify user input into intents (e.g., `order`, `menu_qa`).
- **`handlers.py`**: Individual functions for each intent. They often query Pinecone and format prompts for the LLM.
- **`graph.py`**: Compiles the nodes and edges into a state machine with persistence.

---

## 7. MLOps, Data & Resources
- **MLflow**: Tracks fine-tuning experiments. Artifacts are stored locally by default.
- **Pinecone**: Vector database for menu knowledge. Metadata filtering (e.g., `type: 'menu'`) is used in RAG.
- **Resources**:
  - `resources/menu.json`: The source of truth for restaurant data.
  - `resources/fine_tuning/`: Contains `train.jsonl` and `valid.jsonl` in Chat Template format.

### 📊 Data Ingestion Pipeline
To refresh the vector database after modifying `menu.json`:
1. Ensure `model-server/.env` has valid Pinecone credentials.
2. Run `make install` if dependencies changed.
3. Run `poetry run python scripts/ingest.py`.
4. Verify by checking the Pinecone console or using the `menu_qa` handler.

## 8. Agentic Workflow & Verification
When you work in this repository, follow these steps to ensure quality:
1. **Full-Stack Context**: Before modifying an endpoint, check both `ChatController` (NestJS) and `main.py` (FastAPI) to ensure the request/response contract is maintained.
2. **Linting Verification**:
    - After TypeScript changes (Backend): Run `pnpm run lint` in `app-server/backend/`.
    - After TypeScript changes (Frontend): Run `pnpm run lint` in `app-server/frontend/` (if linter is configured).
    - After Python changes: Run `ruff check .` in `model-server/`.
3. **LSP Check**: Run `lsp_diagnostics` on any modified files before finishing your task.
4. **Testing Policy**:
    - If logic is added to a NestJS service, add/update the corresponding `.spec.ts` file.
    - If logic is added to the Python server, verify it manually via the FastAPI docs (`/docs`) or write a `pytest` script.
5. **No Weights in Git**: Never commit `.safetensors` files or large model checkpoints. Use the `.gitignore` provided.
6. **Parallel Execution**: Use `make start-dev` to run both servers. If one fails, check the logs for port conflicts (3000 or 8000).

## 9. Development Tips for Agents
- **Local LLM Performance**: Since we use MLX on Metal, generation might be slower than cloud APIs. Do not reduce timeouts in the NestJS `HttpService` without reason.
- **RAG Debugging**: If the model gives incorrect menu info, check `app/rag.py` and ensure the query is being embedded correctly.
- **State Persistence**: LangGraph uses a `MemorySaver`. Ensure the `thread_id` (session_id) is passed consistently from the frontend to maintain conversation context.
- **Prompt Engineering**: System prompts are located in `resources/prompts.yaml` or defined within the handlers. Modify these with care as they affect the fine-tuned persona.
- **Frontend Development**: Use `pnpm run dev` in `app-server/frontend/` for hot-reload during development. The Vite dev server will proxy API requests to the NestJS backend.

## 10. Troubleshooting for Agents
- **Pinecone Issues**: Ensure `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` are correctly set in `model-server/.env`. If index creation fails, verify your Pinecone region settings.
- **MLX Memory**: If inference fails with a "Device out of memory" error, check if another process is hogging the GPU (MPS). Closing Chrome or other high-GPU apps may help.
- **SSE Failures**: Ensure the NestJS `HttpService` is configured with `responseType: 'stream'`, otherwise the entire response will buffer before sending, breaking the "typing" effect.
- **CORS Errors**: If the frontend cannot reach the NestJS server during development, check the Vite proxy configuration in `vite.config.ts`.
- **Poetry Env**: If Python packages are missing, run `poetry install` inside `model-server/`. Avoid using `pip` directly to prevent dependency drift.
- **Build Path Issues**: If NestJS cannot find static files, verify that `ServeStaticModule` points to `join(__dirname, '..', '..', 'frontend', 'dist')` in `app.module.ts`.


## 11. Agent Contribution Guidelines
- **Commit Message Style**: Use imperative mood (e.g., "Add SSE handling", "Fix RAG metadata filter").
- **Documentation**: If adding a new agent handler, update the "LangGraph Component Breakdown" in this file.
- **Dependency Management**: 
  - For `app-server/backend`: Use `pnpm add`.
  - For `app-server/frontend`: Use `pnpm add`.
  - For `model-server`: Use `poetry add`.
- **Secret Handling**: Never commit `.env` files. Use the `.env.example` as a template for new environment variables.
- **Model Updates**: When updating the LLM engine, ensure the `MODEL_ID` in `app/engine.py` matches the fine-tuned adapter's base model.

---
*Updated by Sisyphus Agent - 2026-01-06*
*Reflects React migration and monorepo structure (frontend/backend separation)*
