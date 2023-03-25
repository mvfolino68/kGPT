# Image from dockerhub
FROM python:3.8.1-buster

ENV PYTHONUNBUFFERED 1 

# Make /app as a working directory in the container
WORKDIR /app

# Copy everything from ./src directory to /app in the container
COPY . .
# Install the dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Expose the required port
EXPOSE 9000

# Run the application in the port 9000
CMD ["uvicorn", "main:app", "--reload", "--port", "9000","--host", "0.0.0.0"]

