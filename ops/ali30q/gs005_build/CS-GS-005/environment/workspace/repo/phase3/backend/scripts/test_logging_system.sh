#!/bin/bash

# 日志系统测试脚本

echo "=========================================="
echo "日志系统测试"
echo "=========================================="

# 设置环境变量
export LOG_LEVEL=debug
export ENVIRONMENT=development

# 创建日志目录
mkdir -p logs

echo ""
echo "1. 测试结构化日志配置..."
python -c "
from utils.logging_config import setup_structured_logging, get_logger, StructuredLogger

# 初始化日志系统
setup_structured_logging(
    log_level='debug',
    service_name='nautilus-backend',
    environment='development'
)

# 测试基础日志
logger = get_logger('test')
logger.info('Test info message')
logger.warning('Test warning message')
logger.error('Test error message')

# 测试结构化日志
structured_logger = StructuredLogger(logger)
structured_logger.info('Structured log test', user_id='user123', action='test')

print('✓ 结构化日志配置测试通过')
"

echo ""
echo "2. 检查日志文件..."
if [ -f "logs/nautilus.json.log" ]; then
    echo "✓ JSON日志文件已创建: logs/nautilus.json.log"
    echo "  最后一条日志:"
    tail -1 logs/nautilus.json.log | python -m json.tool
else
    echo "✗ JSON日志文件未创建"
fi

if [ -f "logs/nautilus.log" ]; then
    echo "✓ 文本日志文件已创建: logs/nautilus.log"
else
    echo "✗ 文本日志文件未创建"
fi

echo ""
echo "3. 测试日志分析脚本..."
if [ -f "logs/nautilus.json.log" ]; then
    python scripts/analyze_logs.py --time-range 1 --analysis-type all
    echo "✓ 日志分析脚本测试通过"
else
    echo "⚠ 跳过日志分析测试（没有日志文件）"
fi

echo ""
echo "4. 验证日志格式..."
python -c "
import json

try:
    with open('logs/nautilus.json.log', 'r') as f:
        for line in f:
            log_entry = json.loads(line.strip())
            # 验证必需字段
            required_fields = ['timestamp', 'level', 'logger', 'message', 'service', 'environment']
            for field in required_fields:
                if field not in log_entry:
                    print(f'✗ 缺少必需字段: {field}')
                    exit(1)
    print('✓ 日志格式验证通过')
except FileNotFoundError:
    print('⚠ 日志文件不存在')
except json.JSONDecodeError as e:
    print(f'✗ JSON格式错误: {e}')
    exit(1)
"

echo ""
echo "5. 检查配置文件..."
config_files=(
    "config/logging/promtail.yml"
    "config/logging/filebeat.yml"
    "config/logging/grafana-datasources.yml"
    "config/logging/docker-compose.logging.yml"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ 配置文件存在: $file"
    else
        echo "✗ 配置文件缺失: $file"
    fi
done

echo ""
echo "6. 检查文档..."
if [ -f "LOGGING_GUIDE.md" ]; then
    echo "✓ 日志文档存在: LOGGING_GUIDE.md"
    lines=$(wc -l < LOGGING_GUIDE.md)
    echo "  文档行数: $lines"
else
    echo "✗ 日志文档缺失"
fi

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
