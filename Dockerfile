FROM python:3.9-slim-buster

WORKDIR /app

# Copy the requirements.txt first for better cache on later pushes
COPY ./requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the files
COPY . .

ENV FLASK_APP=app.py

# Expose port 2000
EXPOSE 2000

# Run the application
CMD ["flask", "run", "-host=0.0.0.0"]
