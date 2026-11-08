FROM python:3.14-slim-trixie@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f

# Base digest observed in cloud run 42510811993 (Python 3.14.10).
# Debian package versions remain mutable; CI records them. Ghidra and the
# XEX extension are separately SHA-256 pinned.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       bash ca-certificates curl git unzip openjdk-21-jdk-headless \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash analyst
ENV PYTHONUNBUFFERED=1
USER analyst
WORKDIR /workspaces/dotm
