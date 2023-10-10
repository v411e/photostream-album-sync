FROM python:bullseye
RUN apt update
RUN apt install -y exiftool
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
COPY photostream-album-sync /app/photostream-album-sync/
CMD ["python", "photostream-album-sync/main.py"]