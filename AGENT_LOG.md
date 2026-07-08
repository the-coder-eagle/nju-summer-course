# AGENT_LOG.md

按时间顺序记录 AI4SE 项目 A 的关键节点(§4.9)。每条含:时间/序号、task 编号、触发的 Superpowers 技能、关键 prompt/context、subagent 输出或 commit、人工干预、教训。

---

### #1 · 2026-07-08 · 阶段:brainstorming(澄清需求)
- **Superpowers 技能**：superpowers:brainstorming
- **task**：无（brainstorming 前置）
- **关键 prompt/context**：用户给出两份要求文档（《项目 A · Coding Agent Harness》+《通用要求》），要求"做项目 A，先告诉我要做什么，再带着我逐步实现"。
- **关键决策（逐条问答）**：
  1. 主角维度 → 反馈闭环（§A.4-D）
  2. 实现语言 → Python
  3. LLM 抽象 → OpenAI 兼容；真实 provider → DeepSeek（首答"多做游戏兼容"系笔误，二次澄清后定）
  4. 目标场景 → A 测试修复竞技场（用户答前表示"不太了解"，我解释反馈闭环机制后选定）
  5. WebUI → Agent 流式控制台（§5.9）
  6. CI → NJU GitLab + `.gitlab-ci.yml`（文档 §4.8/§5 矛盾，澄清后从 §5）
  7. 架构 → ① 流水线反馈子系统
- **人工干预**：用户给定两条工作纪律并存入记忆：(a) 需要信息就问、不臆测，严格按作业要求；(b) 一次只开发一个能力并测试，不无端耦合。
- **commit**：无
- **教训**：作业文档内部矛盾（GitHub Actions vs `.gitlab-ci.yml`）必须向用户澄清，不能替其假设。

### #2 · 2026-07-08 · 阶段:SPEC
- **Superpowers 技能**：superpowers:brainstorming（写设计文档步）
- **task**：SPEC.md（§4.2 + §A.5 结构，11 节）
- **关键 prompt/context**：用户"帮我都做好完成" → 解读为推进全流程，越过逐节等待门。
- **产出**：SPEC.md（206 行）；自查通过（无占位符 / 无矛盾 / 范围聚焦 / 无歧义）。
- **commit**：1 — `docs: add SPEC.md + .gitignore`
- **人工干预**：无（用户授权推进）。
- **教训**：§A.4-C"移除真实 LLM 后仍可确定性单测"是整个设计的判据透镜；反馈流水线各级设计成纯函数正是为此。

### #3 · 2026-07-08 · 阶段:PLAN
- **Superpowers 技能**：superpowers:writing-plans
- **task**：PLAN.md（26 个 TDD task）
- **关键 prompt/context**：按"一次一个能力"把 26 个组件各成一个 task，标依赖与可并行。
- **产出**：PLAN.md（1610 行）；自查：SPEC 各节均有 task 覆盖、无占位符、类型一致（仅 T14 给 `State` 加 `escalated` 字段已标注）。
- **commit**：2 — `docs: add PLAN.md (26 TDD tasks, cold-start ready)`
- **人工干预**：用户"仓库还没说，先按公共仓库来；文档你也帮我带着写；要求改了"。
- **教训**：PLAN 的 task 颗粒度与用户"一次一个能力"纪律对齐，使 subagent 驱动开发天然契合。

### #4 · 2026-07-08 · 阶段:过程文档
- **Superpowers 技能**：—
- **task**：AGENT_LOG.md + SPEC_PROCESS.md
- **产出**：本文件 + SPEC_PROCESS.md（§4.4：≥3 轮迭代节选、AI 建议采纳/推翻、brainstorming 反思草稿；冷启动节待填）。
- **commit**：3 — `docs: add AGENT_LOG.md + SPEC_PROCESS.md`（本提交）
- **待办**：实现代码受 §4.5 冷启动门阻塞（需用户用不同 agent 跑 SPEC+PLAN）。

### #5 · 2026-07-08 · 阶段:冷启动验证（进行中）
- **Superpowers 技能**：—（§4.5 冷启动，第二 agent = OpenCode）
- **task**：—（验证 SPEC+PLAN 清晰度）
- **关键事件**：第二 agent 实现 T1/T2 时受阻，提问"导入路径设置在 T22，冷启动 T1/T2 如何 `import harness` 跑绿"。暴露 PLAN 排序缺口（脚手架晚于首个 task）。
- **修订**：PLAN 插入 **Task 0**（scaffolding / import-path：`pyproject.toml` pythonpath + `src/harness/__init__.py` + `tests/conftest.py` + sanity test）；T22 改为"扩展 pyproject + Makefile"；依赖注更新为 Task 0 前置。同步更新 `SPEC_PROCESS.md` §4.5。
- **commit**：4 — `docs: fix PLAN ordering — add Task 0 scaffolding`
- **教训**：脚手架/构建配置是所有 task 的隐性前置，必须显式成 task 放最前，否则冷启动与 subagent 在 T1 即卡。

### #6 · 2026-07-08 · 阶段:冷启动验证（进行中）
- **Superpowers 技能**：—（§4.5 冷启动，第二 agent = OpenCode）
- **task**：—（验证 SPEC+PLAN）
- **关键事件**：第二 agent 在 T1 TDD 途中又报两处 plan 缺口：①默认 `python` 3.10.11 低于 PLAN 的 ≥3.11 门槛；②pytest 默认未装，而依赖安装排在 T22。同时确认 T1 可按 PLAN 逐字实现并红→绿（T1 spec 清晰度 OK）。
- **修订**：Python 门槛降为 ≥3.10（Global Constraints + 两处 `requires-python`）；Task 0 增 `pip install pytest` 步。完整 dev-deps-in-Task-0 重构延至真实实现期。SPEC_PROCESS §4.5 补发现 2、3。
- **commit**：5 — `docs: lower Python floor to 3.10 + install pytest in Task 0 (cold-start findings 2&3)`
- **教训**：版本门槛要对齐代码实际最低特性；共享依赖安装要前置到 setup task。

### #7 · 2026-07-08 · 阶段:冷启动验证（完成）→ 转真实实现
- **Superpowers 技能**：§4.5 冷启动完成；下一步 subagent-driven-development / executing-plans。
- **task**：冷启动由第二 agent（OpenCode）实现 Task 0/1/2（commits `fb438e1`/`f518e94`/`83e1a16`，3 tests green，逐字照搬 PLAN）。
- **关键事件**：冷启动共报 6 处缺口（详见 SPEC_PROCESS §4.5）。已修 6 处（Task0 导入、Python→3.10、pytest 安装、`__init__` 归属、Task1 未用 `field` import、`.gitattributes`）；跟进 1（venv 固定 `make test` 环境）。
- **修订**：修 PLAN Task 1（去未用 import）；加 `.gitattributes`；SPEC_PROCESS §4.5 写冷启动完成报告；仓库加完整 `pyproject.toml`（含 build-system）作真实 Task 0 环境。
- **commit**：docs(冷启动完成+修复) + code(pyproject + actions.py import fix)
- **教训**：冷启动在 T1 即撞穿 3 处隐性前置缺口——"setup 必须显式成最前 task"。真实实现期改 worktree/MR（待 NJU remote）。

---

> 后续实现期每完成一个 PLAN task 即追加一条（含 task 编号、subagent 片段/commit hash、人工修改、教训）。
