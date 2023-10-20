FROM okteto/python

COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt

CMD [ "bash", "start.sh" ]
