# 2026-10-23 模型观测与官方价格核验

本期更新基于仓库 `f34421104d89d517a44be685a1338ec8845365cb`，人工读取公开来源后整理为 [market-snapshot.json](market-snapshot.json)。网站继续离线构建，没有自动抓取、付费模型调用或新评测运行。页面的“核验”日期表示读取来源的日期，不代表模型发布日期或评测运行日期。

## 榜单范围

| 来源 | 本次选录 | 来源版本 / 日期 | 数据口径与读取方式 |
| --- | ---: | --- | --- |
| [Artificial Analysis](https://artificialanalysis.ai/leaderboards/models) | 23 | AA 智能指数 v4.3.2；页面未披露统一更新时间 | 读取公开榜单，保留整数分数、加权单任务费用和输出速度的显示精度；含回退配置显式标记。覆盖主要厂商与近期其他厂商型号，不是完整全球榜。 |
| [Arena Text](https://arena.ai/leaderboard/chat/text) | 17 | Overall；更新 2026-10-22 | 匿名成对回答偏好；保留原榜排名、Elo、区间、票数与 Preliminary 标记。未提供费用，不挪用 Agent Code 成本。 |
| [LiveBench](https://livebench.ai/#/) | 22 | LiveBench 2.0；release 2026-10-14；页面更新 2026-10-18 | 实际浏览器读取动态表。Overall 与每成功任务成本独立保留；主表未披露档位，统一标为未知。来源说明每套题运行一次，不补造置信区间。 |
| [Scale HLE Diamond](https://labs.scale.com/leaderboard/hle-diamond) | 15 | Humanity's Last Exam · Diamond；统一更新时间未披露 | 分数、来源区间与校准误差分列。校准误差越低越好；主成绩越高越好。没有费用。 |
| [OpenRouter](https://openrouter.ai/rankings) | 10 | Text · This Week；截至 2026-10-22 的滚动 7 天 | 实际浏览器读取前十。单位为 T tokens，保留周变化与新入榜标记；免费路由独立，不表示付费金额、用户数或能力排名。数据归属 OpenRouter，CC BY 4.0。 |

合计 87 条；每个来源独立排序、筛选和导出。来源未披露的费用、速度、日期保留 `null`。表格“序号”是当前展示顺序，原榜排名只在已取得时标为“来源 #”。相同显示分数不表示统计显著差异。

额外核对 [Scale HSS](https://labs.scale.com/leaderboard/hss) 与 [MultiChallenge](https://labs.scale.com/leaderboard/multichallenge?tab=large) 的前四名，以及全景表涉及的 Argon、Haiku、Flash 条目。未核对的 Scale 项目继续保留 10 月 19 日历史标签。

## 具体修正

- LiveBench 旧全景摘要里，Grok 4.7 改为 Overall 74.1、每成功任务 $2.687；Haiku 5.5 改为 75.6、$0.818。它们不能与 AA 每任务费用直接互换。
- 全景表按型号精确对应新数据；Arena Text 与历史 Agent Code 明确分开。OpenRouter 当前前十未收录的型号标记为“本次未收录”，不推断没有流量或不可用。
- 新榜单收录 DeepSeek V4.1 Flash / 1017、Muse Wonder / Full、MiMo、MiniMax 等。版本和免费路由不合并，未取得同协议逐档成绩的型号不补造任务建议或曲线。
- 原 169 条基准记录、121 条保真基线、44 个逐档配置保持原值与原日期；最新榜单的舍入显示不反向覆盖旧曲线高精度值。
- 选档避坑文案改为与实际题集和观测相称的建议，避免把个别模型曲线推广为所有任务的规律。

## 官方价格

目录 24 款型号的基础 Standard 输入、缓存读取和输出价格已逐项对照，基础值与旧目录一致；不把 Batch / Flex / 产品订阅额度混入。

| 厂商 | 官方入口 | 本次处理 |
| --- | --- | --- |
| OpenAI | [API pricing](https://developers.openai.com/api/docs/pricing)；对应型号页，例如 [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) | 核对六款目录型号，保留原有长上下文规则；每款 `price_source` 指向对应官方页面。 |
| Anthropic | [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing) | 核对十四款目录型号；Haiku 5.5 完整 prompt >100k 的整次阶梯计费保持不变。 |
| Google | [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) | 核对三款；Argon 优惠截至 11 月 30 日、Flash 3.8 截至 12 月 31 日。价格日历由已有 `promo_end` / `future_*` 数据生成。 |
| xAI | [Pricing](https://docs.x.ai/developers/pricing)；[Models](https://docs.x.ai/developers/models) | Grok 4.7 基础价为 $2 / $0.50 / $6；完整 prompt ≥200k 后整次请求为 $4 / $1 / $12，均为每百万 token。 |

xAI 正文个别段落使用 “above”，价格主表与整次计费规则使用 ≥200k；本次按主表边界编码 `tier_inclusive=true`，测试覆盖 199999 / 200000 / 200001。其他型号仍按各自原有严格大于边界；不统一改写。核验价格不等于重新核验全部生命周期、默认档位、上下文限制或厂商自报评测。

## 维护与复核入口

源快照由 `build_report.py` 读入 `market_snapshot`，`scripts/market_snapshot.py` 只更新全景的对应字段。单元测试检查来源日期、缺失值、型号映射、排序/导出及阶梯边界；浏览器回归继续使用现有 `scripts/smoke.py`。本轮没有修改发布流程、权限或依赖，也未创建外部 PR、提交 review 或宣称独立审核。
