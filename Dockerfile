FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create output directory
RUN mkdir -p /app/output

# Run the forecast
CMD ["python", "weather_forecast.py"]
