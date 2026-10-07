#!/usr/bin/env bash
# 一体化:杀旧→端口 19987→起守护循环→自证
pkill -f tunnel_daemon 2>/dev/null
pkill -f 'ssh -NR' 2>/dev/null
sleep 2
sed -i 's/1998[0-9]/19987/g' /root/vdd4/tunnel_daemon.sh
nohup bash /root/vdd4/tunnel_daemon.sh > /root/vdd4/tunnel.log 2>&1 &
echo "launcher_pid=$!"
sleep 15
echo "ssh_procs=$(ps aux | grep 'ssh -NR 19987' | grep -v grep | wc -l)"
echo "loop_procs=$(ps aux | grep 'tunnel_daemon' | grep -v grep | wc -l)"
tail -2 /root/vdd4/tunnel.log
