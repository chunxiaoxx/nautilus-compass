# FDE 第三期领域拆仓（M0）：来源盘点与所有权清单

## 任务范围
- 对象：`FDE 第三期` 领域代码的所有权迁移。
- 目标：将领域规则与映射逻辑迁出为独立项目 `nautilus-fde-phase3`，维持 Bitable 为唯一业务事实，Core 为唯一受控写回者。
- 当前仅执行 `Task 1 (M0 Freeze)`：来源盘点与所有权映射，不新增、删除、移动文件，不写 Feishu，不接触线上业务记录。

## 冻结规则（M0）
1. 不再新增第三期业务规则的重复来源（Core/V5/Compass 任一侧）。
2. 不新增 Bitable 业务账本、凭证或原始记录副本。
3. 不在 M0 后在 Core、V5、Compass 写入任何新的第三期领域规则变体。
4. M0 清单提交后，仅允许在 `nautilus-fde-phase3` 中引入领域化实现，Core 保留网关与受控写回职责。

## 来源盘点与所有权（M0 快照）

### 直接引用项（实现计划要求）
| 源码路径 | 当前仓库可见性 | 当前所有者（现状） | 目标所有者 | 迁移方法 |
| --- | --- | --- | --- | --- |
| `C:\Users\chunx\Projects\nautilus-core\phase3\backend\services\fde_phase3_v3_actual_schema_mapping.py` | 在本次 Core 主工作树缺失；在 `.worktrees\fde-phase3-ops` 存在同名文件 | Core | nautilus-fde-phase3 | extract |
| `C:\Users\chunx\Projects\nautilus-core\phase3\backend\services\fde_phase3_v3_readback_projection.py` | 在本次 Core 主工作树缺失；在 `.worktrees\fde-phase3-ops` 存在同名文件 | Core | nautilus-fde-phase3 | extract |
| `C:\Users\chunx\Projects\nautilus-v5\fde_capsule\feishu\phase3_compass_exporter.py` | 当前 V5 工作区未发现该文件 | V5 | V5（无领域规则） | consumer-only |
| `C:\Users\chunx\Projects\nautilus-compass\gep\fde_v3_adapter.py` | 当前 Compass 工作区未发现该文件 | Compass | Compass（无领域规则） | consumer-only |
| `C:\Users\chunx\Projects\nautilus-compass\gep\import_receipt.py` | 当前 Compass 工作区未发现该文件 | Compass | Compass（无领域规则） | consumer-only |

### Phase3 域逻辑候选文件（本次基线快照）
| 源码路径 | 当前所有者 | 迁移方法 |
| --- | --- | --- |
| `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-ops\phase3\backend\services\fde_phase3_v3_actual_schema_mapping.py` | Core | extract |
| `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-ops\phase3\backend\services\fde_phase3_v3_readback_projection.py` | Core | extract |
| `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-ops\phase3\backend\services\fde_phase3_compass_receipt.py` | Core | remain |
| `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-ops\phase3\backend\services\fde_phase3_compass_v3_contract.py` | Core | remain |
| `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-ops\phase3\backend\services\fde_phase3_compass_v3_receipt.py` | Core | remain |
| `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-ops\phase3\backend\services\fde_phase3_feishu_runtime_contract.py` | Core | remain |
| `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-ops\phase3\backend\services\fde_phase3_t1_workbench_contract.py` | Core | remain |
| `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-ops\phase3\backend\services\fde_phase3_mentor_continuation_workflow.py` | Core | remain |
| `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-ops\phase3\backend\services\fde_phase3_question_precheck.py` | Core | remain |
| `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-ops\phase3\backend\services\fde_phase3_runtime_state.py` | Core | remain |
| `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-ops\phase3\backend\services\fde_phase3_two_stage_schema.py` | Core | remain |
| `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-ops\phase3\backend\services\fde_phase3_two_stage_migration.py` | Core | remain |

## 审计备注
- 上述表仅覆盖当前 M0 盘点的可见路径，不代表全部运行时依赖清单。
- 所有记录字段、业务附件、外链与凭证一律不写入该清单。
