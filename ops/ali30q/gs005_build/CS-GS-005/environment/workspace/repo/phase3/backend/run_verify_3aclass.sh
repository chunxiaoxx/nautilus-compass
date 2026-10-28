#!/bin/bash
# Verify 3 A-class on GPU (soul canonical turf)
# Output: /home/ubuntu/verify_3aclass_<ts>.log

TS=$(date +%Y%m%d_%H%M%S)
LOG=/home/ubuntu/verify_3aclass_${TS}.log

echo "===START $(date)===" | tee $LOG

echo "" | tee -a $LOG
echo "===VERIFY_DJANGO_12113===" | tee -a $LOG
python3 /home/ubuntu/verify_aclass.py django__django-12113 /home/ubuntu/swe_aclass_fuel.jsonl 2>&1 | tee -a $LOG
echo "" | tee -a $LOG
echo "===VERIFY_DJANGO_13220===" | tee -a $LOG
python3 /home/ubuntu/verify_aclass.py django__django-13220 /home/ubuntu/swe_aclass_fuel.jsonl 2>&1 | tee -a $LOG
echo "" | tee -a $LOG
echo "===VERIFY_SKLEARN_10297===" | tee -a $LOG
python3 /home/ubuntu/verify_aclass.py scikit-learn__scikit-learn-10297 /home/ubuntu/swe_aclass_fuel_verified_20260629_163936.jsonl 2>&1 | tee -a $LOG
echo "" | tee -a $LOG
echo "===END $(date)===" | tee -a $LOG
echo "LOG=$LOG"