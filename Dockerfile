FROM ubuntu:18.04
WORKDIR /main
COPY . ./
ENV LANG zh_TW.UTF-8
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get update && \
    apt-get install -y python3-pip tzdata && \
    dpkg-reconfigure -f noninteractive tzdata && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt && \
    apt-get install -y chromium-browser && \
    apt-get install -y fonts-moe-standard-song && \
    apt-get install -y ffmpeg && \
    apt-get install -y language-pack-zh-hant*

CMD uwsgi -w main:app --http-socket :$PORT