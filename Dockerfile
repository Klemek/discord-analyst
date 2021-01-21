FROM python

# Create app directory
WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install -r requirements.txt

# Bundle app source
COPY . .

CMD [ "sh", "-c", "python src/main.py" ]
