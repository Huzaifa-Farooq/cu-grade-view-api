FROM python:3.9-slim-buster

WORKDIR /app

# Copy the requirements.txt first for better cache on later pushes
COPY ./requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the files
COPY . .

ENV FLASK_APP=app.py
ENV FLASK_DEBUG=True
ENV FLASK_RUN_HOST="0.0.0.0"
ENV FLASK_RUN_PORT=2000

# Expose port 2000
EXPOSE 2000

# Run the application
CMD ["flask", "run"]
