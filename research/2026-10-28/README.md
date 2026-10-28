# 2026-10-28 AA 智能指数 v5 接入

Artificial Analysis 在 2026 年 10 月下旬把智能指数从 v4.3.2 升级到 v5.0。本期把 v5 总分整理为 [aa-index-v5.json](aa-index-v5.json)，构建时由 `scripts/market_snapshot.py:merge_aa_v5` 作为“最新榜单”的 **AA 智能指数 v5** 页签插入，设为默认打开的第一个页签；原 v4.3.2 页签改名“AA v4.3.2（旧）”排在其后，内容不变。

## 读取方式与限制

云端会话的网络策略只放行搜索，artificialanalysis.ai 与转载报道原页都无法直接打开。全部数值来自 2026-10-28 的网页检索摘要，逐行标注：

- **多源一致**：至少两个独立摘要给出同一数值（8 条）。
- **单一来源**：只在一处摘要出现（4 条：Opus 5.5 xhigh / low、Muse Wonder max、MiMo-V2.6-Pro），待原页复核。

v5 的费用、输出速度和九项子评测分数没有取得，保持 `null`，不沿用 v4.3.2 费用。v5 数据不进入逐档曲线、甜蜜点、模型档案或任何计算；这些仍基于冻结的 v4.3.2 输入。

## v5 方法变化

| 类别 | 权重 | 评测 |
| --- | ---: | --- |
| 知识工作 | 25% | AA-Briefcase v1.1 15%、AutomationBench-AA 5%、GDP.pdf 5% |
| 编程 | 25% | FrontierCode 2.0（私有）15%、Terminal-Bench 4.0 10% |
| 科学 | 25% | Terminal-Bench-Science 0.1.0 15%、CritPt v2 Hard Subset（私有）10% |
| 通用 | 25% | AA-Omniscience v1.1 15%、HLE-Diamond 10% |

移除 GDPval-AA v2.1、SciCode、AA-LCR v1.1，HLE 原版由 HLE-Diamond 取代。私有或答案不公开的评测约占 60% 权重（v4.2 为 40%，v4.3 为 45%）。旧版 v4.3.2 是 Agents 30% / Coding 20% / General 30% / Scientific Reasoning 20%。

## 排序变化（新旧版本不可直接比较）

| 配置 | v5 | v4.3.2 |
| --- | ---: | ---: |
| Claude Opus 5.5 max | 58 | 58 |
| GPT-6 Astra max | 57 | 53 |
| GPT-6.1 Sol max | 55 | 52 |
| Gemini 4 Argon high | 50 | 53 |
| Kimi K3.1 Pro（权重未发布） | 46 | 55 |
| Muse Wonder max | 43 | 52 |
| Claude Haiku 5.5 max | 36 | 43 |
| DeepSeek V4.1 Flash 1017 max | 32 | 45 |
| GLM-5.3 max | 32 | 45 |
| MiMo-V2.6-Pro | 30 | 46 |

OpenAI 两款上升；开放权重模型普遍下降 9–16 分，最佳闭源与最佳开放权重的差距由约 3 分扩大到约 12 分。这与“公开题集被针对性优化”的担忧相符，但报道对原因只是推测，页面不据此认定任何模型刷榜。私有题集也意味着外部无法复现。

## 待补

- Sonnet 5.5、Fable 5.1、Grok 4.7、Gemini 3.8 Flash、GPT-6 Luna、Muse Wonder Full、Qwen3.8 Max 等未检索到 v5 总分。
- 一条“10-27 v5.0 快照 high 30.5”的 Gemini 3.8 Flash 摘要未明确对应型号，未采用。
- 网络放行 artificialanalysis.ai 后，按原页补录费用、速度、子评测，并复核单一来源行。

## 主要来源

- [AA：Announcing Intelligence Index v5](https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v5)、[方法页](https://artificialanalysis.ai/methodology/intelligence-benchmarking)
- [TechApple](https://global.techapple.com/2026/10/artificial-analysis-intelligence-index-v5/)、[Startup Fortune](https://startupfortune.com/claude-opus-55-takes-top-spot-as-artificial-analysis-launches-intelligence-index-v5/)、[Trending Topics](https://www.trendingtopics.eu/artificial-analysis-index-v5-open-weight-models/)、[OfficeChai](https://officechai.com/ai/artificial-analysis-launches-intelligence-index-v5-with-majority-private-datasets-openai-models-gain-muse-wonder-kimi-drop/)、[AlphaSignal](https://alphasignal.ai/news/artificial-analysis-rebuilds-intelligence-index-v5-with-private-coding-tests)
