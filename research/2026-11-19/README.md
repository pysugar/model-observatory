# 2026-11-19：Gemini 4 Neon 上线、多机构评测刷新与社区最佳实践补全

本目录基于基线 `1de7609`（PR #47 合并后）于 2026-11-19 全量重读多方评测机构、官方规格与社区实践，不改写既有历史目录（`2026-10-*`、`2026-11-15`、`2026-11-18`、`2026-11-18-pm`）。研究未付费运行模型，所有数值均来自 2026-11-19 实测抓取的公开一手页面或官方数据集。

## 新发布模型与官方价格复核

- **新增 Google Gemini 4 Neon（`gemini-4-neon`，2026-11-18 发布）**：定位 Gemini 4 系列的快速、高性价比主力，1,048,576 统一上下文、65,536 同步输出（长解码最高 1M）、全多模态输入（文本/图片/音频/视频/PDF → 文本），原生档位 `low / medium / high（默认）/ xhigh`，全上下文统一标准价 **$3.00 / $0.15（隐式缓存 95% 折扣）/ $15.00**（无 >200k 阶梯涨价，目前仅 Paid Tier）。来源：[Google Neon 文档](https://aistudio.google.com/docs/models/gemini-4-neon)、[更新说明](https://aistudio.google.com/docs/whats-new-gemini-4-neon)、[Google 价格页](https://aistudio.google.com/docs/pricing)。
- **价格与迁移复核**：
  - **GPT-5.6 Sol** 优惠价（$4 / $20）官方已延长至 **2026-11-30**（原 11-21）。
  - **Gemini 4 Carbon / Argon** 优惠价仍持续至 **2026-11-30**（12-01 起均恢复 $4 / $20）；AA v5 仍按 12-01 常规价计 Carbon、按优惠价计 Argon，两者 AA 费用口径差异继续显式标注。
  - **GPT-6.2 Astra / Sol** 官方迁移与提示指南（[OpenAI latest-model](https://developers.openai.com/api/docs/guides/latest-model)）明确：Responses API 顶层 `instructions` 现拼接在 `input` 之后（需改为 `input` 首条 `developer` 消息以保缓存命中）；中途改动历史前缀或切低档位会丢弃已缓存 reasoning items；不支持 Flex tier，改提供公测 **Background mode**（2h 省 30%、8h 省 40%）。
  - **Claude 生命周期**：核对 [Anthropic 弃用文档](https://platform.claude.com/docs/en/about-claude/model-deprecations)，Opus 4.7 / Sonnet 4.6 仍为活跃/兼容型号；Grok 4.8 仅在消费端灰度推送，公开 API 主力仍为 Grok 4.7。

## 多方评测机构刷新

| 来源 | 本期变化 | 处理 |
| --- | --- | --- |
| [AA v5](https://artificialanalysis.ai/leaderboards/models) | 新增 **Gemini 4 Neon** 四档完整评测：low 44.08（$0.75 / 3.7m）、medium 54.86（$1.90 / 8.3m）、high **59.62**（$3.74 / 14.8m，GDP.pdf 33.4%）、xhigh **61.40**（总榜并列第三，$6.44 / 21.5m，输出 ~110 tok/s 约为 Carbon ~55 tok/s 两倍）。共 26 个发布版本 / 87 个配置（五家主力 22 版 / 83 档），榜单 75 行。 | `aa-index-v5.json` / `aa-v5-series.json`。v5 与 v4.3.2 严格隔离，领域受限型号不纳入通用选型。 |
| [Arena 官方数据集](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset) | revision `b9863c6`：**Text（422 模型）、WebDev（160）、Agent（68）、Praise/Complaint（68）三榜全部刷新至 2026-11-18**。Text 榜 Google 包揽前三：Carbon 1525.9、Argon 1520.6、Neon 1518.5；WebDev 榜 GPT-6.2 Astra 空降 #3（1780.6）、Neon #6（1763.9）、GPT-6.2 Sol #8（1756.7，高于 6.1 Sol #10）；Agent 榜 Fable 5.2 仍居 #1（IPS 0.2742，表扬率 0.6872），Opus 5.5 #2（0.1863），Neon #3（0.1841，表扬率 0.4447，与 Opus 5.5 在置信区间内打平），Astra 6.2 #6（0.1522），Sol 6.2 #11（0.1131）。 | `arena.json` 与 `market-snapshot.json` 三榜选录 42 / 45 / 43 项；跨榜对照扩展为 25 款重点型号。 |
| [LiveBench](https://livebench.ai/) | 2026-11-19 重读确认仍为 11-06 题集（38 行），GPT-6.2 Astra（84.9 / $1.941）与 Fable 5.2（84.9 / $9.85）并列第一；尚未收录 Gemini 4 Neon。 | 保持 `source_updated_at: 2026-11-06`、`checked_at: 2026-11-19`。 |
| [Scale SEAL](https://labs.scale.com/leaderboard/hle-diamond) | HLE Diamond 新增 MiniMax-M3.1-Flash（选录 21 项，排除开放权重 `muse-spark-open`）。同步读取并固化三项 SEAL 专项前十快照与 SHA-256：**HSS（Humanity's Software Suite）** Carbon #1（71.10 ±3.60）、**MultiChallenge（Large）** 6.1 Sol #1（81.95）高于 6.2 Astra #8（73.20）/ 6.2 Sol #9（72.00）、**Remote Labor Index（RLI）** Fable 5.2 #1（41.25%，约为 Opus 5.5 21.25% 两倍）。 | `manual-boards.json` 含 `scale_extra`；同步更新前端 Scale 亮点说明与档案文字证据。 |
| [OpenRouter](https://openrouter.ai/rankings) | 周用量截至 2026-11-18：DeepSeek V4.1 Flash 1017 仍居 #1（62.1T）、Tencent Hy4 Flash #2（46.6T）、Opus 5.5 #7（7.63T，+15%）、MiniMax-M3.1-Flash 新入 #10（3.67T）。 | 仅代表平台调用热度，不作能力排名。 |

只作文字参考的扩展评测证据（写入 `model-effort-profiles.json` 的 `evidence`，共 28 条，不进入拐点或任何计算）：

- [AA Neon 分析](https://artificialanalysis.ai/articles/gemini-4-neon-intelligence-gain)：Antigravity CLI 下 Coding Agent Index 达 **59**（每任务 $6.86），以约一半成本追平 Fable 5.2 xhigh（58 / $15.47）与 Opus 5.5 max（58 / $12.61）；Briefcase 演示文稿质量 1771 Elo 居首。
- [AA Ember 分析](https://artificialanalysis.ai/articles/meta-releases-muse-ember-setting-a-new-pareto-frontier-for-intelligence-vs-cost)：Muse Ember max（36.0 / $0.14、~466 tok/s）在低价档刷新效率前沿，Muse Code Coding Agent Index 46、AutomationBench 68.1%，但 FrontierCode 2.0 仅 27.2%、AA-Omniscience 拒答率 64%（准确率 21.1%、幻觉率 17.4%）。
- [Vals AI Index v2.2](https://www.vals.ai/benchmarks/vals_index) 与 [Terminal-Bench 4.0（11-18）](https://www.vals.ai/benchmarks/terminal-bench-4)：Vals Index v2.2 中 Fable 5.2 #1（71.31%）、Neon #2（70.87%）；Terminal-Bench 4.0 中 Fable 5.2 / Opus 5.5 并列 65.15%、Astra 6.2 63.13%（$4.69）、Neon 61.62%（$6.42 / 36m06s）、Sol 6.2 60.61%（$1.13）、Carbon 55.56%、Hydrogen 47.47%、Ember 39.39%（$0.22）。
- [Scale SEAL HSS / RLI / MultiChallenge](https://labs.scale.com/leaderboard/rli)：见上表，揭示多轮复杂指令遵循与真实远程交付上的代际分化。

## 社区最佳实践与最新理解（`community-consensus.json`）

在 11-18 晚间 26 条基础上新增 **8 条原页核对条目**（共 34 条 `source-checked`），实现五厂所有当前主力型号（`tier: "main"`）**100% 覆盖**：

1. **Gemini 4 Neon 速度与性价比平衡**：实测 110 tok/s + $3/$15 统一价 + Agent Arena #3，定位“日常高频主力”。
2. **Claude Fable 5.2 能力上限 vs 成本梯度**：AA/WebDev/Agent/RLI/Vals 全线领跑，但 max 单任务 $26.54 且编程在 high 见顶（54.4% vs max 54.2%），社区常规做法为日常 Opus 5.5、疑难规划与最终把关升至 Fable 5.2。
3. **Gemini 4 Carbon 轨迹过审（Kernel.dev 11-18 实证研究，[HN #50541790](https://news.ycombinator.com/item?id=50541790)）**：Carbon 耗时偏长主要源于行为上的过度审查（步数约 GPT-6 Astra 的 7 倍、动作 11 倍、39% 为重复读文件）；low 档易死循环；每 5 轮注入进度 check-in 可将耗时从 37 分钟降至 28 分钟。
4. **Gemini 4 Hydrogen 与 Orchestrator-Worker 分层（[HN #50472260](https://news.ycombinator.com/item?id=50472260)）**：Google Antigravity 编排实践以只读 Carbon / Neon 做规划和验收、164 tok/s 的 Hydrogen 做执行与试错。
5. **Muse Ember 低价执行前沿与边界**：$0.14/任务 + 466 tok/s 适合结构化自动化的高频 Worker，不适合复杂仓库推理或事实检索；须严防 >200k 3 倍价格悬崖。
6. **Muse Wonder / Spark 1.3 定位边界**：Wonder Full 限于 Muse Code 订阅且无公开单价，不纳入开放 API 成本测算。
7. **GPT-6.1 Terra 视觉与中档执行**：补全 GPT-6.1 中档生态与 6.2 Sol 之间的取舍参照。
8. **GPT-6.2 API 缓存、前缀与提示迁移**：记录 Responses API `developer` 首条消息保缓存、勿中途改前缀/降档位、移除旧“简短回复”指令并显式授权持续执行和验证。

同步更新：
- `maxEffortScenarios` 从 9 条增至 **10 条**（新增 `trajectory-overaudit`：轨迹过审与前缀变更缓存失效）。
- `workPhases` 融入 2026 年底主流工程共识：只读规划（Orchestrator）、静态前缀保缓存、跨家族代码复核、5 轮收敛检查点。

## 页面与模板升级

- 概览页（`#overview`）在保留 `data-aa-version="v4"` 历史 10-20 选型表格原样的前提下，新增 `data-aa-version="v5"` 现代选型表：按任务类型选型（`#engineering-guide-v5`）、四层多 Agent 分工与脚手架工程（`#subagent-guide-v5`）、研究与专业写作（`#writing-research-guide-v5`），全部使用 `{{aa5:...}}` 实时占位符与 2026-11 最新实践。
- `report.js:buildPageToc` 过滤非活动 `[data-aa-version]` 容器内的标题，避免 v4/v5 双套标题导致页内目录重复。
- 规格与档案扩为 **35 款模型**，来源索引扩为 **78 条**；历史 121 / 169 条基准数据与 v4.3.2 全量口径保持零改动。

## 复算与验证

```sh
python3 research/2026-11-19/refresh_aa.py
python3 research/2026-11-19/refresh_boards.py
python3 research/2026-11-19/build_snapshot.py
python3 build_report.py
python3 -m unittest discover -s tests -v
python3 scripts/publish.py build
python3 scripts/publish.py check
python3 scripts/smoke.py --browser-channel chrome --output-dir test-results/refresh-2026-11-19/smoke
```

抓取原始缓存保存在 Git 忽略目录 `test-results/refresh-2026-11-19/`。
