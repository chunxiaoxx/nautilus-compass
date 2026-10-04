from modelscope import snapshot_download

p = snapshot_download('Qwen/Qwen2.5-VL-3B-Instruct')
print('DL_DONE', p)
