---
name: Exam signup (Nautilus Assay)
about: Sign up for the open-day exam — free trial round (limited slots, feedback wanted)
labels: exam-signup
---

**Tier**: [FREE trial (open-day, limited — feedback required) / Standard $99 / Deep $299]

**What you want tested**: e.g. "SWE bug-fix capability of my agent/CLI/tool, on real tasks with preregistered criteria"

**Integration mode**: [URL to repo+branch / paste starter code / we pick from public task list]

**Contact**: (email for the exam packet and scorecard — or leave blank to use your GitHub noreply)

**Feedback consent**: [OK to publish anonymized scorecard on the wall / private only]

## 考试密钥(报名即办 · 3 分钟 · 承 NMACS 案 A)

交卷身份全靠它,双向非抵赖(你签的名只有你的私钥能签;我们发的判分单由平台公钥可验):

1. **生成**(本地执行,私钥永不离开你的机器):
   ```
   ssh-keygen -t ed25519 -C "nmacs-<你的GitHub用户名>" -f ~/.nmacs/id_ed25519
   ```
   (Windows PowerShell / macOS / Linux 同命令;已有 Ed25519 对可直接复用)
2. **提交**:把 `~/.nmacs/id_ed25519.pub` 的全部内容贴到下方 code block——公钥公开=可审计;
   我们会回帖登记指纹(`sha256(公钥)前 16 位)` 并标注「报名密钥已登记」
3. **验签握手**:首个交卷物带 Ed25519 签名 → 平台用你登记的公钥验签,通过即身份绑定完成

> ⚠️ **永远不要**把私钥(`~/.nmacs/id_ed25519`,无 `.pub` 后缀那个文件)贴进任何 issue / 邮件 / 截图。需要它时只在本地签名。

**Ed25519 public key**(贴 `.pub` 文件全文):
```

```

---
By signing up you agree to the public protocol (preregistered criteria, blind grading, §5b challenge window — including challenging us): https://github.com/chunxiaoxx/nautilus-compass/blob/main/docs/protocol/ASSAY_PROTOCOL_V0.md
Trial round: signed scorecard included; misjudgment → full refund + public correction (single-case cap ≤ 2× service fee).
