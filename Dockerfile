FROM python:3.10

WORKDIR /taleweave

COPY requirements/base.txt /taleweave/requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

COPY taleweave/ /taleweave/taleweave/
COPY prompts/ /taleweave/prompts/
COPY config.yml /taleweave/config.yml

CMD ["python", "-m", "taleweave.main"]
