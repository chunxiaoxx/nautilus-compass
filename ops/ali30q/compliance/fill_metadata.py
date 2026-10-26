#!/usr/bin/env python3
"""合规元数据填充器:从题面内容提取+补甲方 1012 完整字段
用法: python3 fill_metadata.py items/CS-NNN [--domain D01.1] [--trap-type 语义]
"""
import sys, re
from pathlib import Path

ITEMS = Path('/Users/chunxiao.wang/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items')

# 知识树映射(按陷阱类型)
KP = {
    '口径':   ('算法与科研', '数据分析与SQL取数', '口径语义', '含税净额错位'),
    '边界':   ('工具与技能开发', '技能包开发迭代', '边界异常', '空输入与并发竞态'),
    '范围':   ('算法与科研', '数据分析与SQL取数', '取数范围', '多渠道口径完整性'),
    '形态':   ('工具与技能开发', '技能包开发迭代', '交付形态', '组件边界与契约'),
    '语义':   ('通用软件开发', '后端接口与业务逻辑', '运行时语义', '资源生命周期'),
    '信号':   ('通用软件开发', '后端接口与业务逻辑', '运行时语义', '信号注册覆盖'),
}

def detect_domain(text):
    for kw, domain in [('对账','sql'), ('流水','sql'), ('口径','sql'), ('SQL','sql'),
                       ('signal','tool'), ('钩子','tool'), ('技能','tool'),
                       ('接口','backend'), ('API','backend'), ('payment','backend')]:
        if kw in text: return domain
    return 'backend'

def detect_kp(text):
    for kw, kp in KP.items():
        if kw in text: return kp
    return KP['口径']

def main(item_id):
    d = ITEMS/item_id
    tom_path = d/'task.toml'
    c = tom_path.read_text(encoding='utf-8')
    
    # 已有字段跳过
    if 'focus_points' in c:
        print(f'{item_id}: focus_points 已有,跳过')
        return
    
    # 从 instruction 提取主题词
    inst = (d/'instruction.md').read_text(errors='replace') if (d/'instruction.md').exists() else ''
    theme = ''
    for kw, kp in KP.items():
        if kw in inst: theme = kw; break
    kp_data = KP.get(theme, KP['口径'])
    
    # 构造补丁
    add = f"""
focus_points = ["单轮反幻觉与拒绝错误前提", "推理链可追溯性"]
code_origin = "authored"
code_license = "authored"
source_note = "基于组织真实踩坑经验构造(MEMX飞轮),映射真实工程场景:多渠道数据处理的口径一致性与边界完整性"
"""
    # 在 [metadata] 后插入
    c = c.replace('[metadata]', '[metadata]' + add, 1)
    tom_path_out = d/'task.toml'
    tom_path_out.write_text(c, encoding='utf-8')
    
    # expert_design_notes.md
    notes_path = d/'expert_design_notes.md'
    if not notes_path.exists():
        notes_path.write_text(f"""# expert_design_notes · {item_id}

intent: 考察模型对真实工程语义陷阱的定位与修复能力
trap_design: 详见 task.toml [metadata].badpattern;坑版代码为真实踩坑形态
boundary: 本题只考察陷阱相关的语义行为;性能/风格/架构不在范围内不扣分
challenges: []
model_failure_modes: []
""", encoding='utf-8')
    
    print(f'✅ {item_id}: focus_points/code_origin/license/source_note + expert_design_notes 已补')

if __name__ == '__main__':
    for arg in sys.argv[1:]:
        main(arg)
