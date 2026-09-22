FROM python:3.12-slim

WORKDIR /app

# System deps for WeasyPrint, pdfplumber, psycopg2, and NodeSource setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 libffi-dev libcairo2 \
    gcc libpq-dev curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install MathJax SSR converter (MathML → SVG for WeasyPrint)
COPY mathjax-convert/ /app/mathjax-convert/
RUN cd /app/mathjax-convert && npm install --omit=dev

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
