FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including WeasyPrint requirements for PDF generation)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Create non-root user and storage directory
RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/storage \
    && chmod +x /app/docker-entrypoint.sh \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
