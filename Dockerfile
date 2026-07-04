FROM eclipse-temurin:17-jdk-jammy

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    curl \
    unzip \
    zipalign \
    apksigner \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tools

RUN wget -q https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar \
    -O /tools/apktool.jar

RUN wget -q https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar \
    -O /tools/uber-apk-signer.jar

WORKDIR /app

COPY engine/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY engine/ .

EXPOSE 8000

CMD ["python3", "main.py"]
