# Trinity ISE II — Simulador de examen

Simulador local de examen oral y escrito para el Trinity ISE II (B2), con
corrección por IA personalizada al contexto y a los errores recurrentes del
candidato.

**Estado actual:** Dashboard, Reading (Task 1/2/3), Writing (Task 4) y
Speaking & Listening (Topic, Collaborative, Conversation e Independent
Listening, en una sesión única de 20 minutos) funcionando de extremo a
extremo, con entrada por voz o texto, TTS para el examinador virtual, y
RAG sobre material propio integrado en las cuatro correcciones. El
clasificador de errores basado en ERRANT (FCE / W&I+LOCNESS) llega en el
siguiente bloque.

## Arquitectura

```
Simulador_Examen/
├── backend/            FastAPI — único lugar que conoce ANTHROPIC_API_KEY
│   └── app/
│       ├── routers/    endpoints HTTP (delgados)
│       ├── services/   lógica de negocio, RAG y llamadas a Claude
│       ├── models/     esquemas Pydantic + modelos SQLAlchemy
│       ├── core/       config y conexiones a base de datos (app + vectorial)
│       └── data/       examen fijo de Reading + propuestas fijas de Writing
│   └── scripts/        script de ingesta de /context al RAG
├── frontend/           Vite + React + TypeScript + Tailwind CSS
├── context/            Tus PDFs y apuntes propios (ingeridos para el RAG)
└── docker-compose.yml  backend + Postgres/pgvector
```

La API key de Anthropic vive **solo** en `backend/.env` y nunca se envía al
frontend: todas las llamadas a Claude pasan por el backend, que actúa de
proxy seguro.

## Requisitos

- Node.js 20+
- Python 3.12 (¡no 3.13! `chroma-hnswlib`/pgvector aún no publican wheels
  precompilados para 3.13 en Windows, y compilar desde código fuente
  requiere Visual Studio Build Tools)
- Docker y Docker Compose, para el vector DB (Postgres + pgvector)
- Una API key de Anthropic (https://console.anthropic.com/)

## Instalación y arranque en local

### 1. Vector DB (necesario para el RAG en Reading y Writing)

```bash
docker compose up -d vector_db
```

Levanta Postgres con la extensión `pgvector` en el puerto `5433` del host
(no `5432`, para no chocar con una instalación local de PostgreSQL si ya
tienes una). Si el backend no encuentra el vector DB, las correcciones
siguen funcionando con normalidad — el RAG simplemente no añade contexto
extra.

### 2. Backend

```bash
cd backend
python -m venv venv          # asegúrate de que sea Python 3.12
venv\Scripts\activate         # Windows
# source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt

copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
# Edita backend/.env y pon tu ANTHROPIC_API_KEY real

uvicorn app.main:app --reload --port 8000
```

El backend queda escuchando en `http://localhost:8000` (documentación
interactiva en `http://localhost:8000/docs`).

### 3. Ingesta de tu material propio (RAG)

Coloca tus PDFs y apuntes en `context/` (puedes usar subcarpetas) y ejecuta:

```bash
cd backend
venv\Scripts\python.exe scripts/ingest_context.py
```

El script extrae el texto de cada PDF, lo trocea por párrafo/sección
(nunca por un número fijo de caracteres), genera embeddings localmente
(`sentence-transformers`, sin API externa) y los guarda en pgvector. Es
idempotente: si editas un PDF y vuelves a ejecutar el script, sus
fragmentos se actualizan sin duplicarse. Los PDFs escaneados o con solo
imágenes (sin texto seleccionable) se detectan y se omiten con un aviso —
no hay OCR todavía.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend queda en `http://localhost:5173` y redirige automáticamente las
peticiones a `/api/*` hacia el backend (ver `vite.config.ts`).

## Arranque con Docker (backend + vector DB)

```bash
cp backend/.env.example backend/.env   # y añade tu ANTHROPIC_API_KEY
docker compose up --build
```

Esto levanta Postgres/pgvector y el backend en `http://localhost:8000`,
con persistencia de la base de datos SQLite en `backend/app/data/` y del
vector DB en un volumen Docker. El frontend, de momento, se sigue
ejecutando con `npm run dev` fuera de Docker (hot-reload más cómodo en
desarrollo). Para ingerir `/context` con el backend en Docker, ejecuta el
script de ingesta en tu entorno local (apuntando a `localhost:5433`) — es
el mismo comando que en desarrollo local.

## Bases de datos

- **SQLite** (`backend/app/data/app.db`): progreso, historial de sesiones
  de práctica con su puntuación/banda/errores, y el log de auditoría del
  RAG (`rag_retrieval_logs`) — qué se buscó, qué fragmentos volvieron y
  con qué score de similitud (consultable en `GET /api/rag/logs`).
- **Postgres + pgvector** (`vector_db`, puerto `5433`): fragmentos de tu
  material propio con sus embeddings, usados para recuperación en cada
  corrección de Reading y Writing.

## RAG — cómo se usa en la corrección

Antes de pedirle a Claude que corrija una respuesta de texto libre
(Reading: sinónimos/frases/resumen; Writing: la redacción completa), el
backend recupera los 2-3 fragmentos más relevantes de tu propio material
por similitud de embeddings y los añade como contexto al prompt. Cada
recuperación queda registrada — puedes auditar la calidad vía
`GET /api/rag/logs`.

## Variables de entorno (`backend/.env`)

Ver `backend/.env.example` para la lista completa y su descripción. Nunca
subas `backend/.env` a git — ya está en `.gitignore`.
