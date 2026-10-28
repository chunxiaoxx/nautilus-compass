#!/bin/bash
# Agent进度监控脚本

echo "==================================="
echo "🤖 团队模式 - Agent进度监控"
echo "==================================="
echo ""

AGENT1="C:/Users/chunx/AppData/Local/Temp/claude/C--Windows-System32/tasks/a21bcf826eb3f8aa9.output"
AGENT2="C:/Users/chunx/AppData/Local/Temp/claude/C--Windows-System32/tasks/a86515eee5bd5d944.output"
AGENT3="C:/Users/chunx/AppData/Local/Temp/claude/C--Windows-System32/tasks/ad98ff0de41cc6c5c.output"

echo "📊 Agent 1: 安全修复专家"
echo "任务: 修复P1安全问题"
echo "输出文件: $AGENT1"
if [ -f "$AGENT1" ]; then
    LINES=$(wc -l < "$AGENT1")
    echo "输出行数: $LINES"
    if [ $LINES -gt 0 ]; then
        echo "最新输出:"
        tail -5 "$AGENT1"
    else
        echo "状态: 初始化中..."
    fi
else
    echo "状态: 未启动"
fi
echo ""

echo "📊 Agent 2: 架构实现专家"
echo "任务: 执行Week 5计划"
echo "输出文件: $AGENT2"
if [ -f "$AGENT2" ]; then
    LINES=$(wc -l < "$AGENT2")
    echo "输出行数: $LINES"
    if [ $LINES -gt 0 ]; then
        echo "最新输出:"
        tail -5 "$AGENT2"
    else
        echo "状态: 初始化中..."
    fi
else
    echo "状态: 未启动"
fi
echo ""

echo "📊 Agent 3: 测试工程专家"
echo "任务: 补充测试到80%"
echo "输出文件: $AGENT3"
if [ -f "$AGENT3" ]; then
    LINES=$(wc -l < "$AGENT3")
    echo "输出行数: $LINES"
    if [ $LINES -gt 0 ]; then
        echo "最新输出:"
        tail -5 "$AGENT3"
    else
        echo "状态: 初始化中..."
    fi
else
    echo "状态: 未启动"
fi
echo ""

echo "==================================="
echo "更新时间: $(date)"
echo "==================================="
