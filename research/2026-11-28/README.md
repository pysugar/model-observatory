# 2026-11-28 模型观测站研究记录

本期从 `060bd74` 版核对更新。11 月 28 日是读取日期。目录收录五家厂商的 35 款型号，跨榜表扩至 30 款，来源索引共 103 条。主页面保留 169 条历史实验记录，各条带有自己的题集与日期。[打开本期报告](../../model-capability-cost.html)

## 榜单与评测

| 来源 | 本期采用的范围和日期 | 核对结果 |
| --- | --- | --- |
| Artificial Analysis | v5.0.2 总榜选录 79 档，含从发布页补入的 Muse Spark 1.3。逐档资料有 26 个发布版本、87 个配置，其中五厂当前系列占 22 版、83 档。来源未注明全榜更新日。 | 每个型号取最高档后，Fable 5.2 max、GPT-6.2 Astra max、Gemini 4 Neon xhigh 依次得 64.77、62.19、61.55 分，每个加权任务为 $26.5386、$3.9979、$6.4448。[总榜](https://artificialanalysis.ai/leaderboards/models) · [方法与版本记录](https://artificialanalysis.ai/methodology/intelligence-benchmarking) |
| LiveBench 2.0 | 11-06 题集共 41 条成绩，选录 31 款。使用官方七个任务套件的权重和费用文件。 | Neon 得 87.4 分，每成功任务 $2.654。新收录 Inkling 2 Small（62.8 分，$0.295）与 Mini（54.9 分，$0.158）。Fable 5.2 和 Astra 显示值同为 84.9，保留精度后 Fable 在前。[成绩](https://livebench.ai/data/20261106/table.csv) · [费用](https://livebench.ai/data/20261106/cost.csv) |
| Arena | 固定 11-26 的数据集版本。Text Style Control 为 11-22（全榜 427 项），WebDev 为 11-23（162 项），Agent 与好评指标为 11-22（69 个 Agent 榜条目）。 | Text 前三是 Carbon、Argon、Neon 的 high 档。Astra 与 Sol 6.2 max 在 Text 分列 57、64，WebDev 分列 7、8，Agent 分列 7、11。[固定版本数据集](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/tree/4e9c2f140324df03c630a1fe91aaeacfb241f1ca) |
| Scale SEAL | 11-28 核对 HLE Diamond、HSS、MultiChallenge、RLI 及 SWE-Bench Pro V2 的 Full、HARD 页。各页未披露全榜日期。HLE Diamond 选录 32/33 条。 | HLE Diamond 的 high 档中，Fable 5.2 为 72.40%，Astra 为 66.90%，Neon 为 65.30%。Neon 的 95% 区间为 ±2.89 个百分点，与 Astra 的 ±2.90 重叠。Opus 5.5、Argon、Hydrogen 同列第 8。HSS 中 Neon xhigh 为 75.86%（±3.40）。[HLE Diamond](https://labs.scale.com/leaderboard/hle-diamond) · [HSS](https://labs.scale.com/leaderboard/hss) |
| Vals AI | 行业指数 v2.2 的榜面更新日为 11-21。单列的 Terminal-Bench 仍采用其 11-19 发布的 4.0 版。 | 行业指数前三为 Fable 5.2（70.06%，每测试 $17.94）、Sonnet 5.5（69.45%，$16.18）、Neon（69.23%，$7.40）。[Vals Index](https://www.vals.ai/benchmarks/vals_index) · [Vals Terminal-Bench 4.0](https://www.vals.ai/benchmarks/terminal-bench-4) |
| ARC Prize | 11-18 发布的 Neon 结果按推理档、题集与完成情况记录。 | Neon medium 在 ARC-AGI-1/2 半私有集得 98.5% / 93.8%，其中有一题未完成。三个 ARC-AGI-3 档位均未完成。[Neon 结果及运行说明](https://arcprize.org/results/google-gemini-4-neon) |
| OpenRouter | 截至 11-27 的滚动 7 日文本用量，保留前十名。星号表示部分日期的 BYOK 流量触及统计上限。 | DeepSeek V4.1 Flash 1017 以 83.1 万亿 token 居首，Hy4 flash 以 38.7 万亿居次。旗舰 Hy4 在 AA 得 34.57 分，每任务 $1.0311。两款型号在跨榜表各占一行。[用量榜](https://openrouter.ai/rankings) · [Hy4](https://huggingface.co/tencent/Hy4) · [Hy4 flash](https://huggingface.co/tencent/Hy4-flash) |

## 发布与价格

- 智谱于 11-23 通过 GLM Coding Plan 开放 GLM-5.4，支持 1M 上下文、128K 输出。官方将模型 API 开放与安全评估挂钩，并把开放权重列为后续计划。本期 AA 总榜尚无其综合分。[发布公告](https://z.ai/blog/glm-5.4) · [模型规格与可用性](https://docs.z.ai/guides/llm/glm-5.4)
- OpenAI 于 11-23 向 ChatGPT 付费层推出针对日常对话调整的 Sol 版本，11-24 在 Responses API 新增四项医疗配置。通用 API 配置保留原有独立评测身份。[ChatGPT 更新](https://help.openai.com/en/articles/6825453-chatgpt-release-notes) · [API 更新](https://developers.openai.com/api/docs/changelog)
- Google Carbon 与 Argon 的输入 / 输出价（每百万 token）在 11-30 前为 $2 / $10，自 12-01 起为 $4 / $20。GPT-5.6 Sol 的 $4 / $20 优惠也在 11-30 结束，官方尚未给出后续费率，预算工具以缺值表示。Claude API 将于 11-30 退役 Sonnet 4.5，迁移型号为 Sonnet 5.5。[Google 定价](https://aistudio.google.com/docs/pricing) · [GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol) · [Anthropic 生命周期](https://platform.claude.com/docs/en/about-claude/model-deprecations)

## 数据与复算

AA 的 4.1 验证器复用 66 道终端任务，FrontierCode-AA 2.0 也重新评审了此前的作答。编程任务视图取两项百分比的等权均值。榜单与发布页以配置 UUID 对齐，使用 4.1 的独立字段，保留来源原始精度和缺测值。可对照[总榜快照](aa-index-v5.json)和[逐档输入](aa-v5-series.json)。

跨榜表逐来源选择同一型号的最高实测配置，按原始精度计算名次。同分并列，缺测留空，用量不参与名次跨度。榜单原始文件分别见 [Arena](arena.json)、[LiveBench](livebench.json) 和 [Scale 与 OpenRouter](manual-boards.json)。各来源保留 URL 和内容指纹。厂商发布与实测资料见[来源索引](catalog-supplement.json)、[档案证据](model-effort-profiles.json)和[本期说明](notes.json)。社区经验沿用 [11-19 核对记录](../2026-11-19/community-consensus.json)。

在仓库根目录设置 `OBS_PYTHON` 为本机配置的 Python 解释器后，可离线重建和核对报告。

```sh
uv run --no-project "$OBS_PYTHON" research/2026-11-28/build_snapshot.py
uv run --no-project "$OBS_PYTHON" build_report.py
uv run --no-project "$OBS_PYTHON" -m unittest discover -s tests
uv run --no-project "$OBS_PYTHON" scripts/publish.py build --site-dir test-results/refresh-2026-11-28/site
uv run --no-project "$OBS_PYTHON" scripts/publish.py check --site-dir test-results/refresh-2026-11-28/site
```

[AA 采集脚本](refresh_aa.py)和[其他榜单采集脚本](refresh_boards.py)用于联网核对。复现本期数字时使用本目录的冻结输入。

本地验收通过 80 项单元测试、静态打包检查和 Chrome 桌面与窄屏回归（1440、390、320 和 305 像素）。市场快照、离线 HTML、JSON 和 CSV 在重复构建后逐字节一致。75 个来源地址的内容指纹核对通过。Model Factbook 的三个入口均返回 HTTP 200，跨榜和证据页的目标文章保留各自的引流参数。
