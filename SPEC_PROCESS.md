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

**发现 2（2026-07-08）— Python 版本门槛与环境不符**：
- 第二 agent 发现：环境默认 `python` 是 3.10.11，但 PLAN 全局约束要求 Python ≥ 3.11（`requires-python = ">=3.11"`）。默认解释器低于门槛。
- 根因：PLAN 设了 3.11 门槛但未考虑开发机默认 python 可能是 3.10；且代码实际未用任何 3.11-only 特性（无 tomllib / TaskGroup / ExceptionGroup / typing.Self；`X|Y` 联合类型 3.10 即支持）。
- **修订**：Python 门槛降为 **≥ 3.10**（Global Constraints + 两处 `requires-python`）。3.10–3.13 均可，默认 python 直接可用，消除摩擦。
- **教训**：语言版本门槛应与代码实际依赖的最低特性对齐，否则会在默认环境上凭空卡住。

**发现 3（2026-07-08）— 开发依赖（pytest 等）安装时机晚**：
- 第二 agent 发现：pytest 默认未安装；PLAN 把依赖安装排在 T22（晚），但 T0/T1 起就需要 pytest。
- 根因：与发现 1 同类——环境/依赖基础设施被排在后期 task，而早期 task 已需要。
- **修订（当前）**：Task 0 增加 `pip install pytest` 步，覆盖 T0–T16。
- **修订（延后）**：把"完整 dev-deps（httpx/keyring/fastapi 等）前置到 Task 0"的重构留到真实实现期（届时 Task 0 直接建全量 pyproject + `pip install -e .[dev]`，T17+ 不再缺依赖）。
- **教训**：所有 task 共享的隐性前置（导入路径、依赖安装、解释器版本）必须集中在最前的 setup task，不能分散在后期。

**T1 清晰度确认**：第二 agent 按 PLAN 逐字实现 Task 1，红（`ModuleNotFoundError: harness.actions`）→ 绿，未对实现产生歧义——T1 spec 清晰度合格。

**冷启动完成（2026-07-08）**：
- 第二 agent（OpenCode，py -3.12 / Python 3.12.10 / pytest 8.3.5）实现 Task 0 + Task 1 + Task 2，严格 TDD（红→绿→commit），代码逐字照搬 PLAN、零偏离；最终 `pytest -q` → 3 passed。
- commits：`fb438e1`(Task 0)、`f518e94`(Task 1)、`83e1a16`(Task 2)，直接落 `main`（冷启动验证性质；真实实现期改 worktree/MR，待 NJU remote）。
- **T1/T2 spec 清晰度：合格**（逐字可实现、无歧义）。
- **6 处缺口**：①导入路径时序✅(补 Task 0) ②Python 门槛✅(→3.10) ③pytest 安装✅(Task 0 加 `pip install pytest`) ④`src/harness/__init__.py` 归属✅(并入 Task 0) ⑤Task 1 未用 `field` import✅(修 PLAN + 修仓库 actions.py) ⑥行尾归一化✅(加 `.gitattributes`)。
- **跟进项**：`make test`（T22）用裸 `python`（本机=3.10，无 pytest）会失败 → 真实实现期用 venv 固定环境（完整 pyproject + `.venv` + `pip install -e .[dev]`），Makefile 走 venv python。
- **反思**：冷启动价值兑现——3 处"所有 task 隐性前置"缺口（导入路径/版本/依赖）全是主 agent 写 PLAN 时漏排的，全新 agent 在 T1 即撞穿；这正是 §4.5 想要的"最接近同侪评审的内部机制"。

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
