"""List S3 delivery table fields via cloud (anchor #5 复用 feishu_client)."""

import sys
sys.path.insert(0, "/home/ubuntu")
import feishu_client
import urllib.request
import json

tok = feishu_client.tenant_token()
print(f"token: {tok[:6]}...")

# 1. list tables in Dx2qb base
tables = feishu_client.list_bitable_tables("Dx2qb1fjhaJadSs0ZeMc0teVn49", tok)
print("tables:", tables)

# 2. list fields of tblFkmEKTk4LIWJM
url = "https://open.feishu.cn/open-apis/bitable/v1/apps/Dx2qb1fjhaJadSs0ZeMc0teVn49/tables/tblFkmEKTk4LIWJM/fields"
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok})
with urllib.request.urlopen(req, timeout=20) as r:
    data = json.loads(r.read())
print("fields:")
for f in data.get("data", {}).get("items", []):
    print(f"  field_name={f.get('field_name')!r}  type={f.get('type')}  uid={f.get('field_id')}")