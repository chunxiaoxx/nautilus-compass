FROM python:3.11-slim
WORKDIR /workspace/qaoa_maxcut_v1_001
COPY . .
RUN pip install --no-cache-dir -r requirements.txt || true
CMD ["python", "verification/evaluate.py", "--benchmark-dir", ".", "--candidate", "baseline/init.py"]