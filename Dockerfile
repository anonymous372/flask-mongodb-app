# Base image with Python 3.9 slim for smaller size and security
FROM python:3.9-slim

# Prevent Python from writing .pyc files to disc and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Create a non-privileged user to run the application securely
RUN groupadd -r appgroup && useradd -r -g appgroup -u 10001 appuser

# Copy and install dependencies first to take advantage of Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app.py .

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]

