# DeepEye-SQL 复现项目文档

## 项目概述
本项目是对论文 **"DeepEye-SQL: A Software-Engineering-Inspired Text-to-SQL Framework"** 的 MVP (Minimum Viable Product) 复现。
DeepEye-SQL 提出了一个受软件工程启发的 Text-to-SQL 框架，包含需求分析、N版本生成、单元测试和发布选择四个阶段。
本项目在本地环境中实现了这一完整流程，旨在验证框架的核心思想和可行性。

## 已实现功能

本项目完整实现了 DeepEye-SQL 的四个核心阶段：

### 1. 意图范围界定与语义落地 (Intent Scoping and Semantic Grounding)
-   **Schema Linking (模式链接)**: 实现了三种链接策略的融合：
    -   **Direct Linking**: 直接让 LLM 识别相关表和列。
    -   **Reversed Linking**: 通过生成草稿 SQL 并解析，反向推导相关 Schema。
    -   **Value-based Linking**: 基于问题中的关键词匹配数据库中的值，定位相关列。
-   **Value Retrieval (值检索)**: 实现了基于关键词的数据库值检索，帮助 LLM 理解特定实体（如课程名、人名）。

### 2. N-version SQL 生成 (N-version Programming for SQL Generation)
-   实现了三种独立的 SQL 生成器，以增加生成结果的多样性：
    -   **Skeleton-based Generator**: 先生成 SQL 骨架，再填充细节。
    -   **ICL-based Generator**: 基于上下文学习 (In-Context Learning)，利用示例指导生成。
    -   **Divide-and-Conquer Generator**: 针对复杂问题，采用分治思想进行生成（MVP 中简化为单一 Prompt）。

### 3. SQL 单元测试与修正 (SQL Unit Testing and Revision)
-   实现了一个工具链 (Tool-Chain) 对生成的 SQL 进行检查和修正：
    -   **Syntax Checker**: 使用 `sqlglot` 检查 SQL 语法是否符合 SQLite 标准。
    -   **Join Checker**: 检查 JOIN 语句是否包含必要的 ON 条件。
-   实现了 **Check-and-Revise** 循环：当检查器发现错误时，自动调用 LLM 根据错误信息进行修正。

### 4. 基于置信度的 SQL 选择 (Confidence-aware SQL Selection)
-   **执行聚类**: 在数据库上实际执行所有候选 SQL，根据执行结果将 SQL 聚类。
-   **置信度估算**: 计算最大聚类的占比作为置信度分数。
-   **选择策略**:
    -   **High Confidence Shortcut**: 如果置信度超过阈值 (0.6)，直接选择最大聚类的 SQL。
    -   **Pairwise Voting**: 如果置信度较低，触发 LLM 对前两名候选者进行成对投票 (Pairwise Voting)，选出最佳 SQL。

## 与原论文实现的差异

由于环境限制和 MVP 的定位，本项目在实现细节上与原论文存在以下差异：

| 模块 | 原论文实现 | 本项目 MVP 实现 | 差异原因 |
| :--- | :--- | :--- | :--- |
| **Value Retrieval** | 使用 **Vector Database (Chroma)** 和 Embedding 模型进行语义检索。 | 使用 **SQL LIKE** 语句进行简单的关键词匹配。 | 避免在 Windows 环境下安装 `chromadb` 和 `hnswlib` 带来的构建依赖问题。 |
| **ICL Generator** | 动态从训练集中检索最相似的示例 (Few-shot)。 | 使用 **Hardcoded (硬编码)** 的固定示例。 | 简化实现，无需加载完整的 BIRD/Spider 训练集。 |
| **Checkers** | 包含 Time, NULL, Result 等多个复杂的检查器。 | 仅实现了 **Syntax** 和 **Join** 两个基础检查器。 | 聚焦核心流程验证，简化开发工作量。 |
| **Selection** | 包含复杂的 Unbalanced Voting 和 Win Rate 计算。 | 简化为对 Top-2 聚类进行一次 **Pairwise Voting**。 | 简化逻辑，降低 Token 消耗。 |
| **Database** | 使用 BIRD 和 Spider 数据集的大型数据库。 | 使用脚本创建的一个包含 3 张表的 **Dummy SQLite Database** (School)。 | 方便本地快速测试和验证。 |
| **LLM** | 使用 Qwen/Gemma 等开源模型或 GPT-4。 | 使用 **LangChain + OpenAI (GPT-4o)** 接口。 | 利用现有 API 资源，简化模型部署。 |

## 目录结构说明

```text
g:\NL2SQL\
├── deepeye/                # 核心代码包
│   ├── __init__.py
│   ├── core.py             # DeepEyeSQL 主类 (Pipeline 入口)
│   ├── schema_linking.py   # 模式链接模块
│   ├── value_retrieval.py  # 值检索模块
│   ├── generators.py       # SQL 生成器模块
│   ├── checkers.py         # 检查器与修正模块
│   ├── selection.py        # 选择与投票模块
│   └── utils.py            # 工具函数与 Prompts
├── create_dummy_db.py      # 创建测试数据库脚本
├── main.py                 # 项目运行入口脚本
├── pyproject.toml          # 依赖配置文件 (uv)
└── README_CN.md            # 项目说明文档 (本文档)
```

## 总结
本项目成功复现了 DeepEye-SQL 的核心思想，证明了将 Text-to-SQL 视为软件工程过程（需求-开发-测试-发布）的有效性。尽管在具体组件上进行了简化，但完整的流水线已经打通，具备了进一步扩展和优化的基础。
