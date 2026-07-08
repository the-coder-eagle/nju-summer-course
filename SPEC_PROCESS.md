# SPEC_PROCESS.md

记录与 Superpowers 协作生成 spec 与 plan 的过程（§4.4）。

## 1. brainstorming 关键节点与好问题

brainstorming 技能强制"一次一个问题"，逼出了若干关键决策；其中最有价值的追问：

- **"主角维度选哪个？"** —— 迫使我在六维度里选一个做深（§A.4-D），而不是摊大饼。用户选反馈闭环，后续设计全部围绕它。
- **"真实 LLM 接哪家？"** —— 暴露了抽象层应 OpenAI 兼容这一设计点；用户首答含糊，二次澄清后定 DeepSeek。
- **"目标场景是什么？"** —— 用户表示不懂，我借机把"反馈闭环闭环在什么上"讲透（含 mock 确定性演示），用户随即选 A。这一轮让我意识到 SPEC 必须把"反馈闭环如何工作"写到冷启动 agent 能直接照做。
- **"CI 用哪个？"** —— 我主动暴露文档矛盾（§4.8 GitHub Actions vs §5 `.gitlab-ci.yml`），用户定 NJU GitLab。

## 2. ≥3 轮关键迭代对话节选与处理决策

**轮次 1 — 主角维度**
- 我问："六维度都有最低实现，但选一个做深……你想把哪个作为主角？" 选项含反馈闭环 / 治理 / 扩展 / 记忆。
- 用户答："反馈闭环（推荐）"。
- 处理：采纳。后续 SPEC §3.5 与 §11 围绕反馈流水线做深；治理 / 记忆设为最低实现。

**轮次 2 — 真实 LLM provider（含澄清）**
- 我问："真实运行时接哪家 LLM？"
- 用户首答："多做游戏兼容？"（笔误 / 语音转写）。
- 处理：不臆测。按"需要就问"纪律，我说明这句没读懂，重新给选项。用户二次答："DeepSeek"。
- 教训：模糊输入必须澄清，不能猜。

**轮次 3 — 目标场景（含解释）**
- 我问："harness 的目标场景是什么？"（A 竞技场 / B TDD 实现 / C 通用助手）
- 用户答："我不太了解，解释一下。"
- 处理：我用 `add` 例子讲清主循环、反馈闭环、mock 确定性演示，再问。用户答："a"（= A）。
- 教训：用户不熟悉时先教后选；解释本身也成了 SPEC/PLAN 的素材。

**轮次 4 — 架构方案**
- 我问："harness 内核用哪种架构？"（①流水线反馈子系统 / ②事件溯源 / ③插件化）
- 用户答："①"。
- 处理：采纳 ①；②作为二期增强（给 Compose 加事件日志即可拿 replay），不另立架构。

## 3. AI 建议采纳 vs 推翻

**采纳的 AI 建议**：
- LLM 抽象层面向 OpenAI 兼容接口（可换 base_url/key，mock 可注）——用户认可。
- WebUI 分阶段（内核 → HTTP → 流式），内核不 import 任何 web 框架——契合"不无端耦合"。
- 我对照作业查出的 7 个补丁（HITL 状态机、沙箱防逃逸、多信号反馈、凭据 CLI 流程、机制演示交付物、CI 构建镜像、领域机制节）——全部折进 SPEC/PLAN。
- 凭据用 Windows Credential Manager + `.env` 回退；分发用 Docker；部署 Render/Fly.io——用户默认采纳未异议。

**推翻 / 修正的 AI 建议**：无重大推翻。唯一"修正"是 brainstorming 技能的"等用户审 spec"门：用户以"帮我都做好完成"指示推进，我据此越过该等待门（§3.6 允许有理由偏离，已在此记录）。

## 4. 冷启动验证（§4.5）

**第二 agent**：OpenCode（与主 agent Claude Code 不同类型），全新 session，仅 SPEC.md + PLAN.md。

**发现 1（2026-07-08）— PLAN 任务排序缺口**：
- 第二 agent 实现 T1/T2 时受阻提问："T1/T2 测试需要 `harness` 可从 `src/` 导入，但导入路径设置（pyproject pythonpath / conftest.py）在 T22，排在很后面。冷启动的 T1/T2 怎么让测试跑绿？"
- 根因：PLAN 把"导入脚手架"放进 T22（打包），但 T1–T21 全都需要 `import harness` 可用 → 排序缺陷。
- **修订（关键 diff）**：
  - 修订前：导入路径设置仅在 T22（Create `pyproject.toml` + `tests/conftest.py`），排在 T1 之后 21 个 task。
  - 修订后：在 PLAN 最前插入 **Task 0: Project scaffolding（import path）**——创建 `pyproject.toml`（`[tool.pytest.ini_options] pythonpath=["src","."]`）、`src/harness/__init__.py`、`tests/conftest.py`、`tests/test_sanity.py`（TDD：先红 `ModuleNotFoundError`→建包+路径→绿）。T22 改为"Modify `pyproject.toml`（扩展 deps/ruff/mypy）+ Create `Makefile`"（conftest 已在 Task 0，不重建）。依赖注更新为"Task 0 是所有 task 前置"。
- **给第二 agent 的即时答复**（让它继续而非猜测）：先建 `src/harness/__init__.py`（空）+ `tests/conftest.py`（`sys.path.insert(0, '<repo>/src')`），装 pytest，再继续 T1/T2。
- **教训**：脚手架/构建配置这类"所有 task 的隐性前置"必须在第一个 task 之前显式成 task，否则冷启动（及后续 subagent）会在 T1 就卡住。

（冷启动继续；后续发现追加于此。）

## 5. 反思：brainstorming 技能在我项目里的表现

**做得好**：
- "一次一个问题"避免了信息过载，也直接产出了 §4.4 要的"对话节选"素材。
- 强制 §A.4 四类机制 + 焦点维度的提问，把"机制必须是代码"这条判据前置到设计期。
- 自查（spec/plan self-review）抓出了类型不一致等小问题。

**让我不满**：
- 技能默认把 spec 存到 `docs/superpowers/specs/`，与作业要求 `SPEC.md` 在根目录冲突；我改用作业路径，但技能未提示这种冲突，要靠人判断。
- "等用户审 spec"门与本项目的"都做好"节奏冲突；技能没有"用户已授权推进"的快捷路径，只能靠用户指令覆盖。
- 视觉伴侣（visual companion）全程未用到——本项目是纯后端 / CLI，技能却把它列为前置考虑，略增噪音。

> 注：本节为草稿，建议学生本人复核 / 改写为本人口吻（§4.4 反思部分宜出自学生）。
