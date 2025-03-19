# filepath: Dockerfile
FROM python:3.11-slim

# Set environment variables (if needed, these can also be set in Vercel dashboard)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port your app is running on (e.g., 7860 for Gradio)
EXPOSE 7860

# Run the app (ensure your app listens on 0.0.0.0)
CMD ["python", "-m", "gradio", "app.py"]