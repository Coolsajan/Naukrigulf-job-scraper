# Use the official Apify image that has Chrome and Python pre-installed
FROM apify/actor-python-selenium:latest

# Copy requirements and install them
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . ./

# Run your script
CMD ["python3", "main.py"]