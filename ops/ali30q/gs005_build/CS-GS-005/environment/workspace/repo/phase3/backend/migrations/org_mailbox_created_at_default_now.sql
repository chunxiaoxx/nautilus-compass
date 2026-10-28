-- 2026-10-04 org_mailbox.created_at 时钟统一(根修配套 DDL)
-- 背景:default=datetime.utcnow(模型路径)早8h + 表无 DEFAULT → server_default 改后 NULL 回归
-- 修正:表级 DEFAULT now(),全路径统一 DB 钟。已在生产执行(探针偏差 0.19s 验证)。
ALTER TABLE org_mailbox ALTER COLUMN created_at SET DEFAULT now();
-- 附:修复 NULL 残留(若有)
-- UPDATE org_mailbox SET created_at = now() WHERE created_at IS NULL;
