# Deployment Guide

Guía completa para desplegar el Financial Metrics Terminal en desarrollo y producción.

---

## 1. Desarrollo Local

### Requisitos

- Python 3.11+
- Git

### Setup

```bash
# Clonar repo
git clone <repo-url>
cd CAPM

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables
cp .env.example .env
# Editar .env según necesidad
```

### Ejecutar

```bash
uvicorn main:app --reload
```

Dashboard: `http://localhost:8000`

---

## 2. Producción: Render + Neon

### 2.1 Base de Datos (Neon / Supabase)

**Neon:**

1. Crear cuenta en [neon.tech](https://neon.tech)
2. Crear proyecto nuevo
3. Copiar connection string (formato: `postgresql://user:pass@host/db?sslmode=require`)

**Supabase:**

1. Crear cuenta en [supabase.com](https://supabase.com)
2. Crear proyecto nuevo
3. Ir a Settings → Database → Copiar connection string

### 2.2 Deploy en Render

1. Crear cuenta en [render.com](https://render.com)
2. New → Web Service
3. Conectar repositorio de GitHub
4. Configurar:

| Campo              | Valor                        |
| ------------------ | ---------------------------- |
| **Runtime**        | Python 3                     |
| **Build Command**  | `pip install -r requirements.txt` |
| **Start Command**  | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

5. Agregar variables de entorno:

| Variable             | Valor                                    |
| -------------------- | ---------------------------------------- |
| `SECRET_TRIGGER_KEY` | Token seguro (generar con `openssl rand -hex 32`) |
| `MARKET_TICKER`      | `^GSPC`                                  |
| `RISK_FREE_RATE`     | `0.042`                                  |
| `DATABASE_URL`       | `postgresql://...` (de Neon/Supabase)    |
| `ENV_MODE`           | `production`                             |

6. Deploy

### 2.3 Migración de SQLite a PostgreSQL

**Cambios necesarios:**

1. Instalar driver PostgreSQL:

```bash
pip install psycopg2-binary
```

2. Agregar a `requirements.txt`:

```
psycopg2-binary>=2.9.9
```

3. Modificar `app/database.py`:

```python
import os
from app.config import settings

def get_db_url():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    return f"sqlite:///{settings.db_path}"

# En DatabaseManager:
self.engine = create_engine(get_db_url(), echo=False)
```

4. Las tablas se crean automáticamente con `Base.metadata.create_all()`

---

## 3. Scheduler (Home Server)

### Cron (Linux/macOS)

```bash
crontab -e
```

Agregar línea (ejemplo: lunes a viernes a las 6pm):

```bash
0 18 * * 1-5 curl -X POST https://tu-app.onrender.com/sync \
  -H "x-api-key: $SECRET_TRIGGER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "MSFT", "GOOGL", "TSLA"]}'
```

### Estrategia Anti-Sleep (Render Free Tier)

Render suspende servicios inactivos después de 15 minutos. Para despertarlo:

```bash
#!/bin/bash
# sync.sh
for i in {1..3}; do
  response=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://tu-app.onrender.com/sync \
    -H "x-api-key: $SECRET_TRIGGER_KEY" \
    -H "Content-Type: application/json" \
    -d '{"tickers": ["AAPL", "MSFT", "GOOGL", "TSLA"]}')

  if [ "$response" = "200" ]; then
    echo "Sync successful"
    break
  fi

  echo "Attempt $i failed, retrying in 30s..."
  sleep 30
done
```

Cron con retry:

```bash
0 18 * * 1-5 /path/to/sync.sh >> /var/log/capm-sync.log 2>&1
```

### Windows (Task Scheduler)

1. Abrir Task Scheduler
2. Create Basic Task
3. Trigger: Weekly (Mon-Fri, 6pm)
4. Action: Start a program
   - Program: `powershell.exe`
   - Arguments:

```powershell
-Command "Invoke-RestMethod -Uri 'https://tu-app.onrender.com/sync' -Method POST -Headers @{'x-api-key'='$env:SECRET_TRIGGER_KEY'; 'Content-Type'='application/json'} -Body '{\"tickers\":[\"AAPL\",\"MSFT\",\"GOOGL\",\"TSLA\"]}'"
```

---

## 4. Verificación

### Check health

```bash
curl https://tu-app.onrender.com/
```

### Trigger manual

```bash
curl -X POST https://tu-app.onrender.com/sync \
  -H "x-api-key: $SECRET_TRIGGER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "MSFT"]}'
```

### Ver métricas

```bash
curl https://tu-app.onrender.com/api/metrics
```

---

## 5. Monitoreo

### Logs en Render

Dashboard → Tu servicio → Logs

### Logs locales del cron

```bash
# Ver logs de sync
tail -f /var/log/capm-sync.log

# Ver cron logs
grep CRON /var/log/syslog
```

---

## 6. Escalabilidad Futura

| Mejora              | Implementación                    |
| ------------------- | --------------------------------- |
| Cache               | Redis (Upstash free tier)         |
| Async jobs          | Celery + Redis                    |
| Live updates        | WebSockets                        |
| Multi-portfolio     | Agregar tabla `portfolios`        |
| BI Integration      | Exponer endpoint CSV/JSON         |
| Rolling Beta        | Implementar `RollingBeta` class   |
| GARCH               | Implementar `GARCHBeta` class     |

---

## 7. Troubleshooting

### Error: "No data for ticker"

- Verificar que el ticker existe en Yahoo Finance
- El mercado puede estar cerrado

### Error: "Invalid or missing API key"

- Verificar que `x-api-key` coincide con `SECRET_TRIGGER_KEY`

### Render sleep timeout

- Usar estrategia anti-sleep con retries
- Considerar upgrade a paid tier si es crítico

### SQLite locked

- No correr múltiples instancias simultáneas
- Migrar a PostgreSQL para producción
