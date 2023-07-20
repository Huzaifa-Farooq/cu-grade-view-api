FROM python:3.9-slim-buster

WORKDIR /app

# Copy the requirements.txt first for better cache on later pushes
COPY ./requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the files
COPY . .

ENV FLASK_APP=app.py

# Expose port 5000
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
