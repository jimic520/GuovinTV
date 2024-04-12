FROM python:3.8
RUN pip install -r requirements.txt
EXPOSE 8989
WORKDIR /
CMD ["python", "app.py"]
