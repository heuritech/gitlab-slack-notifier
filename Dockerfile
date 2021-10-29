FROM python:3.8-alpine

ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 5000
ENV FLASK_APP gitlabnotifier/app.py

RUN pip install --upgrade pip

RUN adduser -D captain
USER captain
WORKDIR /home/captain
ENV PATH="/home/captain/.local/bin:${PATH}"

COPY --chown=captain:captain requirements.txt .
RUN pip install --user -r requirements.txt

COPY --chown=captain:captain setup.py .
COPY --chown=captain:captain gitlabnotifier gitlabnotifier
RUN pip install --user .

ENTRYPOINT ["flask", "run"]
