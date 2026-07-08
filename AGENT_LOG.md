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

---

> 后续实现期每完成一个 PLAN task 即追加一条（含 task 编号、subagent 片段/commit hash、人工修改、教训）。
