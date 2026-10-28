# 压力测试结果目录

此目录用于存储压力测试的结果文件。

## 文件类型

- `*.html` - HTML格式的测试报告
- `*_stats.csv` - 统计数据CSV文件
- `*_failures.csv` - 失败请求记录
- `*_exceptions.csv` - 异常记录

## 文件命名规则

格式: `production_{scenario}_{timestamp}.{ext}`

示例:
- `production_light_20260227_143000.html`
- `production_medium_20260227_143000_stats.csv`

## 注意事项

- 测试结果文件会自动生成
- 建议定期清理旧的测试结果
- 重要的测试结果应该备份到其他位置
