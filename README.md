# KTZH Digital Twin

**Визуальный цифровой двойник локомотива** с потоковой телеметрией, **индексом здоровья (0–100)** и расшифровкой факторов — full-stack прототип, агрегация сигналов в реальном времени, понятный дашборд «кабины», базовая безопасность и хранение истории в PostgreSQL.

---

## Задача кейса


| Ожидание организаторов                                             | Как закрыто в репозитории                                                                                                                                                     |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Поток телеметрии в реальном времени (≥1 Гц, допускается симулятор) | Отдельный **симулятор** (`simulator/`) → WebSocket → **backend** → WebSocket/SSE-совместимый поток на дашборд                                                                 |
| Индекс здоровья и категории состояния                              | Правила в `backend/app/services/loco/telemetry_live_view.py`: штрафы по полосам норм, **норма / внимание / критично**; любая метрика **critical** → общий статус **critical** |
| Объяснимость (топ факторов)                                        | Поле `top_factors` в live JSON                                                                                                                                                |
| Визуализация: графики, тренды, алерты, рекомендации                | **Next.js** дашборд (`frontend/`)                                                                                                                                             |
| Низкая задержка, устойчивость канала                               | Fan-out в памяти, reconnect у ingest к симулятору; клиент может передавать токен в query для WS                                                                               |
| История, настройки без пересборки                                  | `telemetry_snapshots` / `telemetry_current`; таблица `loco.index_settings` + REST (см. backend README)                                                                        |
| Аутентификация, ограничение настроек                               | Сессии + роль **admin** для изменения порогов                                                                                                                                 |
| Документация API                                                   | Swagger: `http://localhost:8000/docs`                                                                                                                                         |


Подробные формулы индекса, переменные окружения и миграции — в **[backend/README.md](backend/README.md)**. Формат симулятора и частоты (`normal` / `highload` / `burst`) — в **[simulator/README.md](simulator/README.md)**.

---

## Архитектура

```text
┌─────────────────────┐     WebSocket      ┌──────────────────────────────┐
│  Locomotive         │  ws://…:9001/      │  FastAPI backend             │
│  simulator          │  telemetry   ──▶  │  ingest → live JSON → PG      │
│  (simulator/)       │                    │  WS /api/v1/telemetry/stream │
└─────────────────────┘                    └──────────────┬───────────────┘
                                                            │
                     HTTP + WebSocket (auth)                │
                                                            ▼
                                               ┌────────────────────────────┐
                                               │  Next.js dashboard        │
                                               │  (frontend/)               │
                                               └────────────────────────────┘
```

- **Симулятор** не ходит в БД: только генерирует кадры и отдаёт их всем подписчикам.  
- **Backend** подключается к симулятору как **клиент**, считает индекс и витрину, **сначала** рассылает данные **затем** пишет в PostgreSQL.  
- **Фронт** использует API (логин, `/latest`, настройки индекса) и в WebSocket поток с учётом сессии.

---

## Структура репозитория


| Каталог                  | Назначение                                                               |
| ------------------------ | ------------------------------------------------------------------------ |
| [backend/](backend/)     | FastAPI, PostgreSQL (Alembic), auth, телеметрия,                         |
| [simulator/](simulator/) | Изолированный сервис WebSocket + HTTP control (`/frequency`, `/mode`, …) |
| [frontend/](frontend/)   | Next.js: кабина, индекс здоровья, карточки метрик, графики, алерты       |


---

## Быстрый старт (локально)

Нужны: **PostgreSQL**, **Python 3.14+** (backend), **Node.js** (frontend). Рекомендуется [uv](https://docs.astral.sh/uv/) для backend.

### 1. База данных

Создайте БД и выполните миграции из каталога `backend/` (подробно в [backend/README.md](backend/README.md)):

```bash
cd backend
cp env.example .env
# отредактируйте POSTGRES_* или DATABASE_URL
uv sync
uv run alembic upgrade head
```

### 2. Симулятор (порт **9001** по умолчанию)

```bash
cd simulator
# см. simulator/README.md — uv run или venv + uvicorn
uvicorn main:app --host 0.0.0.0 --port 9001 --reload
```

### 3. Backend (порт **8000**)

```bash
cd backend
# в .env: SIMULATOR_INGEST_ENABLED=true, SIMULATOR_WS_URL=ws://127.0.0.1:9001/telemetry
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Проверка: [http://localhost:8000/health](http://localhost:8000/health), [http://localhost:8000/docs](http://localhost:8000/docs), [http://localhost:8000/metrics](http://localhost:8000/metrics).

### 4. Frontend

```bash
cd frontend
cp env.example .env.local
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
npm install
npm run dev
```

Откройте [http://localhost:3000](http://localhost:3000) — войдите после регистрации; при необходимости выдайте роль администратора в БД для `PATCH /index-settings`.

**Типичный порядок запуска:** PostgreSQL → миграции → симулятор → backend → frontend.

---

## Нагрузочная проверка (демо)

Симулятор поддерживает пресеты частоты, например **×10** к базовому потоку:

```bash
curl -s -X POST http://127.0.0.1:9001/frequency \
  -H "Content-Type: application/json" \
  -d '{"preset": "highload"}'
```

Смотрите задержки и счётчики на `GET /metrics` у backend. Подробнее — в [backend/README.md](backend/README.md) и [simulator/README.md](simulator/README.md).

---

## Безопасность и данные

- Не использовать реальные коммерческие данные без согласования; по умолчанию — **mock / симулятор**.  
- Секреты и пароли только через **переменные окружения** (шаблоны: `backend/env.example`, `frontend/env.example`).  

