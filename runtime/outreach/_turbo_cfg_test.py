import transformers
print("transformers:", transformers.__version__)
from transformers import AutoConfig
cfg = AutoConfig.from_pretrained("/root/vdd2/models/Qwen3.8-14B-Turbo")
print("cfg_ok:", cfg.model_type, "| layers:", getattr(cfg, "num_hidden_layers", "?"))
print("AutoModelForCausalLM import ok")
