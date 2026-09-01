FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry==1.8.3

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no dev deps, no root package yet)
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-root --no-interaction

# Copy source
COPY . .

# Install the screen package itself
RUN poetry install --only=main --no-interaction

# Create non-root user
RUN adduser --disabled-password --gecos "" screenuser \
    && chown -R screenuser:screenuser /app
USER screenuser

EXPOSE 8001

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
