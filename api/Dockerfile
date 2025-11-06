FROM python:3.12-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルを先にコピー（レイヤーキャッシュの最適化）
COPY api/requirements.txt /app/api/requirements.txt

# 依存関係をインストール（requirements.txtが変更されない限りキャッシュされる）
WORKDIR /app/api
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードとデータをコピー
COPY api/main.py /app/api/
COPY api/run.py /app/api/
COPY notebooks/ /app/notebooks/
COPY data/ /app/data/

# ポート設定（Cloud Runは自動的に$PORTを設定）
ENV PORT=8080

# ポートを公開（Cloud Runでは必須ではないが、ベストプラクティス）
EXPOSE 8080

# Pythonパスを設定
ENV PYTHONPATH=/app/api:/app/notebooks:$PYTHONPATH

# 作業ディレクトリを設定（apiディレクトリに）
WORKDIR /app/api

# アプリケーションを起動
CMD ["python", "/app/api/run.py"]

