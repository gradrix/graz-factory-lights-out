FROM python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca AS build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential ca-certificates curl && rm -rf /var/lib/apt/lists/*
WORKDIR /build
RUN curl -fsSL https://www.sqlite.org/2026/sqlite-autoconf-3510300.tar.gz -o sqlite.tar.gz && echo '81f5be397049b0cae1b167f2225af7646fc0f82e4a9b3c48c9ea3a533e21d77a  sqlite.tar.gz' | sha256sum -c - && tar xzf sqlite.tar.gz
WORKDIR /build/sqlite-autoconf-3510300
RUN ./configure --prefix=/opt/sqlite --disable-static --disable-readline && make -j2 && make install
FROM python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca
COPY requirements.lock /tmp/requirements.lock
RUN python -m pip install --no-cache-dir -r /tmp/requirements.lock && python -m pip check
COPY --from=build /opt/sqlite/lib /opt/sqlite/lib
ENV LD_LIBRARY_PATH=/opt/sqlite/lib
RUN python -c 'import sqlite3; assert sqlite3.sqlite_version == "3.51.3"; print(sqlite3.sqlite_version)'
