FROM python:3.9

RUN git clone https://github.com/LDAP/Sync2CalDav /app
RUN pip install -r /app/requirements.txt

CMD python /app/main.py
