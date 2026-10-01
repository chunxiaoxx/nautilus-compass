from huggingface_hub import snapshot_download

snapshot_download("Qwen/Qwen3.5-9B", local_dir="/home/ubuntu/models/qwen35-9b")
print("QWEN_CLOUD_DONE")
