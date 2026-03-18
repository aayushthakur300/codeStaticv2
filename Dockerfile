# # 1. Use an official lightweight Python image
# FROM python:3.13-slim

# # 2. Set the working directory inside the container
# WORKDIR /app

# # 3. Copy the dependencies file first (for caching speed)
# # (Make sure you have generated a requirements.txt!)
# COPY requirements.txt .

# # 4. Install dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # 5. Copy the rest of your application code
# COPY . .

# # 6. Expose the port your app runs on (You use 10000)
# EXPOSE 10000

# # 7. The command to run your app
# # Since you use "python run.py" to start, we use that here.
# CMD ["python", "run.py"]

# 1. Use an official lightweight Python image
FROM python:3.12-slim

# 2. Set the working directory inside the container
WORKDIR /app

# --- THE FIX: Install required system dependencies for your heavy packages ---
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
# -----------------------------------------------------------------------------

# 3. Copy the dependencies file first (for caching speed)
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code
COPY . .

# 6. Expose the port your app runs on
EXPOSE 10000

# 7. The command to run your app
CMD ["python", "run.py"]