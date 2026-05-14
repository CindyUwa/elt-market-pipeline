FROM ubuntu:latest
LABEL authors="cindy"

ENTRYPOINT ["top", "-b"]