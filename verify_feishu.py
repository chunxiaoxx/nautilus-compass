"""verify_feishu.py"""
import sys
sys.path.insert(0, "/home/ubuntu/fde-toolbox")
from feishu_client import read_bitable_records
APP = "KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe"; TBL = "tblQAW4aNM99nva6"
r = read_bitable_records(APP, TBL)
items = r.get("data",{}).get("items",[])
print(f"rows={len(items)}")
for it in items:
    f = it.get("fields",{})
    tid = f.get("task_id","?")
    verdict = f.get("held_out_verdict","?")
    print(f"  {tid}: held_out_verdict={verdict}")