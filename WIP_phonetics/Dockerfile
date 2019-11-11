FROM python:3.7
COPY requirements.txt .
RUN pip3 install -r requirements.txt

RUN mkdir /code
COPY code/uri_synonames.py code/synonames_helper.py /code/

WORKDIR /code
CMD [ "python", "uri_synonames.py" ]