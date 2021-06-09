FROM python:3.8.10

# Create app directory
WORKDIR /usr/src/app

VOLUME ["/usr/src/app/logs"]

COPY requirements.txt ./

RUN pip install -r requirements.txt

RUN mkdir -p logs && touch logs/guilds.log && ln -s logs/guilds.log guilds.log

# Bundle app source
COPY . .

CMD [ "sh", "-c", "python src/main.py" ]
