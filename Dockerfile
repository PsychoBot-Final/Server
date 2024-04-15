FROM python:3.9

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt

RUN pip install gunicorn

COPY . /app/

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]