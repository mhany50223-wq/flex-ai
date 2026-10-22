FROM python:3.11-slim

WORKDIR /app

COPY gemini/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY gemini/ ./

ENV PORT=7860
EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "app:app"]
