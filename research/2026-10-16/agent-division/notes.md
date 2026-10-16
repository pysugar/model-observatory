# 固定主控后的任务分工

用户前提：主控固定 gpt-6.1-sol / high。此次仅补充报告，未修改实际代理配置、创建代理任务、调用付费模型或开展中文实验。

## 推荐与证据

通用子 agent 从 Sol 6.1 medium 起步；简单辅助用 Luna 6 none / low；重要独立评审可用 Opus 5.5 high，截图入口用 Opus 5 high。长会话压缩在可独立控制时优先 Sol low，因为遗漏关键状态会影响后续工作。以上是任务匹配推断，非同工作流实测最优配置。

`routing-evidence.json` 保留报告原有 Luna 6 的 low / medium / high 三条 Vulcan 编码记录：分别通过 0 / 0 / 2 道，总数均 23。它们只用于说明不能将简单辅助定位外推到复杂工程子任务，不能证明 Luna 的标题、提取或 OCR 质量。中文理解和输出均未专项实测。

## 框架事实

- OpenClaw 子 agent 可设 model / thinking 默认，也能按 sessions_spawn 覆盖；显式覆盖可避免继承主控 high。不同 runtime 的支持条件不能互相代替。
- Hermes 当前 delegate_task 没有逐任务 model 参数，统一 delegation 路由。官方实现确认 delegation.reasoning_effort 优先于父级设置；未设或未能解析时继承父级。
- Hermes /review 是工作产物审查，有独立 auxiliary.review 模型路由，默认使用主模型；具体评审 effort 仍须在本地实际请求验收，报告未虚构可用字段。
- Hermes background_review 是记忆和技能整理。同模型 fork 继承主控 effort，独立 low 设置无效；换模型后可设置独立 effort，但输入变为摘要，失去与主控相同的缓存前缀。不能只按模型单价判断总成本。
- OpenClaw 内置 compaction 可设 thinkingLevel；原生 Codex app-server compaction 不接受此覆盖。heartbeat 也有单独路由，不受 subagents 默认统一控制。
- Sol 的工具调用使用 Responses。Luna 带 reasoning 的工具调用使用 Responses；Chat Completions 仅在 none 时支持其工具调用。未核验用户 provider、版本或真实 wire 请求。

## 策略假设与验收

同时 2 个子 agent、1 层委派只是起步建议。工作须可独立划分，明确上下文、可写范围、验收、预算及停止条件。补齐证据并纠偏一次仍重复同错，交回固定 high 主控或独立专家；xhigh 仅用于具体难点，不修改固定主控。

比较策略时合计主控、子 agent、辅助调用、工具、重试和缓存成本，记录完整完成率、人工纠偏、端到端耗时、实际回退、压缩漏项和中文质量。预算耗尽不算成功。

`manifest.json` 保存 12 个来源快照的 URL、实际抓取时间和 SHA256。框架源码仅作为只读材料，未执行。原 166 条评测记录、20 个 AA 配置和 Opus 补充证据保持原值。
