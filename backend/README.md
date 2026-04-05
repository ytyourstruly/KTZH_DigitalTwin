# Backend — KTZH Digital Twin

API на FastAPI + PostgreSQL. Поток телеметрии: отдельный сервис симулятора (WebSocket) → этот бэкенд подключается как клиент, считает индекс и витрину, сначала шлёт JSON фронту по WebSocket, затем пишет в БД. Для быстрой проверки в Swagger: `GET /api/v1/telemetry/latest`.

---

## Что нужно заранее

- PostgreSQL (локально или Docker), созданная БД.
- Python версии из `pyproject.toml` (сейчас `>=3.14`).
- По желанию [uv](https://docs.astral.sh/uv/) — удобно ставить зависимости и запускать команды без ручной активации venv.

---

## Переменные окружения

Скопируйте пример и подставьте свои значения:

```bash
cp env.example .env
```

Список переменных см. в `env.example`. Для приёма телеметрии с симулятора включите:

```env
SIMULATOR_INGEST_ENABLED=true
SIMULATOR_WS_URL=ws://127.0.0.1:9001/telemetry
```

URL должен совпадать с адресом WebSocket симулятора (порт и путь `/telemetry`).

---

## База данных и миграции

Из каталога `backend/` (с рабочей `DATABASE_URL` или `POSTGRES_*` в `.env`):

**Через uv:**

```bash
uv sync
uv run alembic upgrade head
```

**Через свой venv** (см. ниже): после активации и установки зависимостей:

```bash
alembic upgrade head
```

---

## Запуск API (два способа)

Рабочий каталог — **`backend/`**. Сервер по умолчанию: `http://0.0.0.0:8000`.

### 1) Через uv (рекомендуется)

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`uv run` использует виртуальное окружение проекта (после `uv sync` это уже `.venv` в `backend/`).

### 2) Активированное `.venv` и `uvicorn` вручную (без `uv run`)

Если **uv** установлен, достаточно **`uv sync`** — отдельный `pip install -e .` не нужен: зависимости подтянутся из `pyproject.toml`, при необходимости создастся `.venv`.

**Linux / macOS:**

```bash
cd backend
uv sync
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Windows (cmd):**

```bat
cd backend
uv sync
.venv\Scripts\activate.bat
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Windows (PowerShell):**

```powershell
cd backend
uv sync
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Без uv** — классический venv и pip:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

На Windows те же шаги, но активация — `.venv\Scripts\activate.bat` или `Activate.ps1`, команда Python — `python`.

Полезные URL:

- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Поток для фронта: `ws://localhost:8000/api/v1/telemetry/stream`
- Последний кадр (polling): `http://localhost:8000/api/v1/telemetry/latest`

---

## Запуск симулятора

Симулятор лежит в соседней папке репозитория: `../simulator` (относительно `backend/`).

Порт по умолчанию — 9001 (см. `simulator/config.yaml`). Бэкенд по умолчанию ждёт `ws://127.0.0.1:9001/telemetry`.

### Через uv (без отдельного pyproject в симуляторе)

Из каталога **`simulator/`**:

```bash
cd ../simulator
uv run --with fastapi --with "uvicorn[standard]" --with pyyaml --with websockets --with pydantic \
  uvicorn main:app --host 0.0.0.0 --port 9001 --reload
```

Если порт занят — смените `--port` и обновите `SIMULATOR_WS_URL` в `.env` бэкенда.

### Через venv в симуляторе

```bash
cd simulator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt fastapi "uvicorn[standard]"
uvicorn main:app --host 0.0.0.0 --port 9001 --reload
```

На Windows активация: `.venv\Scripts\activate` или `Activate.ps1`.

Порядок для полного потока: поднять PostgreSQL → миграции → симулятор → бэкенд с `SIMULATOR_INGEST_ENABLED=true`.

---

## Структура каталога `backend/`

```
backend/
├── alembic/              # миграции БД
├── alembic.ini
├── app/
│   ├── main.py           # FastAPI-приложение, lifespan (фоновый ingest)
│   ├── api/              # HTTP/WebSocket роутеры (auth, telemetry) и зависимости
│   ├── core/             # настройки, логирование, безопасность, исключения
│   ├── db/               # объявление Base и сессия
│   ├── models/           # SQLAlchemy-модели (auth, loco)
│   ├── repositories/     # реализация доступа к таблицам (SQLAlchemy)
│   ├── services/         # сценарии (auth, телеметрия, локомотивы)
│   ├── provider/         # сборка сервисов на одну AsyncSession
│   ├── realtime/         # клиент к симулятору + fan-out на браузеры
│   ├── schemas/          # Pydantic-схемы запросов/ответов
│   └── middleware/
├── env.example           # шаблон .env
├── pyproject.toml
└── README.md
```

Логика «симулятор → БД → WebSocket фронту»:

- `app/realtime/simulator_client.py` — подключение к симулятору, парсинг кадров
- `app/services/loco/simulator_sync.py` — запись в `telemetry_current` / `telemetry_snapshots`
- `app/realtime/telemetry_hub.py` — список клиентов и рассылка JSON
- `app/api/routers/telemetry.py` — `WS /api/v1/telemetry/stream`, `GET .../latest`

---

## Расчёт индекса здоровья и полей в JSON (live view)

Вся логика в `app/services/loco/telemetry_live_view.py` (`build_live_payload`). Вход — кадр симулятора (`SimulatorFrame`: скорость, топливо, температура, `oil_pressure` → тормоз, напряжение, ток, `error_codes`, `health_hint`, `mode`).

### Нормы по метрикам (`METRIC_BANDS`)

Для каждой метрики заданы `norm_min` / `norm_max` и доля мягкой зоны `warn_margin_ratio` (от ширины нормы). Это не приходит с симулятора — это конфигурация бэкенда (при желании позже можно подменять строками из `loco.index_settings`).

### Статус и штраф по одной метрике

Обозначения для **одной** метрики (например, давление тормоза или ток):

| Обозначение            | Что это                                                                                                                                                                                       |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `value`                | Текущее значение из кадра симулятора (после маппинга полей: `oil_pressure` → тормоз и т.д.).                                                                                                  |
| `norm_min`, `norm_max` | Допустимый интервал «нормы» для этой метрики (из `METRIC_BANDS`).                                                                                                                             |
| `warn_margin_ratio`    | Доля от **ширины нормы** `(norm_max - norm_min)`, задающая «мягкую зону» у границ. Чем больше коэффициент, тем шире зона, где отклонение ещё считается относительно мягким при тех же числах. |


**Если `norm_min ≤ value ≤ norm_max`** — метрика в норме: статус `normal`, штраф `0`, дальнейшие формулы не нужны.

**Если значение вне интервала** — меряем, **насколько далеко** вышли за границу:

- **`gap`** — расстояние до ближайшей границы нормы в тех же единицах, что и метрика.
  - **Ниже** нормы: `gap = norm_min - value` (на сколько единиц не дотягиваем до нижнего порога).
  - **Выше** нормы: `gap = value - norm_max` (на сколько перевалили верх).
- **`w`** (ширина мягкой зоны) — `w = (norm_max - norm_min) * warn_margin_ratio`.
  - Это не «допуск по ГОСТ», а **масштаб чувствительности**: в знаменателе и в пороге `severity` участвует именно он.
  - У узких диапазонов (например, тормоз в `bar`) при той же доле `w` меньше в абсолютных единицах — отклонение на 1 `bar` даёт больший `ratio`, чем у «широкой» метрики.

**Насколько серьёзно выход за границу (цвет карточки метрики):**

- **`ratio = gap / w`** — «во сколько раз отступ больше искусственной мягкой зоны».
  - Интуиция: `ratio ≈ 1` — чуть задели «подушку»; `ratio > 2` — выскочили **существенно** дальше этой подушки → для UI статус метрики **`critical`**; при `0 < ratio ≤ 2` — **`warning`**.

**Вклад в интегральный индекс (число, которое потом вычитаем из 100):**

- **`penalty = min(100, gap² / w)`** — штраф растёт **квадратично** с отступом: малые выбросы дают малый вклад, большие — резко утяжеляют индекс.
  - Потолок `100` на одну метрику не даёт одной величине «снести» расчёт до бесконечности. По всем метрикам штрафы **складываются** в `metric_penalty_total`.

### Индекс 0–100

1. **`metric_penalty_total`** — сумма штрафов по метрикам.
2. Дополнительный штраф по **`error_codes`** зависит от их числа и уже накопленного стресса (`_error_penalty`).
3. **`index = 100 - metric_penalties - error_penalty`**, затем ограничение в `[0, 100]`.
4. Учёт **`health_hint`** симулятора (`_apply_simulator_hint`): может умножить индекс (например, в режимах spike / degrading) и поднять «внутренний» уровень тревоги.
5. После hint снова **clamp** индекса в `[0, 100]`.

### Общий `health_status` (норма / внимание / критично)

Решается в `_resolve_health_status`:

- Базово по **интегральному индексу**: ≥ 80 — `normal`, 50–79 — `attention`, **ниже 50** — `critical`.
- Если хотя бы одна метрика в **critical**, общий статус не «зелёный»: при индексе ≥ 45 обычно минимум **attention**; при индексе **ниже 45** остаётся **critical**. Так большой индекс не помечается «критично» только из‑за одной красной карточки, а низкий индекс остаётся согласованным с «критично».

### `top_factors`, `alerts`, `recommendations`, `trends`

- **`top_factors`** — вклад в индекс в процентах (масштаб от теоретического максимума штрафов `tmax`). Для метрик со статусом `critical` вклад визуально не занижается относительно самого тяжёлого штрафа в кадре (чтобы «critical» не давал крошечный процент при узкой полосе нормы).
- **`alerts`** — текстовые карточки по нарушенным метрикам (в т.ч. доля ниже порога по тормозам, превышение по температуре и т.д.).
- **`recommendations`** — правила: снижение нагрузки от температуры, тормоза, отдельная ветка если T уже выше `norm_max` (без вводящего в заблуждение «дохода» к точке ниже потолка).
- **`trends`** — производные по времени между последними кадрами в памяти (`*_per_min`), не с симулятора.

Подробные формулы и пороги смотри в исходнике модуля — README не дублирует каждую константу полосы.

---

## Логи

Уровень логирования: переменная **`LOG_LEVEL`** (например `DEBUG`, `INFO`), см. `app/core/logging_config.py`.