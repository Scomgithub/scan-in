FROM python:3.11-slim
RUN apt-get update && apt-get install -y libzbar0
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "$PORT"]