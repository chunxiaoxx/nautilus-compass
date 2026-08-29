"""Download e2e 500 results tarball from GPU via paramiko sftp."""
import sys
sys.path.insert(0, "vtf")
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.32", 10516, username="root", password="ieco7Xah", timeout=20)
s = c.open_sftp()
s.get("/root/e2e_results_500.tar.gz", "docs/evidence/e2e_500_gpu_20260829.tar.gz")
print("DOWNLOADED")
c.close()
