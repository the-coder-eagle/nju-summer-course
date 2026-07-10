# Coding Agent Harness — AI4SE Project A

把 LLM 封装成能稳定修复失败测试的系统——自研 harness 内核，非 agent 框架配置。

## 简介

Coding Agent Harness 是一个自研的 coding agent 内核，包含：LLM 抽象层、动作解析、治理护栏、沙箱分发、反馈流水线（runner→parse→classify→compose→selfcorrect）、主循环。6 个 kata 测试竞技场，mock-LLM 确定性单测。

## 安装

```bash
git clone <repo-url>
cd sumsch
pip install -e ".[dev]"
```

## 运行

```bash
# 运行测试
make test

# 启动 WebUI (http://localhost:8000)
make run

# 代码检查
make lint
```

## Docker 分发

```bash
docker build -t harness .
docker run -p 8000:8000 harness
```

## API key 安全配置

```bash
# 录入 key（隐藏输入）
python -c "from harness.auth.cli import set_; set_()"

# 查看状态（不回显明文）
python -c "from harness.auth.cli import status; status()"

# 清除 key
python -c "from harness.auth.cli import clear; clear()"
```

**安全说明：**
- key 存储在系统凭据管理器（Windows Credential Manager / macOS Keychain / Linux Secret Service）
- `.env` 文件已 gitignore，仅开发期回退
- key 绝不写入日志、shell history、或进程环境变量

## 目录结构

```
sumsch/
├── src/harness/       # 内核源码
│   ├── llm/           # LLM 抽象 (base + mock + deepseek)
│   ├── feedback/      # 反馈流水线
│   ├── auth/          # 凭据存储 + CLI
│   ├── loop.py        # 主循环
│   ├── guardrail.py   # 治理护栏 + HITL
│   ├── dispatcher.py  # 工具分发
│   ├── parser.py      # 动作解析
│   ├── config.py      # 配置加载
│   ├── context.py     # 上下文构建
│   └── memory.py      # 项目约定加载
├── arena/             # 6 个 kata 竞技场
├── web/               # WebUI (FastAPI)
├── tests/             # 单元测试 (mock-LLM, 确定性)
├── SPEC.md            # 设计规约
├── PLAN.md            # 实现计划
├── REFLECTION.md      # 反思报告
├── Dockerfile
├── .gitlab-ci.yml
└── Makefile
```

## 安全边界

- **沙箱围栏**：所有文件操作限 `sandbox_root` 内，路径规范化防逃逸
- **Shell denylist**：`rm -rf`、`sudo`、`curl|sh` 等危险命令硬拦截
- **HITL**：warnlist 命令（如 `git push`）暂停等待人工审批
- **凭据**：key 不入源码/git/log/shell history；首次运行引导录入；查看状态不回显明文

## 已知限制

- 真实 LLM 需 DeepSeek API key（用户提供，经 `auth` 流程）
- WebSocket 流式在 Starlette TestClient 下有线程限制（Windows），生产部署不受影响
- 凭据存储在 Docker 容器内需用 secret env（非 keyring）
- 平台：Windows（开发）/ Linux（Docker 部署）

## 部署

```bash
# Render (推荐)
# 1. Push 到 NJU GitLab
# 2. 在 Render 连接仓库
# 3. 设置 DEEPSEEK_API_KEY secret
# 4. 部署 → 公网 URL
```
