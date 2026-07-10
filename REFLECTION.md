# REFLECTION.md — 反思报告

## 1. Superpowers 技能：哪些发挥最大作用、哪些形式大于实质？

**brainstorming — 实效最大。** 它的"一次一个问题"机制避免了需求阶段的信息过载。在本项目里，它逼迫我逐项确认主角维度、真实 LLM provider、目标场景、CI 平台等关键决策。最有价值的是它强制追问 §A.4 的四类机制——这让"机制必须是代码"这条判据在 SPEC 阶段就前置了。没有这套追问，很容易把反馈闭环写成"让 LLM 自己检查"的提示词。

**writing-plans — 实效大，但需要人工校准。** 26 个 task 的依赖树和可并行标注是好的，但 PLAN 最初漏掉了最关键的脚手架 task——导入路径、pytest 安装、Python 版本门槛。这三件事是 T1–T26 的隐性前置，全被推到 T22（打包阶段）。冷启动 agent 在 T1 就被卡住，证明了"技能写的 plan 需要人审查时序"。

**subagent-driven-development — 冷启动阶段已验证实效。** 用 OpenCode（不同类型 agent）仅凭 SPEC+PLAN 跑 T0/T1/T2，严格 TDD，逐字照搬 PLAN 无偏离。这个机制暴露了主 agent 写 PLAN 时的 6 处盲区——相当于一次免费的同行评审。

**test-driven-development — 实效大但执行成本被低估。** 红→绿→重构的节奏迫使 mock-LLM 单测在写实现前就明确了接口契约。但冷启动暴露了一个实际问题：TDD 的前提（import 路径、pytest 可用）本身也需要 TDD 来验证——这形成了一种递归式的"谁来测试测试环境"的困境，Task 0 就是为此设的。

**requesting-code-review / receiving-code-review — 尚未充分使用。** 冷启动阶段代码量少（3 个文件），暂未触发正式 review 流程。判断：小规模项目中 review 技能的收益曲线偏后——代码量积累到一定程度后才体现价值。

**形式大于实质的部分**：brainstorming 技能的 visual companion 提示——本项目是纯后端/CLI，每次 brainstorming 都提醒"是否需要 visual companion"成了噪音。技能没有根据项目类型（前端 vs 后端）自适应跳过的机制。

---

## 2. TDD 强制：AI 协作下是阻碍还是放大器？

**在 mock-LLM 单测场景下是放大器。** 原因：

1. **mock-LLM 的确定性让 TDD 的红→绿可严格复现。** 每个测试用例的输入输出完全确定，不会因为 LLM 随机性导致"有时红有时绿"的混乱。`test_config.py` 里断言 `"rm -rf" in cfg.denylist`，这个断言在 T0 import 路径打通后必然红→绿，不会出现"本地绿 CI 红"的灵异现象。

2. **TDD 充当了 SPEC→代码的翻译校验。** 写测试时首先暴露问题：`harness.actions.ReadFile` 这个 import 路径对吗？dataclass 字段名叫 `path` 还是 `file_path`？这些问题在测试里敲定后，实现就只是填空。冷启动 agent 按 PLAN 的测试模板逐字照搬、先红后绿，零歧义。

3. **但有一个前提条件：测试环境必须先行可用。** 本项目冷启动发现 1/2/3（无 import 路径、Python 版本不对、pytest 未装）本质上都是"TDD 的前提条件不满足"。解决方式是 Task 0——一个用 TDD 验证"TDD 可以工作"的 meta-task。这层 meta 成本在常规开发中不存在，是 TDD×AI 协作特有的开销。

**没有"为了凑失败测试而浪费时间"的情况。** 因为 PLAN 已经为每个 task 提供了测试模板，subagent 的工作是照搬并验证——失败是真实的（ModuleNotFoundError、ImportError），不是人为制造。

---

## 3. Subagent-driven 工作流：自主运行多久不偏离主题？

**冷启动 agent（OpenCode）表现：全程未偏离。** 在仅提供 SPEC.md + PLAN.md、无任何对话历史的条件下，OpenCode 严格按 PLAN 的 TDD 步骤实现 T0/T1/T2，代码逐字照搬 PLAN、零偏离。这首先归功于 PLAN 颗粒度够细——每个 task 给出了测试代码、实现代码、运行命令的具体文本。

**但也暴露了一个关键限制：subagent 对隐性前提完全盲视。** OpenCode 在 T1 被卡住时没有直接猜测，而是暂停提问："导入路径设置在 T22，T1/T2 怎么让测试跑绿？"这是正确的行为——按 §4.5 的要求，遇到不确定即暂停。但这意味着 subagent **不能替代人对 PLAN 逻辑的正确性判断**——如果 PLAN 有 bug（如任务排序错误），subagent 会忠实执行到碰壁、然后暂停，而不是自己修复 PLAN。

**对比：主 agent（Claude Code）写 PLAN 时的偏差。** 主 agent 在 brainstorming 阶段积累了隐性上下文（知道 python 3.10 可用、知道 pytest 需要装），但这些上下文没有写进 PLAN。冷启动 agent 没有这些上下文、就直接暴露了 PLAN 的完整性缺口。这说明 **subagent 自主运行的质量上限 = PLAN 的质量**。

---

## 4. Task 颗粒度：什么样的 task 大小最优？

**PLAN 的 26 个 task 颗粒度整体合理，但有三种改进空间：**

- **太细的（T0 各子步骤）**：Task 0 的 Step 1–5（写测试→跑红→实现→跑绿→commit）每个只有 2–3 行操作，在一个 subagent 会话里可以全做完。作为 PLAN 文档的一部分这些步骤有记录价值，但不必各成一个独立 subagent 任务。

- **正好的（T1/T2/T3/T4/T5）**：一个 dataclass 模块 + 对应测试 ≈ 5–10 分钟工作量，一个 subagent 一次会话轻松完成，commit 粒度也匹配"一个能力一个 commit"的纪律。

- **可能偏大的（T16 主循环）**：`loop.py` 集成了 context→llm→parse→guardrail→dispatch→feedback pipeline→stop check 七步，且与 T4–T8+T15 全部耦合。如果 subagent 实现时某个上游接口与预期不一致，排查会很难。建议在实际实现时拆成两个子 step：先写 loop 骨架 + mock 走通 happy path，再加 guardrail/HITL/feedback 分支。

**"一次 commit ≈ 一个能力"在 mock-LLM 场景下行得通。** 每个 task 产出一个模块 + 对应测试，commit message 清晰标注 `feat(模块名): 功能摘要`。真实实现期如果按 worktree→PR 的流程，每个 task 一个 PR 也是合理的。

---

## 5. SPEC/PLAN 质量如何影响实现质量？

**最典型案例：冷启动发现 1——PLAN 任务排序缺口。**

**具体场景**：冷启动 agent（OpenCode）按 PLAN 从 T1 开始实现 `actions.py`。写测试时即受阻——`from harness.actions import ReadFile` 报 `ModuleNotFoundError`。agent 查 PLAN 发现：import 路径设置（`pyproject.toml` 的 `pythonpath` + `tests/conftest.py` 的 `sys.path.insert`）排在 T22（打包阶段），在 T1 之后 21 个 task。

**根因**：主 agent 写 PLAN 时把"构建配置"视为"打包阶段"的事情，没有意识到 `import harness` 是 T1–T21 全部 task 的隐性前置。这是典型的"作者盲区"——写 PLAN 的人脑子里知道 import 路径应该怎么设，但没把它写进 PLAN 的前置步骤。

**修订前后的关键 diff**：
- 修订前：T1（actions）→ T2（config）→ … → T22（pyproject + Makefile + conftest）
- 修订后：**Task 0**（import path scaffolding）→ T1 → T2 → … → T22（扩展 pyproject + Makefile）

**影响**：如果没有冷启动，主 agent 在实现 T1 时会自动补上 import 路径（因为它有隐性上下文），subagent 不会发现这是个缺口。但换一个 agent、换个时间、换个心态——这些隐性上下文全没了，缺陷就暴露了。这验证了 §4.5 的核心主张：**SPEC/PLAN 的质量不能依赖作者的隐性知识**。

**另外两处同样性质的缺口**：Python 版本门槛 3.11→3.10（发现 2）、pytest 安装时机 T22→T0（发现 3），都是"作者认为理所当然、PLAN 没写、冷启动 agent 忠实执行到碰壁"的模式。

---

## 6. 最有效的 prompt / context 策略是什么？为什么？

**目前还是设计阶段，以下基于 SPEC 设计推理，实现期验证后修正：**

**结构化反馈消息（§3.5 compose）**：`Feedback` 不把 pytest raw output 原样灌给 LLM，而是经过 parse→classify→compose 三级处理后生成：
```
Feedback (retry budget left: 3):
- kata_assertion/test_lib.py:2 [logic] assert add(2,3) == 5
  hint: Logic error; the function runs but returns an incorrect result. Re-read the test intent.
```
这比 raw pytest traceback 有效，因为：(1) 去掉了无关的框架噪声；(2) 附加了针对性的 hint；(3) 保留了剩余预算信息——让 LLM 知道"还剩几次尝试"。这是"机制是代码，不是提示词"（§A.4-B）的直接体现：分类器和 composer 是纯函数，不用 LLM 也能跑。

**工具使用受限的 system prompt**：动作只有 5 种（READ/EDIT/SHELL/TEST/FINISH），且 EDIT 的 wire format 固定（`EDIT <path> <old>-><new>`）。小动作集 + 严格格式 = 解析确定性高，减少 `ParseError` 回灌次数。

**历史消息的预算感知**：`State.history` 只追加不截断，但随着轮次增加消息列表会膨胀。对于一个 3–5 轮的典型 kata 修复这没问题，但如果扩展到更复杂场景，需考虑滑动窗口或摘要压缩。

---

## 7. 凭据与分发：这两条工程要求迫使你想清楚了哪些原本会忽略的问题？

**凭据方面**：

1. **key 的多个泄露面**：不只 `.env` 进 git 是问题——shell history（`export KEY=xxx`）、日志（httpx debug 输出）、进程列表（`/proc/<pid>/environ`）全是泄露面。SPEC §7.1 的威胁模型表格迫使逐条列出对策。

2. **跨平台凭据存储的矛盾**：Windows Credential Manager 在 Docker 容器里不可用，Linux secret service 在 WSL 里需要 dbus。一个"跨平台"方案实际上是"按部署形态选方案"——开发机用 keyring，容器用 secret env，文档标明各形态的限制。

3. **首次运行引导**：没有 key 时不能直接 crash，而要引导 `auth set` → 隐藏输入 → 确认存储。这比"请设置环境变量 DEEPSEEK_API_KEY"多了一层工程，但用户体验完全不同。

**分发方面**：

4. **"单条 docker run 可跑"的前提**：Dockerfile 要 pin Python 版本、装依赖、打包 src+arena+web、设置 PYTHONPATH、expose 端口。任何一个遗漏都会让这条命令失败——而使用者没法像开发者那样调试。

5. **镜像大小 vs 构建时间**：`python:3.11-slim` vs `alpine` 的权衡——slim 更大但兼容性好，alpine 小但 musl 可能和某些 Python wheel 不兼容。SPEC 选 slim 是务实的选择。

6. **CI 构建镜像 ≠ 本地能跑**：`.gitlab-ci.yml` 里 `image-build` job 用 `docker:24-dind`，需要 privileged mode。NJU GitLab runner 是否支持 dind 是实际部署前必须确认的问题。

---

## 8. 如果重做，你会改变什么？

1. **把 Task 0 从"补丁"变成"一开始就有"**：导入路径、pytest 安装、Python 版本三项前置条件在 brainstorming 收尾时就应该确认并写进 PLAN 最前。这次是冷启动发现了才补——说明 PLAN 自审时缺了一个"从零开始 blind run"的 checklist。

2. **SPEC 的反反馈闭环机制更具体**：§3.5 各级都是纯函数、不依赖 LLM、可单测——这点在 SPEC 里写了。但 selfcorrect 的升级策略（同类型 N 次后强化提示）具体怎么"强化"（改 prompt？换 kata？增加 hint 强度？）在 SPEC 里没定——留给实现了。如果重做，会在 SPEC 里明确升级策略的决策树。

3. **冷启动 agent 选型更早定**：PLAN 写完后等了用户一段时间才确定冷启动 agent 用 OpenCode。如果重做，brainstorming 阶段就确认冷启动 agent，省去等待。

4. **AGENT_LOG 与 SPEC_PROCESS 同步写，不后补**：本次两个文件在 PLAN 完成后一次补齐，导致冷启动期间的细节依赖记忆而非实时记录。#8 条（漏提 code 改动）就是后补的代价——如果每完成一件事即写日志，就不会出现"日志说提了、实际没提"。

5. **尽早搭建 CI**：虽然 CI 排在 T24，但哪怕是一个只跑 `make test` 的空壳 CI，从 T0 就挂上，也能在每次 commit 后自动验证"新机器上能不能跑"。这比"最后一次性配 CI、祈禱 pass"风险小得多。

---

## 9. 对 Superpowers 方法论的批判

**Superpowers 假设了什么？**

1. **假设开发者愿意接受流程纪律**：七步工作流（brainstorming → writing-plans → worktree → subagent → TDD → review → finish）假设每一步都严格执行。实际情况是——用户会说"帮我都做好完成"，跳过逐节等待门。Superpowers 对此有"合理偏离需记录"的条款，但没有"用户已授权推进"的快捷路径。

2. **假设 task 可以独立并行**：worktree + subagent 模型假设 task 间依赖少、可大量并行。但像 harness 主循环（T16）上游依赖 7 个模块——它的并发度受依赖树深度限制，不是所有项目都适合高并行。

3. **假设 mock/stub 容易构造**：§A.4-C 的"移除 LLM 后仍可单测"是好的判据，但它意味着每个外部依赖（LLM API、文件系统、子进程）都要有可注入的 mock 版本。对简单模块（config、actions）这容易，对 dispatcher（真正执行 shell 命令的模块），mock 子进程的行为需要更精细的设计。

4. **假设开发者理解"一次一个能力"的粒度**：PLAN 要求每个 task 2–5 分钟、一个 subagent 一次会话完成。但"一个能力"的定义在不同抽象层级不同：`actions.py` 的 5 个 dataclass 是一个能力，但 `loop.py` 的 7 步编排也是一个能力——后者的工作量是前者的数倍。粒度判断仍然依赖人的经验。

**这些假设在我的项目里成立吗？**

- 流程纪律：部分成立——brainstorming 和 PLAN 阶段严格遵循，但记录文件的同步被推迟（本次补全）。
- task 并行：部分成立——T0 是瓶颈，T1–T3 可并行，T4–T8 可并行，但 T16 的扇入依赖决定了实现后期会串行化。
- mock 构造：成立——纯函数模块（classifier、parser、guardrail）mock 容易，subprocess 相关模块（dispatcher、runner）可用 tmp_path fixture 解决。
- 粒度判断：基本成立——26 个 task 中大部分粒度合适，T16 偏大需拆分。

**七步工作流若缺了哪一步会怎样？**

- 缺 brainstorming → SPEC 变成散文式需求列表，没有四类机制的强制追问。
- 缺冷启动验证 → PLAN 的 6 处时序/版本/依赖缺口全部进入实现期，subagent 反复碰壁。
- 缺 TDD → mock-LLM 的优势被浪费——没有确定性测试，每次改动都要肉眼判断"对不对"。
- 缺 review → subagent 的代码偏差会累积，因为没有人在 task 间把关。

**Superpowers 最适合什么场景？**
适合有清晰接口边界、可拆分为独立模块、可 mock 外部依赖的项目。本项目的 LLM 抽象层 + 反馈流水线恰好满足这三个条件。

**对什么场景不适？**
不适合高度耦合的单体、需要大量集成测试的项目、或者"探索性编程"——你还不确定要做什么、需要边写边改的场景。Superpowers 的前置门槛（SPEC→PLAN→冷启动）对这类项目太重。

---

> 最终字数：约 2400 字
