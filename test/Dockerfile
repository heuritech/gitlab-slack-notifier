ARG BASE_IMAGE

FROM $BASE_IMAGE

ENV FLASK_ENV development

RUN pip install --user pytest

COPY --chown=captain:captain test test

ENTRYPOINT ["pytest"]
