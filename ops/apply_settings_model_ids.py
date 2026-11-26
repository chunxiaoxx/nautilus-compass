#!/usr/bin/env python3
"""settings.json:去掉模型名里的 [1M]/[1m] 后缀 + 加 CLAUDE_CODE_AUTO_COMPACT_WINDOW。

为什么(2026-11-26 实测):
  - 带后缀的模型名在智谱网关侧是无效 ID:流式 /v1/messages 直接报 1211「模型不存在」,
    /v1/messages/count_tokens 返回 input_tokens=0;去掉后缀两者都正常(同一文本 413)。
    Claude Code 2.1.325 发消息时会自己剥掉后缀,所以会话一直能跑;count_tokens 是否也剥,外部无法确认。
  - 智谱官方文档:后缀是给旧版 Claude Code 识别 1M 窗口用的;用 GLM-5.4 建议
    CLAUDE_CODE_AUTO_COMPACT_WINDOW=512000(本机此前没有,会话曾涨到 65.9 万 token 才压缩)。
只改 env 里这几个键;先备份;不打印任何凭据;只对新开的会话生效。
用法:python ops/apply_settings_model_ids.py [--dry-run]
"""
import argparse
import json
import os
import pathlib
import shutil
import sys

MODEL_KEYS = ("ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
              "ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_FABLE_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL")
COMPACT_WINDOW = "512000"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    path = pathlib.Path.home() / ".claude" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    env = dict(data.get("env") or {})
    changes = {}
    for key in MODEL_KEYS:
        value = env.get(key)
        if isinstance(value, str) and value.rstrip().endswith("]") and "[" in value:
            stripped = value.split("[", 1)[0].strip()
            env[key] = stripped
            changes[key] = [value, stripped]
    if "CLAUDE_CODE_AUTO_COMPACT_WINDOW" not in env:
        env["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = COMPACT_WINDOW
        changes["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = [None, COMPACT_WINDOW]
    print(json.dumps({"file": str(path), "changes": changes}, ensure_ascii=False, indent=1))
    if args.dry_run or not changes:
        return 0
    backup = path.with_name("settings.json.bak-20261126-model-ids")
    shutil.copy2(path, backup)
    updated = dict(data)
    updated["env"] = env
    content = (json.dumps(updated, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    json.loads(content.decode("utf-8"))  # 写前校验
    tmp = path.with_name("settings.json.tmp")
    try:
        tmp.write_bytes(content)
        try:
            os.replace(tmp, path)
            how = "replace"
        except PermissionError:
            # 运行中的 Claude Code 占着文件,改名替换被 Windows 拒绝 → 就地写。
            # 以 r+b 打开:打开被拒则原文件一字不动(不会先截断)。
            with open(path, "r+b") as handle:
                handle.seek(0)
                handle.write(content)
                handle.truncate()
                handle.flush()
                os.fsync(handle.fileno())
            how = "in-place"
    except Exception:
        # 临时文件含凭据,任何失败都要清掉再抛
        if tmp.exists():
            tmp.unlink()
        raise
    tmp.unlink(missing_ok=True)  # 走了 os.replace 分支时临时文件已不存在
    print(json.dumps({"applied": True, "how": how, "backup": backup.name}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
