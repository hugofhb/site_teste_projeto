RUN apt-get update && \
    apt-get install -y python3-dev && \
    rm -rf /var/lib/apt/lists/*
