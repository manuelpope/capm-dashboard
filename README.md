# Financial Metrics Terminal (CAPM)

MVP para cálculo y visualización de métricas financieras (**Beta**, **CAPM**, **Sharpe**) usando datos de Yahoo Finance.

---

## Arquitectura

```
src/capm/
├── main.py              # FastAPI app + lifespan
├── config.py            # Settings
├── domain/              # Capa de dominio
│   └── repositories.py  # Modelos + DB Manager
├── application/         # Capa de aplicación
│   ├── engine.py        # FinancialEngine
│   ├── beta_models.py  # OLSBeta, GARCHBeta
│   └── adapters.py      # YahooDataAdapter
├── infrastructure/      # Capa de infraestructura
│   └── templates.py     # Dashboard HTML
└── api/                 # Capa de presentación
    ├── routes.py        # Endpoints
    └── deps.py         # Dependencies
```

---

## Stack

| Capa        | Tecnología           |
| ----------- | -------------------- |
| Lenguaje    | Python 3.12          |
| Backend     | FastAPI + Uvicorn    |
| Data        | Pandas, NumPy, SciPy |
| Data Source | yfinance             |
| DB          | SQLite               |
| ORM         | SQLAlchemy           |
| Config      | Pydantic Settings    |
| Health      | fastapi-health       |

---

## Instalación

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar en modo editable
pip install -e .

# Configurar variables de entorno
cp .env.example .env
```

---

## Ejecución

```bash
# Desarrollo
source venv/bin/activate
uvicorn src.capm.main:app --reload --port 8000

# Docker
docker-compose up --build
```

Dashboard disponible en `http://localhost:8000`

---

## API Endpoints

| Método   | Ruta                    | Descripción                      | Auth          |
| -------- | ----------------------- | -------------------------------- | ------------- |
| `GET`    | `/`                    | Dashboard terminal               | No            |
| `GET`    | `/health`              | Health check                     | No            |
| `POST`   | `/sync`                | Calcular métricas                | `x-api-key`   |
| `GET`    | `/api/metrics`         | Listar todas las métricas        | No            |
| `GET`    | `/api/metrics/{ticker}`| Get métrica de un ticker         | No            |
| `DELETE` | `/api/metrics/{ticker}`| Eliminar ticker                  | `x-api-key`   |
| `PATCH`  | `/api/metrics/{ticker}/active` | Toggle activo         | `x-api-key`   |
| `GET`    | `/api/tickers`         | Listar tickers disponibles        | No            |
| `GET`    | `/api/sync/status`    | Estado del sync                  | No            |
| `GET`    | `/api/config`          | Ver configuración actual         | No            |

### Ejemplos

```bash
# Sync con tickers custom
curl -X POST http://localhost:8000/sync \
  -H "x-api-key: super_secret_token" \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "MSFT", "GOOGL"]}'

# Get métrica individual
curl http://localhost:8000/api/metrics/AAPL

# Toggle activo
curl -X PATCH http://localhost:8000/api/metrics/AAPL/active \
  -H "x-api-key: super_secret_token" \
  -H "Content-Type: application/json" \
  -d '{"active": false}'
```

---

## Configuración (.env)

```env
SECRET_TRIGGER_KEY=super_secret_token
MARKET_TICKER=^GSPC
DB_PATH=capm.db
ENV_MODE=development
DEFAULT_TICKERS=AAPL,MSFT,AMZN,GOOGL,META,NVDA,JPM,JNJ,WMT,XOM
BETA_METHOD=ols
DATA_PERIOD=2y
BETA_BUY_THRESHOLD=0.7
BETA_SELL_THRESHOLD=1.3
ALPHA_BUY_THRESHOLD=0.0
SHARPE_BUY_THRESHOLD=1.0
```

---

## Métricas Calculadas

| Métrica   | Descripción                              |
| --------- | --------------------------------------- |
| **Beta**  | Sensibilidad al mercado (OLS/GARCH)      |
| **Alpha** | Retorno exceso sobre CAPM               |
| **CAPM**  | Retorno esperado según CAPM             |
| **Sharpe**| Ratio de Sharpe anualizado              |
| **R²**    | Coeficiente de determinación            |
| **P-Value** | Significancia estadística             |

### Señales (Dashboard)

| Condición | Color  | Indicación           |
| --------- | ------ | -------------------- |
| Beta < 0.7 | 🟢    | Defensivo (buy)      |
| Beta > 1.3 | 🔴    | Agresivo (sell)      |
| Alpha > 0  | 🟢    | Exceso retorno       |
| Sharpe > 1 | 🟢    | Buen risk-adjusted   |

---

## Diseño Extensible (Beta)

```python
class BetaCalculator(ABC):
    @abstractmethod
    def calculate(asset_returns, market_returns) -> BetaResult:
        pass

class OLSBeta(BetaCalculator):       # Default
class GARCHBeta(BetaCalculator):     # Configurable via BETA_METHOD
```

---

## Docker

```bash
# Build
docker build -t capm .

# Run
docker run -p 8000:8000 -v ./capm.db:/app/capm.db capm

# Docker Compose
docker-compose up --build
```

---

## Filosofía

- **Simple > Complejo**
- **Data real > Hardcoded**
- **Costo mínimo, valor máximo**

---

**Autor:** Manuel Andrés Tobón Bayona  
**Estado:** MVP funcional
