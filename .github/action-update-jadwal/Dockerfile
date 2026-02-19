FROM python:slim

RUN apt-get update; \
    apt-get install -y git

ENV HOME=/root
RUN git config --system --add safe.directory /github/workspace
	

RUN pip install --no-cache-dir \
        lxml \
        requests \
        pytz

ENTRYPOINT ["python3", "./script/parser.py"]