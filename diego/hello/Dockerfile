FROM python:3.10

WORKDIR /app
COPY . /app

RUN pip install spade
RUN pip install numpy
RUN pip install pandas
#RUN pip install openpyxl
#RUN pip install xlrd

RUN chmod +x main.py
CMD python -u main.py
