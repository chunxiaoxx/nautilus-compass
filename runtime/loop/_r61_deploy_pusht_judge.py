"""R61 部署 pusht 四窗判读脚本并执行(SFTP+运行+回读关键段)。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="A100_PW_ENV", timeout=10)
sftp = c.open_sftp()
sftp.put("tools/pusht_4win_judge_v1.py", "/root/pusht_4win_judge_v1.py")
sftp.close()
print("[deploy] /root/pusht_4win_judge_v1.py")
_, out, err = c.exec_command(
    "python3 /root/pusht_4win_judge_v1.py >/tmp/p4j.out 2>/tmp/p4j.err;"
    "python3 -c \"import json; v=json.load(open('/root/vdd3/pipe_art/pusht_4win_verdict.json'));"
    "print(v['ts'], v['judge']);"
    "print('verdict:', v['verdict'][:240]);"
    "print('noise_floor:', v['noise_floor_check']['verified']);"
    "print('clean p:', v['comparisons']['clean_A1N_vs_A2F']['p_two_sided'],"
    "'adapter p:', v['comparisons']['adapter_A1O_vs_A1N']['p_two_sided'])\";"
    "tail -1 /tmp/p4j.err", timeout=60)
print(out.read().decode())
c.close()
