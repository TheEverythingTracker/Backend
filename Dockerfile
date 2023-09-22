FROM python:3.11-slim

RUN useradd -u 8877 containeruser

WORKDIR /code
COPY pyproject.toml /code

RUN pip3 install --no-cache-dir poetry
# do not create virtual env since we already are in a container
RUN poetry config virtualenvs.create false

# install
RUN poetry install --no-dev

USER containeruser
# changes often so put as close to the end as possible since the rest can be cached by docker
COPY ./app /code/

WORKDIR /code/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
