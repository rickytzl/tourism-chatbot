# Use official Python image as base
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy only the requirements file to install dependencies first (improves caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 8050 for Dash
EXPOSE 8050

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the Dash app
CMD ["python", "app.py"]
