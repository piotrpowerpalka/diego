FROM python:3.12

WORKDIR /app
COPY . /app

# ! SPADE lib above v3.3.3 is not working with this implementation
RUN pip install spade==3.3.3 
RUN pip install numpy
RUN pip install pandas
#RUN pip install openpyxl
#RUN pip install xlrd

RUN chmod +x main.py
CMD python -u main.py
