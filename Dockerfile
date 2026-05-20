# Build stage
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --trusted-host pypi.org \
                --trusted-host pypi.python.org \
                --trusted-host files.pythonhosted.org \
                --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install system dependencies for Kubernetes client
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/app/.local

# Copy application code
COPY app/app.py app/k8s_analyzer.py app/rancher_client.py app/translations.py app/FaureciaRootCA.cer ./

# Change ownership to app user
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Set Python path
ENV PATH=/home/app/.local/bin:$PATH
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/healthz || exit 1

# Start Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]