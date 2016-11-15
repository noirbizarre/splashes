FROM python:3.5-alpine
ENV PYTHONUNBUFFERED 1

RUN mkdir /splashes
WORKDIR /splashes
ADD . /splashes/

RUN pip install -e .

ENTRYPOINT ["splashes"]
CMD ["--help"]
