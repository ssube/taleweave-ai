FROM python:3.10

WORKDIR /taleweave

# COPY requirements/cpu.txt /taleweave/requirements/cpu.txt
# RUN pip install --no-cache-dir -r requirements/cpu.txt

COPY requirements/base.txt /taleweave/requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt
RUN pip install --no-cache-dir --index-url https://test.pypi.org/simple/ packit_llm==0.1.0

COPY taleweave/ /taleweave/taleweave/

CMD ["python", "-m", "taleweave.main"]
