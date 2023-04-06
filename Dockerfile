FROM python:bullseye
RUN apt update
RUN apt install -y exiftool
COPY main.py requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]