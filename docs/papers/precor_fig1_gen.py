#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRECOR 短文 Figure 1 生成器(R332 主件):漂移-量化强度图(SVG,论文用)。
输出 docs/papers/precor_fig1.svg。"""
from pathlib import Path

# 数据 [实测](PRECOR_BC_VERDICT)
DATA = [
    ("fp16",  1.0000, 0),
    ("int8",  0.9828, 2),
    ("int4-nf4", 0.9416, 17),
]
GATE = 0.99

W, H = 640, 300
ML, MB, MT = 70, 60, 30
ymin, ymax = 0.90, 1.005
bw = 90

def y(v):
    return MT + (ymax - v) / (ymax - ymin) * (H - MB - MT)

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Helvetica,Arial,sans-serif" font-size="13">']
# 轴
svg.append(f'<line x1="{ML}" y1="{MT-8}" x2="{ML}" y2="{H-MB}" stroke="#333" stroke-width="1.2"/>')
svg.append(f'<line x1="{ML}" y1="{H-MB}" x2="{W-20}" y2="{H-MB}" stroke="#333" stroke-width="1.2"/>')
# y 刻度
for t in [0.90, 0.93, 0.96, 0.99, 1.00]:
    ty = y(t)
    svg.append(f'<line x1="{ML-5}" y1="{ty}" x2="{ML}" y2="{ty}" stroke="#333"/>')
    svg.append(f'<text x="{ML-8}" y="{ty+4}" text-anchor="end" fill="#333">{t:.2f}</text>')
# 门线
gy = y(GATE)
svg.append(f'<line x1="{ML}" y1="{gy}" x2="{W-20}" y2="{gy}" stroke="#b02a2a" stroke-dasharray="6,4" stroke-width="1.3"/>')
svg.append(f'<text x="{W-24}" y="{gy-6}" text-anchor="end" fill="#b02a2a" font-size="12">preregistered gate ≥ 99%</text>')
# 柱
for i, (name, agree, flips) in enumerate(DATA):
    x = ML + 60 + i * 160
    bh = H - MB - y(agree)
    color = "#0a7d32" if agree >= GATE else "#b02a2a"
    svg.append(f'<rect x="{x}" y="{y(agree)}" width="{bw}" height="{bh}" fill="{color}" fill-opacity="0.82"/>')
    svg.append(f'<text x="{x+bw/2}" y="{y(agree)-8}" text-anchor="middle" fill="#16213e" font-weight="bold">{agree:.4f}</text>')
    if flips:
        svg.append(f'<text x="{x+bw/2}" y="{y(agree)-26}" text-anchor="middle" fill="#666" font-size="11">{flips} label flips</text>')
    svg.append(f'<text x="{x+bw/2}" y="{H-MB+20}" text-anchor="middle" fill="#333">{name}</text>')
# 轴标签
svg.append(f'<text x="18" y="{(MT+H-MB)//2}" transform="rotate(-90 18 {(MT+H-MB)//2})" text-anchor="middle" fill="#333">Label agreement vs bf16 anchor (n=291)</text>')
svg.append(f'<text x="{ML+(W-20-ML)//2}" y="{H-12}" text-anchor="middle" fill="#333">Post-training quantization</text>')
svg.append('</svg>')

out = Path('docs/papers/precor_fig1.svg')
out.write_text("\n".join(svg), encoding='utf-8')
print(f'fig1 written: {out} ({out.stat().st_size} bytes)')
