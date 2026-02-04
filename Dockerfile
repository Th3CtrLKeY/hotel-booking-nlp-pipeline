FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY hotel_email_parser/ ./hotel_email_parser/
COPY pipeline/ ./pipeline/
COPY config/ ./config/
COPY models/ ./models/
COPY utils/ ./utils/
COPY README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Create output directory
RUN mkdir -p /app/output

# Set Python path
ENV PYTHONPATH=/app

# Default command - show help
ENTRYPOINT ["python", "-m", "hotel_email_parser"]
CMD ["--help"]
