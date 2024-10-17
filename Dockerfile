FROM python:3.12-slim

WORKDIR /truecolors

COPY requirements.txt .
RUN python3 -m venv .venv
RUN .venv/bin/pip install -r requirements.txt

COPY static ./static
COPY templates ./templates
COPY server.py ./

CMD [ ".venv/bin/gunicorn", "--workers", "4", "--bind", "0.0.0.0:80", "server:app" ]
