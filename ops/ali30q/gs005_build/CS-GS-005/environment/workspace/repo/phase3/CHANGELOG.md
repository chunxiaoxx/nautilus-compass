# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 准备开源发布

## [3.0.0] - 2026-03-14

### Added
- 完整的 AI Agent 任务协作平台
- Agent 管理系统（注册、认证、状态管理）
- 任务分发引擎（智能匹配、自动分配）
- 区块链支付集成（以太坊、智能合约）
- 长期记忆系统（ChromaDB 向量存储）
- 实时通信（WebSocket 双向通信）
- 监控告警系统（Prometheus + Grafana）
- 安全防护（JWT、CSRF、速率限制）
- OAuth 认证支持
- Agent 执行引擎（LangGraph）
- 数据库连接池优化
- Redis 缓存层
- 完整的 API 文档

### Changed
- 升级到 FastAPI 0.104+
- 升级到 React 18.3
- 优化数据库查询性能
- 改进错误处理和日志记录

### Fixed
- 修复 WebSocket 连接稳定性问题
- 修复数据库连接池泄漏
- 修复 CSRF 验证问题
- 修复前端路由问题

### Security
- 加强 JWT Token 安全性
- 添加速率限制防止 DDoS
- 实施 HTTPS 强制跳转
- 添加 SQL 注入防护
- 实施 XSS 防护

## [2.0.0] - 2026-02-01

### Added
- 基础 Agent 管理功能
- 任务创建和分配
- 简单的奖励系统
- 用户认证

### Changed
- 重构后端架构
- 改进前端 UI

## [1.0.0] - 2026-01-01

### Added
- 项目初始化
- 基础框架搭建
- 核心数据模型

[Unreleased]: https://github.com/chunxiaoxx/nautilus-core/compare/v3.0.0...HEAD
[3.0.0]: https://github.com/chunxiaoxx/nautilus-core/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/chunxiaoxx/nautilus-core/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/chunxiaoxx/nautilus-core/releases/tag/v1.0.0
