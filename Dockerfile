FROM python:3.10-slim

WORKDIR /app

# Install required packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code and welcome image
COPY bot.py .
COPY welcome.jpg .

# Expose the health check port
EXPOSE 8080

# Set environment variables
ENV PORT=8080

# Run the bot
CMD ["python", "bot.py"]
