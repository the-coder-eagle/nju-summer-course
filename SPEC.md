# SPEC.md — Coding Agent Harness（AI4SE 期末项目 A）

> 本 SPEC 与《通用要求》+《项目 A · Coding Agent Harness 要求》拼接阅读，遵循 Superpowers 七步工作流。TDD 强制；SPEC + PLAN 完成并通过冷启动验证前，不写实现代码（§4）。

---

## 1. 问题陈述

当 LLM 能完成大部分"思考"，工程师的价值落在 harness 这层工程：治理、反馈、上下文、安全、分发。本项目交付一个**自研的 Coding Agent Harness 内核**——把"只会产生下一步设想"的 LLM 封装成能稳定修复失败测试的系统，而非在现成 agent 框架上做配置。

- **目标用户**：(1) AI4SE 评审者——验证机制是代码而非提示词、可 mock 单测（§A.4-C）；(2) 想观察/演示 agent 反馈闭环的开发者；(3) 在沙箱里让 agent 修复小型 Python 测试任务的使用者。
- **为什么值得做**：把 §A.4 的"机制必须是代码、移除 LLM 后仍可独立验证"这条判据落成一个可跑、可测、可分发的真实系统，而非提示词堆叠。

## 2. 用户故事（INVEST）

- **US1**：作为开发者，我想用 mock LLM 离线跑通 harness 全流程，以便不花钱不联网验证每个机制。
- **US2**：作为开发者，我想注入一个"第一次失败"的脚本化场景，以便确定性演示反馈闭环使 agent 改变下一步。
- **US3**：作为用户，我想在 WebUI 发起一个 kata 修复任务并实时看每轮动作/测试结果，以便观察自我修正过程。
- **US4**：作为用户，我想安全录入/查看（不回显）/更新/清除 DeepSeek key，以便凭据不泄露。
- **US5**：作为评审者，我想看到 guardrail 拦截 `rm -rf` 与沙箱外编辑，以便确认治理是代码机制。
- **US6**：作为用户，我想用一条 `docker run` 跑起 WebUI+harness，以便零配置体验。
- **US7**：作为评审者，我想用 `make test` 一键跑 mock-LLM 确定性单测，以便验证内核机制。

## 3. 功能规约（按模块）

### 3.1 LLM 抽象层 `src/harness/llm/`
- 输入：`messages: list[Message]`、`tools: list[ToolSpec]|None`、`config`。
- 行为：`complete() -> LLMResponse`。两实现：`DeepSeekClient`（OpenAI 兼容 Chat Completions；base_url+key 来自凭据层）、`MockLLM`（按脚本返回）。
- 输出：`LLMResponse(raw, content, tool_calls?)`。
- 边界：单次补全调用；不内置 agent 循环；不依赖高层框架（§A.4-A）。
- 错误：网络/超时/限流 → 重试 N 次后抛 `LLMError`，主循环捕获转为"暂停"。

### 3.2 动作模型与解析 `actions.py` / `parser.py`
- 动作：`ReadFile(path)`、`EditFile(path, old, new)`、`RunShell(cmd)`、`RunTests(target)`、`Finish`。
- `parse(raw_response) -> Action | ParseError`：解析 LLM 输出为结构化动作；格式不符 → `ParseError` 回灌。

### 3.3 工具分发 `dispatcher.py`
- `dispatch(action, ctx) -> ActionResult`：在沙箱内执行（子进程 `cwd=sandbox_root`）。
- ReadFile/EditFile 限沙箱内；RunShell 经 allowlist/denylist；RunTests 跑 pytest。
- 输出：`ActionResult(ok, out, err, changed_files, test_result?)`。

### 3.4 治理护栏 `guardrail.py`（+ HITL）
- `guardrail(action, scope) -> Decision`：`Allow | Deny | RequireApproval`。
- 拦截：沙箱外编辑（路径规范化后不在 `sandbox_root` 下）、denylist shell（`rm -rf`/`sudo`/`drop`/`curl|sh`/网络）、测试中网络外联。
- HITL：`RequireApproval` → 主循环暂停、对外暴露动作 → 等待 `Approved/Denied` → 恢复/中止（最小状态机）。
- 输出：`Decision` + 理由。

### 3.5 反馈流水线（★主角维度） `src/harness/feedback/`
- `runner.py` Run：`run_tests(target) -> TestResult`（exit_code、stdout；信号源 pytest，可选 ruff/mypy）。
- `parse.py` Parse：`parse_failures(TestResult) -> list[Failure]`（file/line/assertion/expected/actual/traceback）。
- `classifier.py` Classify：`classify(Failure) -> (FailureType, hint)`；类型：assertion/import/syntax/type/logic/timeout。
- `composer.py` Compose：`compose(failures, state) -> Feedback`（结构化反馈消息）。
- `selfcorrect.py`：重试预算、failure-type→hint 映射、升级（同类型 N 次后强化提示或放弃）、停机（green 且预算>0 → done；预算=0 → aborted）。
- 各级纯函数、不依赖 LLM、mock 可单测。

### 3.6 上下文与记忆 `context.py` / `memory.py`
- `build_context(state) -> messages`：system prompt + 当前 kata 任务 + 历史 + 上轮反馈。
- 记忆（最小）：每 arena 项目的 `CONVENTIONS.md` 按需载入（不全量）；跨会话 = 文件持久化。

### 3.7 主循环 `loop.py`
- `run(task) -> Outcome`：建上下文→调 llm→解析→guardrail→分发→（若 RunTests）反馈流水线→合成反馈入上下文→停机判断。薄导体，无业务逻辑。

### 3.8 配置 `config.py`
- 声明式：沙箱根、重试预算、denylist/warnlist、model（默认 `deepseek-chat`）、base_url、信号源开关。

### 3.9 竞技场 `arena/`（内容物，非内核）
- ~6 个 kata 目录，各带失败测试，覆盖：断言失败/导入错误/语法/类型/逻辑/超时。

### 3.10 WebUI `web/`（薄，分阶段，非内核）
- 阶段 1：HTTP API（POST task → 启动 loop）；阶段 2：WebSocket 流式（每轮动作/测试/反馈推前端）。内核不 import 任何 web 框架。

### 3.11 凭据 CLI `auth` 子命令
- `set`（隐藏输入）/`status`（set/unset，不回显）/`update`/`clear`。首运行缺 key → 引导 `set`。

## 4. 非功能性需求

- **性能**：单 kata 修复在 mock 下秒级；真实 DeepSeek 视 API 延迟。
- **安全**：见 §7 凭据威胁模型；沙箱路径围栏；shell denylist；HITL。
- **可用性**：一条 `docker run` 起服务；WebUI 流式可读；CLI auth 引导。
- **可观测性**：每轮结构化日志（turn/action/result/feedback）；（二期）事件日志 replay。

## 5. 系统架构

```
                 ┌─────────────┐
  声明式配置      │  config.py  │
                 └──────┬──────┘
                        ▼
  ┌──────────────────────────────────────────────────────────┐
  │  loop.py  主循环（薄导体）                                  │
  │  建上下文→调llm→解析→guardrail→分发→                       │
  │   (若RunTests)反馈流水线→合成反馈入上下文→停机判断          │
  └──┬───────┬─────────┬───────────┬────────────┬───────────┘
     ▼       ▼         ▼           ▼            ▼
  ┌──────┐ ┌──────┐ ┌──────────┐ ┌────────────┐ ┌──────────┐
  │ llm/ │ │parser│ │guardrail │ │ dispatcher │ │context+  │
  │抽象层│ │      │ │+HITL     │ │            │ │memory(min)│
  └──────┘ └──────┘ └────┬─────┘ └─────┬──────┘ └──────────┘
                          │             │
                          ▼             ▼
                     ┌────────┐   ┌──────────────────┐
                     │ 拦截   │   │ 沙箱 arena        │
                     └────────┘   └──────────────────┘
  反馈流水线（★主角，RunTests 触发，各级纯函数）：
  runner→parse→classify→compose→selfcorrect
  展示层（分阶段，非内核）：web/ HTTP+WS → 流式控制台
```

- **外部依赖**：DeepSeek API（OpenAI 兼容）、pytest、（可选）ruff/mypy、Docker、Render/Fly.io、NJU GitLab CI。
- **数据流**：见 §3.7 + §2 时序（设计第 2 节）。

## 6. 数据模型

- `Message(role, content, tool_calls?)`
- `Action` 联合体（见 §3.2）
- `ActionResult(ok, out, err, changed_files, test_result?)`
- `TestResult(exit_code, stdout, signals)`
- `Failure(file, line, assertion, expected, actual, traceback, type?, hint?)`
- `Feedback(text, failures, retry_state)`
- `State(history, retry_budget, status, current_kata)`
- `Outcome(status, turns, final_test_result)`

## 7. 凭据与分发设计

### 7.1 凭据威胁模型与对策
| 威胁 | 对策 |
|---|---|
| key 硬编码源码 | 禁止；CI 扫描 |
| key 进 git 历史 | `.gitignore` 含 `.env`；pre-commit 检查 |
| 日志/shell history 泄露 | 不 log key；`auth set` 隐藏输入，非 `export` |
| `.env` 明文 | 仅开发期回退；文档标注风险；生产用 Credential Manager/secret env |
| 进程环境可见 | key 仅调用时载入内存；容器用 secret env |

存储：Windows Credential Manager（主，OS 加密）；容器/Linux 用 secret env 或加密文件；`.env` 开发回退。

### 7.2 分发
- Docker 镜像：单条 `docker build` + `docker run -p PORT`。Dockerfile pin Python、装依赖、打包 src+arena。
- `.gitlab-ci.yml`：`unit-test` job + `image-build` job。
- README：获取/运行/key 安全配置/已知限制（平台/架构/依赖）。

### 7.3 部署
- Render（主）/Fly.io：跑 web 服务 + 内核；DeepSeek key 经 Render secret env 或容器内 `auth set`。公网 URL。CI 构建镜像，部署手动触发。

## 8. 技术选型与理由

- **Python**：LLM/mock 生态最成熟，pytest 适合 mock-LLM 确定性单测，subprocess 跑测试方便，TDD 体验好，Windows 友好。
- **LLM 抽象**：OpenAI 兼容 Chat Completions（可换 base_url/key，mock 可注）。
- **真实 provider DeepSeek**：OpenAI 兼容、国内直连、便宜、coding 强。
- **分发 Docker**：跨平台一致、契合部署、CI 可构建。
- **部署 Render/Fly.io**：免费额度、支持 Docker。
- **WebUI**：轻量 HTTP/WS（FastAPI/Starlette），内核不依赖。
- **不用** LangChain/AutoGen/CrewAI 高层循环（§A.4-A）。

## 9. 验收标准

- mock-LLM 确定性单测全绿（`make test`），不联网。
- 机制演示（§A.6）可复现：① guardrail 拦截危险动作；② 注入失败→反馈→改下一步→绿；③ 焦点行为（分类 + 预算耗尽 → abort）。
- `docker run` 一条命令起 WebUI；发起 kata 任务可见流式每轮。
- `auth set/status/clear`：status 不回显；clear 后 key 不可用。
- guardrail 阻断 `rm -rf` 与沙箱外编辑（单测断言）。
- CI `.gitlab-ci.yml` 含 `unit-test`（+`image-build`），最后一次 pass。
- 公网 URL 可访问 WebUI。

## 10. 风险与未决问题

- DeepSeek 输出格式漂移 → parser 容错 + Mock 兜底；pin 输出契约。
- pytest 输出版本差异 → pin pytest 版本；parser 适配。
- **冷启动第二 agent 选型未定（§4.5）**——待用户选 Codex/Cursor/Gemini CLI 等。
- Windows Credential Manager 在 Linux 容器不可用 → 容器用 secret env/加密文件，文档说明。
- WebUI 流式复杂度 → 分阶段（先 HTTP 再 WS）。
- 真实 live demo 需 DeepSeek key（用户提供，经 `auth` 流程）。

## 11. 领域与机制设计（§A.5）

- **领域**：coding。
- **反馈信号**：pytest exit+output（主）；ruff lint、mypy 类型（可选加深）。客观、确定、可回灌。
- **危险动作**：沙箱外编辑、denylist shell、测试网络外联；HITL 暂停。
- **所需工具**：ReadFile/EditFile/RunShell/RunTests/Finish。
- **记忆需求**：项目约定（`CONVENTIONS.md`）按需载入；跨会话持久。
- **焦点维度：反馈闭环**。理由：coding 反馈最客观可编码；分类法 + 自我修正策略天然由代码构成，深入后最契 §A.4 (A)(B)(C)；治理/记忆等保持最低实现（§A.4-D）。
- **如何编码**：反馈流水线各级纯函数；classifier = pytest 输出的规则解析；selfcorrect = 预算/类型计数状态机；guardrail = 路径围栏 + denylist 函数；HITL = 最小暂停状态。移除真实 LLM 后均可用 mock 单测（§A.4-C）。
