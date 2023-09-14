FROM python:3.11

WORKDIR /app
COPY . /app/
RUN pip3 install -r requirements.txt --no-cache-dir

RUN python3 manage.py migrate

ENTRYPOINT [ "python3" ]
CMD ["manage.py", "runserver", "0.0.0.0:8000"]
