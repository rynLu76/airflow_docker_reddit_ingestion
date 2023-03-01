FROM apache/airflow:2.2.3
USER root
RUN  apt-get update \
     && apt-get install -y wget \
     && rm -rf /var/lib/apt/lists/*
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_mac64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
ENV DISPLAY=:99

COPY . /app
WORKDIR /app

RUN pip install --upgrade pip

USER airflow
RUN pip install selenium && \
    pip install praw && \
    pip install pendulum && \
    pip install spacy && \
    pip install scikit-learn==1.0 && \
    pip install textblob && \
    pip install webdriver-manager && \
    pip install nltk && \
    pip install webdriver-manager