# AI 协作开发指南 (AI-Assisted Development Guide)

> 本文档解决"跨 Session 上下文丢失"问题，确保每次新 Session 都能快速恢复进度。

## 📌 核心原则

**每次 Session 开始时，AI 必须先阅读以下文件（按顺序）：**
1. `docs/ai_context.md` - 当前进度与待办
2. `docs/coding_standards.md` - 编码规范
3. 相关功能的设计文档

---

## 📄 关键上下文文件

### 1. `docs/ai_context.md` (每次 Session 必读)
**用途**：告诉 AI "我们在哪，接下来做什么"

```markdown
# AI Context 上下文

## 当前版本
v0.1.0-dev

## 当前阶段
[ ] 需求分析 -> [x] 架构设计 -> [ ] 开发中 -> [ ] 测试

## 上次 Session 进度
- 完成了 xxx 功能的基础框架
- 正在开发 xxx 模块

## 本次 Session 目标
- [ ] 完成 xxx 接口
- [ ] 编写 xxx 测试

## 重要决策记录
- 2026-01-16: 选择 LangGraph 而非 AutoGen (原因见 requirements_analysis.md)

## 待解决问题
- Q: xxx 如何处理？
```

### 2. `docs/coding_standards.md` (编码规范)
**用途**：约束 AI 的代码风格

```markdown
# 编码规范

## Python
- 使用 Python 3.11+
- 类型注解：所有函数必须有类型注解
- 文档字符串：使用 Google 风格
- 格式化：使用 Black + isort
- 变量/函数命名：snake_case
- 类命名：PascalCase

## 注释要求
- 每个模块开头：说明功能和职责
- 复杂逻辑：解释"为什么"而不是"是什么"
- 中文注释优先（个人项目，方便自己阅读）

## 测试要求
- 每个功能模块必须有对应的测试文件
- 测试命名：test_<功能名>.py
- 提交前运行：pytest
```

### 3. 功能设计文档 (按需创建)
每个功能模块一个文档，例如：
- `docs/design/memory_system.md`
- `docs/design/proactive_messaging.md`

---

## 🔄 Session 切换流程

### 结束 Session 时
1. 更新 `docs/ai_context.md` 中的"上次进度"
2. 将未完成任务写入"本次目标"
3. 记录任何重要决策

### 开始新 Session 时
**复制以下 Prompt 给 AI：**

```
我们正在开发 AI 陪伴助手项目。

请先阅读以下文件了解项目背景：
1. docs/ai_context.md - 当前进度
2. docs/coding_standards.md - 编码规范
3. docs/requirements_analysis.md - 需求与架构

阅读完成后，请确认你理解了：
- 我们目前在做什么
- 接下来要做什么
- 需要遵循的编码规范

然后我们继续开发。
```

---

## 🎯 给 AI 的补充指令

在 Session 中可以随时提醒 AI：

| 情况                   | 指令示例                                   |
| :--------------------- | :----------------------------------------- |
| AI 代码风格偏离规范    | "请遵循 coding_standards.md 的规范"        |
| AI 忘记了之前的决策    | "请查看 ai_context.md 中的决策记录"        |
| 需要 AI 记录重要决策   | "请把这个决策记录到 ai_context.md"         |
| 需要 AI 更新进度       | "请更新 ai_context.md 的进度"              |

---

## 📁 推荐的 `docs/` 目录结构

```
docs/
├── ai_context.md           # [必需] AI 上下文（每次 Session 必读）
├── coding_standards.md     # [必需] 编码规范
├── requirements_mvp.md     # 需求文档
├── requirements_analysis.md # 需求分析与技术选型
├── development_protocol.md # 开发协议
├── tech_stack_decisions.md # 技术决策日志
├── daily_progress.md       # 每日进度
├── prompt_log.md           # 重要 Prompt 记录
└── design/                 # [按需] 功能设计文档
    ├── memory_system.md
    ├── proactive_messaging.md
    └── ...
```
