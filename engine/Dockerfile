# Base image with Java (needed for apktool + apksigner)
FROM eclipse-temurin:17-jdk-jammy

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    curl \
    unzip \
    zipalign \
    apksigner \
    && rm -rf /var/lib/apt/lists/*

# Create tools directory
RUN mkdir -p /tools

# Download apktool
RUN wget -q https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool \
    -O /usr/local/bin/apktool && chmod +x /usr/local/bin/apktool

RUN wget -q https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar \
    -O /tools/apktool.jar

# Download uber-apk-signer
RUN wget -q https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar \
    -O /tools/uber-apk-signer.jar

# Set working directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy engine source code
COPY . .

# Expose port
EXPOSE 8000

# Start FastAPI engine
CMD ["python3", "main.py"]
