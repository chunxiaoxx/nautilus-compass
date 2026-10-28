FROM python:3.11-slim
WORKDIR /workspace/bin_packing_ffd_v1_001
COPY . .
RUN pip install --no-cache-dir -r requirements.txt || true
CMD ["python", "verification/evaluate.py", "--benchmark-dir", ".", "--candidate", "baseline/init.py"]