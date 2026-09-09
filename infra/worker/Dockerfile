FROM python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca
COPY wheels /opt/wheels
COPY requirements.lock /opt/requirements.lock
RUN python -m pip install --no-index --no-cache-dir --require-hashes --find-links=/opt/wheels -r /opt/requirements.lock && rm -rf /opt/wheels
ENV PYTHONDONTWRITEBYTECODE=1
