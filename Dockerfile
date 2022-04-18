FROM python:3.9.9

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
COPY ./.env /code/.env
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install pydantic[dotenv]
COPY ./app /code/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]