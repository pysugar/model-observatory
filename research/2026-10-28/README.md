# 2026-10-28 AA 智能指数 v5 接入

Artificial Analysis 于 **2026-10-27** 把智能指数从 v4.3.2 升级到 v5.0（[发布文章](https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v5)）。本期数据在 [aa-index-v5.json](aa-index-v5.json)，构建时由 `scripts/market_snapshot.py:merge_aa_v5` 作为“最新榜单”的 **AA 智能指数 v5** 页签插入并默认打开；原 v4.3.2 页签改名“AA v4.3.2（旧）”排在其后，内容不变。

## 读取方式

- 第一版（PR #28）在网络受限时用网页检索摘要整理了 12 个分数。
- 网络放行 artificialanalysis.ai 后，[fetch_aa_v5.py](fetch_aa_v5.py) 读取 [AA 公开榜单页](https://artificialanalysis.ai/leaderboards/models) 内嵌的模型数据，重建全部 26 行：总分（页面整数显示，四舍五入；另存两位小数原值）、加权单任务成本、输出速度和九项 v5 子评测。脚本只覆盖 `board.rows`、`pages`（URL + SHA-256，不提交原始 HTML）与 `fetched_at`，方法说明手写维护。
- 检索摘要阶段的 12 个分数全部与原页一致，包括当时只有单一来源的 4 条：Opus 5.5 xhigh 57（未列入最终选录）、Opus 5.5 low 35、Muse Wonder max 43、MiMo-V2.6-Pro 30。
- Kimi K3.1 Pro 的 v4.3 旧分 55 取自 AA 10-23 [发布文章](https://artificialanalysis.ai/articles/kimi-k3-1-pro-launch-benchmarks)；其余旧分取自 10-23 v4.3.2 选录。GPT-6.1 Terra 于 10-26 [发布](https://artificialanalysis.ai/articles/gpt-6-1-terra-pushes-the-cost-efficiency-frontier)，不在旧选录中。Kimi K3 已不在 v5 榜单上。

选录沿用 10-23 的配置，另加 Opus 5.5 low、Kimi K3.1 Pro、GPT-6.1 Terra 与 Gemini 3.5 Flash-Lite。Opus 5.5 xhigh（56.99）略高于 GPT-6 Astra max（56.85），两者都显示 57；为与 AA 文章按模型的排名一致（Opus 5.5 第一、GPT-6 Astra 第二），选录不含 xhigh。

## v5 方法变化

| 类别 | 权重 | 评测 |
| --- | ---: | --- |
| 知识工作 | 25% | AA-Briefcase v1.1 15%、AutomationBench-AA 5%、GDP.pdf 5% |
| 编程 | 25% | FrontierCode 2.0（Cognition，私有）15%、Terminal-Bench 4.0 10% |
| 科学 | 25% | Terminal-Bench-Science 0.1.0 15%、CritPt v2 Hard Subset（私有）10% |
| 通用 | 25% | AA-Omniscience v1.1 15%、HLE-Diamond 10% |

移除 GDPval-AA v2.1、SciCode、AA-LCR v1.1，HLE 原版由 HLE-Diamond 取代。私有或答案不公开的评测约占 60% 权重（v4.2 为 40%，v4.3 为 45%）。旧版 v4.3.2 是 Agents 30% / Coding 20% / General 30% / Scientific Reasoning 20%。

## 排序变化（新旧版本不可直接比较）

| 配置 | v5 | v4.3.2 | v5 单任务成本 |
| --- | ---: | ---: | ---: |
| Claude Opus 5.5 max | 58 | 58 | $10.04 |
| GPT-6 Astra max | 57 | 53 | $6.24 |
| GPT-6.1 Sol max | 55 | 52 | $1.27 |
| Claude Sonnet 5.5 max | 54 | 56 | $10.02 |
| GPT-6.1 Terra max | 51 | — | $0.96 |
| Gemini 4 Argon high | 50 | 53 | $3.84 |
| Muse Wonder Full max | 50 | 56 | — |
| Claude Fable 5.1 max | 49 | 53 | $13.04 |
| Kimi K3.1 Pro（权重未发布） | 46 | 55 | $3.68 |
| Claude Haiku 5.5 max | 36 | 43 | $0.41 |
| Grok 4.7 high | 35 | 46 | $6.18 |
| DeepSeek V4.1 Flash 1017 max | 32 | 45 | $0.60 |
| GLM-5.3 max | 32 | 45 | $5.01 |
| Gemini 3.8 Flash high | 31 | 41 | $7.77 |
| MiMo-V2.6-Pro | 30 | 46 | $0.26 |
| GPT-6 Luna max | 28 | 38 | $0.15 |

OpenAI 三款上升或持平；开放权重模型普遍下降 13–16 分，AA 称最佳闭源与最佳开放权重的差距由 3 分扩大到 12 分，差距在 HLE-Diamond 与 Terminal-Bench-Science 上最大。这与“公开题集被针对性优化”的担忧相符，但 AA 没有给出原因，页面不据此认定任何模型刷榜。私有题集也意味着外部无法复现。

## 仍是 v4.3.2 的部分

AA 已按 v5 重算 6 大领域指数（例如 Opus 5.5 max 的财务与会计由 60.73 变为 59.40），各发布版本页也给出 v5 逐档总分与费用。但本站的能力指数图、发布版本曲线、逐档子评测、甜蜜点与模型档案互相绑定，任务视图又用到了 v5 已移除的 SciCode、GDPval-AA、AA-LCR，需要整体迁移并重新定义任务视图，另行处理。在此之前这些图表都标明 v4.3.2。
