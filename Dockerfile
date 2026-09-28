FROM python:3.12-slim

# tesseract-ocr is required for the receipt scanning feature.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY frontend ./frontend

WORKDIR /app/backend

ENV DATABASE_URL=sqlite:////app/backend/data/foodwise.db
ENV AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
ENV AZURE_OPENAI_API_KEY=
ENV AZURE_OPENAI_DEPLOYMENT=gpt-5.4
ENV AZURE_OPENAI_API_VERSION=2024-12-01-preview

EXPOSE 8000


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
