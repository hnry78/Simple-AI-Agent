# Simple-AI-Agent
个人开发的轻量化agent，可以实现数学计算，文件读写（在项目文件夹下），bash命令执行（简单沙箱）

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

## 功能

- 实现数学计算
- 在项目/agent_workspace文件夹下进行文件读写与删除，实现简单沙箱
- 简单的bash命令
- 每次运行会预估当前的token消耗量来调整生成策略，防止超过阈值
- 统计每个任务的tokens和成本，并生成run_id，方便复现

可以实现比如“读取某csv文件，并将某列/行的某统计矩输入XXX.txt”一类的指令
## <span style="color:red;font-weight:bold;">注意！</span>
<span style="color:red;font-weight:bold;">agent默认工作路径已在.\agent_workspace下，在指定进行文件读写时不要加入agent_workspace及之前的目录！</span>
## 示例

```text
> 读取 sales.csv 的最后一列，计算平均值和标准差，写入 result.txt
> 列出所有文件
> 计算 (3.14159 * 17.2) / log(2.71828) 并保留 4 位小数
```

## 项目结构

```
AItask/
├── main.py              # 入口，启动交互式会话
├── agent.py             # Agent 核心逻辑，工具调度与轮次控制
├── ai_model.py          # LLM 配置（API Key、模型名、参数）
├── llm_client.py        # LLM API 客户端封装
├── context.py           # 对话上下文管理与 Token 预算控制
├── tools.py             # 工具实现（计算器、文件读写、bash 执行）
├── observability.py     # 日志与成本追踪
├── requirements.txt     # 依赖清单
├── agent_workspace/     # Agent 可读写的沙箱目录（自动创建）
├── logs/                # 运行日志和 run_id 记录（自动创建）
└── README.md
```

## 食用指南

### 前置要求
- **python** 3.10+
- **自己用着顺手的大模型** 

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/hnry78/Simple-AI-Agent.git
cd simple-AI-Agent

# 2. 创建虚拟环境（推荐）
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS / Linux:
# source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
```
### 使用

- 在ai_model.py里面写入你选择的ai参数，不要删除双引号
- 运行main.py，随后可以直接运行

### 注意事项
- 文件操作仅限制在.\agent_workspace里（程序会自动创建），请将你需要agent读取的材料加入.\agent_workspace
- 日志和run_id记录在.\logs里，用jsonl格式储存

## 许可证

[MIT](LICENSE) © 2026