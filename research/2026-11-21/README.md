# 2026-11-21 模型与评测更新

本期以 `bfbfe4e` 为研究基线。11 月 21 日是观察站读取公开资料的日期。下表另列机构实际标注的题集日期、榜单日期或用量截止日。模型档案覆盖五家厂商的 35 款型号，跨榜对照收录 26 款。默认 AA 视图为 v5，v4.3.2 和 169 条历史实验记录可独立查看。

## 榜单读数

| 来源 | 本期范围与时间 | 值得关注的变化 |
| --- | --- | --- |
| Artificial Analysis | v5 总榜选录 76 档。发布页覆盖 26 版、87 档，均有科学与编程的四项原始成绩。榜单未披露整体更新日。 | 以各型号最高分计，Fable 5.2 max 得 64.56，GPT-6.2 Astra max 得 62.14，Neon xhigh 得 61.40。新增跨厂参照 Qwen4 Max（42.89 分，每个加权任务 $3.2681）。[AA v5 原榜](https://artificialanalysis.ai/leaderboards/models) |
| LiveBench 2.0 | 11-06 题集已公布 39 条成绩。报告选录 29 款，按官方七个任务套件的权重和费用文件复算。 | Neon 综合 87.4，每成功任务 $2.654。Fable 5.2 与 Astra 均显示 84.9，原精度和费用分别是 84.883／$9.850 与 84.872／$1.941。来源未披露原生档位。[成绩](https://livebench.ai/data/20261106/table.csv) · [费用](https://livebench.ai/data/20261106/cost.csv) |
| Arena | Text Style Control（11-19）、WebDev（11-20）、Agent（11-18）全榜共有 426、161、68 条。 | Text 前三均为 high 档，依次是 Carbon、Argon、Neon。Astra 与 Sol 的 max 分别列 Text 第 55、64，WebDev 第 5、8。Fable 5.2 的 xhigh 领跑 WebDev，max 领跑 Agent。Qwen4-Max xhigh 在 WebDev 列第 9。[官方数据集固定版本](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/tree/abbae57d7888809e8b686f8548a6f77c81fa03f4) |
| Scale SEAL | 六张专项榜于 11-21 读取，全榜更新日未披露。HLE Diamond 页面共 27 项，按观察站目录范围选录 26 项。 | HLE Diamond 上 Fable 5.2 high 得 72.40%，Astra high 66.90%，Sol high 56.50%。视觉推理 HSS 中 Neon xhigh 得 75.86%（±3.40 个百分点），Carbon high 得 71.10%（±3.60），95% 区间重叠。[HLE Diamond](https://labs.scale.com/leaderboard/hle-diamond) · [Humanity’s Sixth Sense](https://labs.scale.com/leaderboard/hss) |
| Scale SEAL 软件工程与交付 | SWE-Bench Pro V2 由 642 题全集与 51 题高难集组成，保留每行的运行环境和来源名次。另读取 MultiChallenge 大模型组及 RLI。 | Claude Opus 5（Claude Code，xhigh）两个子集分别为 99.40% 和 98.00%。全集中 Gemini 4 Argon（mini-swe-agent，high）和 Fable 5.1（Claude Code，high）均列来源第 2。MultiChallenge 由 Carbon high（85.90%）领先，RLI 上 Fable 5.2（41.25%）和 Opus 5.5（21.25%）居前。[Full](https://labs.scale.com/leaderboard/swe_bench_pro_public_v2?tab=full) · [HARD](https://labs.scale.com/leaderboard/swe_bench_pro_public_v2?tab=hard) · [MultiChallenge](https://labs.scale.com/leaderboard/multichallenge?tab=large) · [RLI](https://labs.scale.com/leaderboard/rli) |
| OpenRouter | 截至 11-20 的滚动七日 Text 榜，保留前十和免费路由标记。 | DeepSeek V4.1 Flash 1017 以 62.4 万亿 token 居首。GPT-6 Luna 第 4（8.74 万亿），Opus 5.5 第 5（7.25 万亿）。该榜衡量平台 token 用量。[OpenRouter Rankings](https://openrouter.ai/rankings) |

## 工作任务与模型发布

- **行业任务。** Vals 11-19 行业指数中，Fable 5.2 以 71.31% 居首，每测试 $17.94。Neon 为 70.87%／$7.40。Excel 财务建模专项中，Fable 5.2 为 77.38%／$6.67，Neon 为 76.46%／$3.82，Astra 为 76.03%／$2.80。[Vals Index v2.2](https://www.vals.ai/benchmarks/vals_index) · [Excel Modeling v1.1](https://www.vals.ai/benchmarks/emb-v1-1) · [Terminal-Bench 4.0](https://www.vals.ai/benchmarks/terminal-bench-4)
- **研究工作。** Epoch 11-17 发布了四类真实工作样本的人工评阅。Astra 平均 65%，Fable 5.2 高 17 个百分点。数据中心分析一项中，Fable 5.2 与 Opus 5.5 达到了该机构的外包交付标准，仍需编辑。METR 11-20 的季度报告覆盖至 Opus 5.5 与 GPT-6 Astra。在 TH1.1 和 TH2 合并题集上，前沿系统以 50% 成功率可完成的任务，其对应的人类工作时长约每 3.6 个月翻倍。报告还记录了缺少明确反馈时的判断失误。[Epoch AI](https://epoch.ai/publications/how-good-are-fable-5-2-and-gpt-6-2-astra-at-real-work) · [METR](https://metr.org/blog/2026-11-20-q4-2026-capability-update/)
- **厂商科学评测。** 11-20 公布的 MedChemBench 采用 99 道回顾性问题。同为 xhigh 档，GPT-6.2 Astra、GPT-6 Astra、GPT-6.1 Sol 的得分占可得分的 84.5%、83.3%、82.0%。这是发布方对已发表材料的单次无工具评测，模型可能见过原始材料。[OpenAI 报告](https://openai.com/index/introducing-medchembench/)
- **新题泛化。** ARC Prize 11-17 公布了 GPT-6.2 在 ARC-AGI-3 的两种结果。标准框架下 Astra max 为 70.3%，Sol max 为 54.9%。使用厂商适配器后分别为 99.8% 和 98.2%。模型档案分别标出框架。[ARC Prize 原始结果](https://arcprize.org/results/openai-gpt-6-2)
- **价格。** AA 将 Gemini 4 Argon high 的加权单任务费用从 $4.9733 调整为 $9.9466，得分仍为 50.41。AA 的 Argon 和 Carbon 均采用每百万输入／输出 token $4／$20。Google 官方两款模型在 11-30 前（含当日）仍为 $2／$10，12-01 起执行 $4／$20。[AA Argon 发布页](https://artificialanalysis.ai/zh/models/releases/gemini-4-argon) · [Google 定价](https://aistudio.google.com/docs/pricing#gemini-4-argon)
- **实时模型与跨厂参照。** OpenAI 11-19 开放 GPT-Live-1.1，活动通话 $0.05/分钟，WebRTC 待机 $0.02/分钟。Google 同日通过付费 API 开放 Genie 4，视频输出约 $0.10/秒（含音频）。阿里 11-16 发布的 Qwen4-Max 已进入跨榜对照。Kimi K3.1 Pro 已有官方权重分片，当前榜单据此校正开放权重标注。xAI 的 `grok-build-0.1` 已于 11-19 停服。[OpenAI 模型页](https://developers.openai.com/api/docs/models/gpt-live-1.1) · [Google 更新记录](https://aistudio.google.com/docs/changelog#11-19-2026) · [阿里巴巴公告](https://www.alibabagroup.com/en-US/document-2060139246777270272) · [Moonshot 权重](https://huggingface.co/moonshotai/Kimi-K3.1-Pro) · [xAI 发布记录](https://docs.x.ai/developers/release-notes)

## 数据与复算

11 月 22 日补录 MiMo V2.6 Pro、MiMo V2.6 Flash、GLM 5.3 Flash、MiniMax-M3 的逐项成绩。四份原始发布页与本快照记录的 SHA-256 一致。科学与编程合计占 AA v5 总分的 50%，单项贡献按原始百分比乘该项权重估算。同日核对经济学指数说明，知识工作与长文档分别占 30% 和 15%。[AA 总指数方法](https://artificialanalysis.ai/methodology/intelligence-benchmarking) · [AA 行业指数方法](https://artificialanalysis.ai/methodology/capability-indexes)

[AA 榜单](aa-index-v5.json) 和[发布系列](aa-v5-series.json)用 AA 的模型 UUID 匹配到具体档位。[Arena](arena.json)保存固定数据集版本和来源名次。[LiveBench](livebench.json)保存题集、权重和费用文件的指纹。[Scale 与 OpenRouter](manual-boards.json)保存每个来源的 URL、SHA-256 和原始单位。Scale 同页可能含多套数据，采集时按可见模型列表的完整顺序选取对应标签页。SWE-Bench 的并列名次按来源披露的置信区间规则保留。

[市场快照](market-snapshot.json)由上述冻结输入和[本期更新文字](notes.json)生成。[目录与来源](catalog-supplement.json)、[档案补充证据](model-effort-profiles.json)收录厂商规格与评测报告。机构报告中的工作样本与行业趋势仅供对应任务参考。社区经验沿用 [11-19 的 34 条核对记录](../2026-11-19/community-consensus.json)，每条保留自己的日期。

从仓库根目录执行下列命令可离线重建。先将 `OBS_PYTHON` 指向当前机器为本项目配置的 Python 解释器。

```sh
uv run --no-project "$OBS_PYTHON" research/2026-11-21/build_snapshot.py
uv run --no-project "$OBS_PYTHON" build_report.py
uv run --no-project "$OBS_PYTHON" -m unittest discover -s tests
uv run --no-project "$OBS_PYTHON" scripts/publish.py build --site-dir test-results/refresh-2026-11-21/site
uv run --no-project "$OBS_PYTHON" scripts/publish.py check --site-dir test-results/refresh-2026-11-21/site
uv run --no-project "$OBS_PYTHON" scripts/smoke.py --site-dir test-results/refresh-2026-11-21/site --output-dir test-results/refresh-2026-11-21/smoke --browser-channel chrome
```

[AA 采集脚本](refresh_aa.py)和[其余榜单采集脚本](refresh_boards.py)用于联网核对。动态页面可能在同一题集或版本下追加结果，复现本期页面应使用本目录的冻结输入。

本地验收通过 79 项单元测试、两次一致的离线重建及静态打包校验。Chrome 覆盖 1440、390、320 像素视口，另检查 305 像素的窄屏布局、榜单并列名次、版本切换和 CSV 下载。本次核对 75 个来源地址，其中 71 个比对了内容指纹。验收日志和截图保存在 `test-results/refresh-2026-11-21/`。
