FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies (without lock file for dev flexibility)
RUN uv sync --python /usr/local/bin/python3

# Copy source
COPY . .

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/usr/local/bin/python3", "-m", "uvicorn", "src.capm.main:app", "--host", "0.0.0.0", "--port", "8000"]