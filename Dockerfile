FROM python:3.10

WORKDIR /taleweave

COPY requirements/base.txt /taleweave/requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

COPY taleweave/ /taleweave/taleweave/

CMD ["python", "-m", "taleweave.main"]
