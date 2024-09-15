# # Use the official Python image
# FROM python:3.12

# # Set environment variables
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# # Set the working directory
# WORKDIR /app

# # Install dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the application code
# COPY . .

# # Expose the port that Gunicorn will run on
# EXPOSE 8000

# # Command to run the application with Gunicorn
# CMD ["gunicorn", "trend.wsgi:application", "--workers", "4", "--bind", "0.0.0.0:8000"]

# Stage 1: Build environment
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install dependencies
# RUN apt-get update && apt-get -y install libpq-dev gcc
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# # Stage 2: Runtime environment
# FROM python:3.12-slim AS runtime

# # Set environment variables
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# # Set the working directory
# WORKDIR /app

# # Copy only necessary files from the build environment
# COPY --from=builder /packages /usr/lib/python3.12/site-packages
# ENV PYTHONPATH=/usr/lib/python3.12/site-packages

# Security Context 
RUN useradd -m nonroot
USER nonroot

# Expose the port that Gunicorn will run on
EXPOSE 8000

# Command to run the application with Gunicorn
CMD ["gunicorn", "trend.wsgi:application", "--workers", "4", "--bind", "0.0.0.0:8000"]
