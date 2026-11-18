# 2026-11-18 晚间：GPT-6.2 首日评测与风评

上午的 [11-18 研究记录](../2026-11-18/README.md) 已随 PR41 发布；本目录是同一天晚间（Asia/Taipei 约 22:50 起）的补充读取，不改写上午快照。研究未付费运行模型，核验日期仍记为 2026-11-18。

## 第三方评测

| 来源 | 本期变化 | 处理 |
| --- | --- | --- |
| [AA](https://artificialanalysis.ai/leaderboards/models) | 分数与上午逐项一致。Sol 6.2 补齐五档任务费用：low $0.18、medium $0.41、high $0.56、xhigh $0.65、max $1.01；GPT-6.2 补入每任务耗时。其余型号耗时有小幅重测波动。 | `aa-index-v5.json` / `aa-v5-series.json`。领域受限的 Astra for Law 6.2 不纳入通用选型。 |
| AA Carbon 费用口径 | AA 改按 12-01 常规价 $4 / $0.20 / $20 计算 Gemini 4 Carbon，任务费用升约四成（high $5.48 → $7.76），令牌用量不变；Argon 仍按 $2 / $10。 | [Google 价格页](https://aistudio.google.com/docs/pricing)当日核对：Carbon / Argon 优惠仍至 11-30。照录 AA 数值并在榜单说明、发布版本与五厂速览中注明口径，两者费用不可直接比较。 |
| [LiveBench](https://livebench.ai/) | 11-06 题集在 11-15 后追加 GPT-6.2：Astra 84.9（与 Fable 5.2 并列第一）、每成功任务 $1.941；Sol 6.2 80.3、$0.523，低于 6.1 Sol 的 81.4。原始记录 35 → 38 项。 | 计分与费用公式未变；同题集内可比，不跨题集算涨跌。 |
| [Arena 官方数据集](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset) | revision `b17ca88`：WebDev / Agent 发布于 11-15，Fable 5.2 仍居第一；文本榜仍为 11-11。均未收录 GPT-6.2。 | 三张显示榜重新选录 43 / 43 / 42 项。 |
| [Scale HLE Diamond](https://labs.scale.com/leaderboard/hle-diamond) | 新增 Muse Ember；仍无 GPT-6.2。选录 20 项。 | 发布日期未披露，保持 null。 |
| [OpenRouter](https://openrouter.ai/rankings) | 周用量截至 11-17；腾讯 Hy4 Flash 新上榜第二，GPT-6.2 未进前十。 | 只代表平台调用热度。 |

只作文字参考的补充证据（写入 `model-effort-profiles.json`，不进入拐点或任何计算）：

- [AA 发布分析](https://artificialanalysis.ai/articles/openai-has-the-2-model-in-the-intelligence-index-with-the-release-of-gpt-6-2-astra-and-gpt-6-2-sol)：Coding Agent Index（Codex，max）Astra 6.2 与 GPT-6 Astra 持平，Sol 6.2 比 6.1 Sol 低 3 分，主要来自 SWE-Atlas-QnA-AA 下降 14 分。绝对指数只在图中，未转录。
- [Vals AI Terminal-Bench 4.0](https://www.vals.ai/benchmarks/terminal-bench-4)：Astra 6.2 63.13% / 每题 $4.69，Sol 6.2 60.61% / $1.13，GPT-6 Astra 59.60%，6.1 Sol 55.05%，Fable 5.2 与 Opus 5.5 65.15%。页面更新戳为 11-16，未注明档位。
- [ARC Prize](https://arcprize.org/leaderboard)（认证）：Astra 6.2 ARC-AGI-2 95.8%、ARC-AGI-3 标准框架 70.3%；Sol 6.2 ARC-AGI-2 85.8%（6.1 Sol 94.2%）、ARC-AGI-3 54.9%。

## 社区声音（`community-consensus.json`）

沿用 10-29 的 23 条并新增 3 条，均打开原页核对，只作文字参考：

1. 早期测试者反馈偏负面（[VentureBeat](https://venturebeat.com/technology/essentially-unusable-openai-launches-gpt-6-2-astra-and-sol-to-negative-reception-from-ai-power-users) 汇总 Matt Shumer、Theo Browne、Ethan Mollick、Every 的意见）：难以引导、端到端构建常提前停止；正面反馈在 3D、动效与 computer use。X 原帖（402）和 Every 原文（404）无法直接读取，正文注明为转述。
2. [OpenAI 系统卡](https://deploymentsafety.openai.com/gpt-6-2-astra-sol/blocker-deception)：诱发型 Blocker Deception 中 Astra 6.2 省略已知阻碍 22.28%（GPT-6 Astra 11.09%）；Codex 开发者提示能显著减少，但不用于直接 API 请求。Sol 6.2 的数值只在图中，未转录。
3. [HN 发布讨论](https://news.ycombinator.com/item?id=50535230)（1,318 赞）：Sol 与 Astra 取舍分歧明显，部分用户认为 Sol 6.2 更需引导、不如 6.1。

OpenAI 发布文章与 The New Stack 对自动读取返回 403，未引用其中的说法。

## 页面

- 本期更新栏原先会把 AA 变更说明与市场快照第一条重复显示（上午版出现两条同名条目）；改为不同内容，并加单元测试防止标题重复。
- 证据表的规格行更正为 34 型号；多源榜单行改为各来源本期日期。

## 复算

```sh
python3 research/2026-11-18-pm/refresh_aa.py
python3 research/2026-11-18-pm/refresh_boards.py
python3 research/2026-11-18-pm/build_snapshot.py
python3 build_report.py
python3 -m unittest discover -s tests -v
python3 scripts/publish.py build
python3 scripts/publish.py check
python3 scripts/smoke.py --browser-channel chrome --output-dir test-results/refresh-2026-11-18-pm/smoke
```

抓取缓存在忽略目录 `test-results/refresh-2026-11-18-pm/aa-pages/`。Arena 固定 revision，LiveBench 出现新题集时脚本会停止导入，Scale / OpenRouter 遇到未复核的型号名也会停止。
