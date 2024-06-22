FROM python:3.10

WORKDIR /taleweave

COPY requirements/base.txt /taleweave/requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

COPY taleweave/ /taleweave/taleweave/
COPY prompts/ /taleweave/prompts/
COPY config.yaml /taleweave/config.yaml

CMD ["python", "-m", "taleweave.main"]
