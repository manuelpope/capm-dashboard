# 📊 Financial Metrics Terminal (Beta & CAPM)

Proyecto de arquitectura híbrida para el cálculo y visualización de métricas financieras (**Beta** y **CAPM**) usando datos de Yahoo Finance.

Diseñado como un MVP profesional optimizado para **costo $0**, evitando las limitaciones de suspensión de procesos en plataformas PaaS como Render.

---

# 🏗️ Arquitectura del Sistema

El sistema sigue un modelo **trigger-based (event-driven)** con ejecución bajo demanda.

### Componentes

* **🖥️ Home Server (Local Scheduler)**

  * Ejecuta un `cron`
  * Despierta Render
  * Dispara el cálculo vía HTTP

* **☁️ Cloud API (Render)**

  * FastAPI como backend
  * Ejecuta lógica financiera
  * Persiste resultados

* **🗄️ Base de Datos (Neon / Supabase)**

  * PostgreSQL externo
  * Persistencia independiente del lifecycle de Render

* **🖥️ UI (Terminal Dashboard)**

  * HTML + estilo tipo terminal
  * Alto contraste (dark mode)

---

# 🔁 Flujo de Datos

```mermaid
flowchart LR
    A[Home Server Cron] -->|POST /sync| B[Render FastAPI]
    B --> C[yfinance API]
    B --> D[FinancialEngine]
    D --> E[PostgreSQL DB]
    E --> F[Dashboard HTML]
```

---

# 🛠️ Stack Tecnológico

| Capa        | Tecnología             |
| ----------- | ---------------------- |
| Lenguaje    | Python 3.11+           |
| Backend     | FastAPI + Uvicorn      |
| Data        | Pandas, NumPy, SciPy   |
| Data Source | yfinance               |
| DB          | PostgreSQL             |
| ORM         | SQLAlchemy             |
| Config      | Pydantic Settings      |
| Infra       | Render + Neon/Supabase |
| Scheduler   | Cron (Home Server)     |

---

# 🧱 Diseño del Sistema (POO)

### 1. `Settings`

* Manejo de variables de entorno
* Validación tipada (fail-fast)

### 2. `FinancialEngine`

* Descarga datos históricos
* Calcula:

  * retornos log
  * Beta (regresión)
  * CAPM

### 3. `DatabaseManager`

* Conexión a PostgreSQL
* Persistencia de métricas
* Lectura para dashboard

### 4. `TemplateGenerator`

* Render HTML
* Estilo terminal (CRT / Matrix)
* Footer con metadata

---

# ⚙️ Configuración

## `.env`

```env
DATABASE_URL=postgresql://user:password@host/db?sslmode=require
SECRET_TRIGGER_KEY=super_secret_token
MARKET_TICKER=^GSPC
RISK_FREE_RATE=0.042
ENV_MODE=production
```

---

# 🚀 Ejecución Local

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

---

# ⏰ Scheduler (Home Server)

```bash
crontab -e
```

```bash
0 18 * * 1-5 curl -X POST https://tu-app.render.com/sync \
  -H "x-api-key: super_secret_token"
```

### Estrategia anti-sleep (Render Free Tier)

```bash
for i in {1..3}; do
  curl -X POST https://tu-app.render.com/sync && break
  sleep 30
done
```

---

# 📊 Modelos Matemáticos

## Beta (β)

Regresión lineal:

```
Ri = α + βRm + ε
```

* β = sensibilidad al mercado
* Calculado con `scipy.stats.linregress`

---

## CAPM

```
E(Ri) = Rf + β (Rm - Rf)
```

Donde:

* `Rf`: tasa libre de riesgo
* `Rm`: retorno esperado del mercado

---

# 🧠 Estrategia de Ejecución

### Decisión clave del diseño:

❌ NO usar scheduler en Render
✅ Usar trigger externo (Home Server)

### Beneficios:

* Evita limitación de sleep
* Control total del timing
* Costo ≈ 0
* Arquitectura desacoplada

---

# 🗄️ Persistencia

* DB externa (Neon / Supabase)
* Render se vuelve **stateless**
* Datos sobreviven reinicios

---

# 🎨 UI / UX

## Estilo

* Tema: **Dark Terminal**
* Inspiración: consola financiera / trading desk

## Paleta

| Elemento    | Color     |
| ----------- | --------- |
| Fondo       | `#0a0a0a` |
| Primario    | `#00ff41` |
| Secundario  | `#008f11` |
| Texto muted | `#888`    |

## Características

* Tipografía monoespaciada
* Tabla con hover
* Footer técnico:

  * status
  * timestamp
  * engine version

---

# 🔐 Seguridad

* Endpoint protegido con header:

  ```
  x-api-key
  ```
* Validación contra `SECRET_TRIGGER_KEY`
* Evita ejecuciones públicas del cálculo

---

# 📦 Escalabilidad futura

* Cache (Redis)
* Async jobs (Celery / RQ)
* WebSockets para live updates
* Integración con dashboards BI
* Multi-portfolio support

---

# 🧩 Filosofía del Proyecto

* **Simple > Complejo**
* **Event-driven > Always-on**
* **Stateless API > Stateful server**
* **Costo mínimo, valor máximo**

---

# ✅ Estado

🚧 MVP funcional
📈 Listo para iterar a producto fintech más serio

---

**Autor:** Manuel Andrés Tobón Bayona
**Tipo:** MVP → Arquitectura escalable
**Objetivo:** Validar sistema financiero automatizado de bajo costo
