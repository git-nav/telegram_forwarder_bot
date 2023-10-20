FROM python:3

COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt

CMD [ "bash", "start.sh" ]
