FROM python:3.14-slim-trixie

# The Python image tag and Debian packages are mutable; record their versions
# in each run. Ghidra and the XEX extension are separately SHA-256 pinned.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       bash ca-certificates curl git unzip openjdk-21-jdk-headless \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash analyst
ENV PYTHONUNBUFFERED=1
USER analyst
WORKDIR /workspaces/dotm
