FROM python:3.12

WORKDIR /app

# Добавляем необходимые системные зависимости
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 libsm6 libxrender1 libxext6

COPY requirements.txt .

RUN pip install --no-cache-dir --timeout=100 -i https://pypi.org/simple -r requirements.txt
COPY . .

# Запуск через python -m uvicorn (лучше для path)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
