# Use the official Python image
FROM python:3.13-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements file first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Run the app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]