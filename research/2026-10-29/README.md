# 2026-10-29 多源榜单与社区声音

本期在 AA v5 之外补齐其他主流评测与社区来源，新增“跨榜对照”。页面上的“核验”日期是读取日期，不是评测日期。网站仍离线构建，没有新的模型调用或评测运行。

## 来源与读取方式

| 来源 | 本期内容 | 来源日期 | 读取方式 |
| --- | --- | --- | --- |
| [Artificial Analysis](https://artificialanalysis.ai/leaderboards/models) | 重跑 `research/2026-10-28/` 两个脚本 | v5，10-27 发布 | 分数全部不变；速度、用时随实时测量波动。Gemini 4 Argon high 单任务费用 $3.84 → $7.68，token 数不变：AA 页面写明已按 $4 / $20（Google 12-01 起的价格）计价，而官方优惠价 $2 / $10 仍到 11-30。 |
| [Arena](https://arena.ai/leaderboard) 文本 / WebDev / Agent | `fetch_arena.py` → `arena.json` | 文本 10-22，WebDev 10-27，Agent 10-23 | arena.ai 对脚本和自动化浏览器都返回 Cloudflare 拦截页，未绕过；改读 Arena 官方 Hugging Face 数据集 `lmarena-ai/leaderboard-dataset`，版本固定在 `6852ae7`，记录 parquet 的 SHA-256。网页默认的文本榜对应 `text_style_control`。 |
| [LiveBench 2.0](https://livebench.ai/#/) | `fetch_livebench.py` → `livebench.json` | release 10-25 | 读取发布静态文件（table / categories / cost）。Overall 与每成功任务成本在网页端计算、不落盘，脚本按页面代码的规则重算，并对 7 个模型做页面抽查。 |
| [Scale HLE Diamond](https://labs.scale.com/leaderboard/hle-diamond) | `manual-boards.json` | 未披露 | 浏览器读取，全部 17 项。 |
| [OpenRouter](https://openrouter.ai/rankings) | `manual-boards.json` | 截至 10-27 的 7 天 | 浏览器读取 This Week 前十。 |
| [Hacker News](https://news.ycombinator.com/) | 14 个发布讨论帖 | 9 月初至 10-28 | 官方 API 按页面顺序取每帖前 25 条顶层评论，提炼反复出现的观点；引用的评论逐条附链接。 |

Reddit 被本期浏览环境的安全策略拦截，X / Twitter 未检索。

`build_snapshot.py` 以 10-23 快照为底，只替换有新读取的榜单，生成 `market-snapshot.json`，并计算 `cross_source`。AA v4.3.2 冻结榜单原样保留，AA v5 仍在构建时从 `research/2026-10-28/aa-index-v5.json` 合并。

## 主要发现

- **Arena 文本榜无新发布**：10-23 浏览器读取的 17 行与官方数据集逐行一致（分数、区间、票数）。
- **新增 Arena WebDev**：Opus 5.5 max 1809 居首，GPT-6 Astra max 1774、Sonnet 5.5 xhigh 1769 随后。
- **新增 Agent Arena**：真实代理会话的多信号 IPS 估计，Opus 5.5 max 0.208 明显领先，第 2–5 名（Sonnet 5.5、Astra、Fable 5.1、Sol 6.1）约 0.136–0.140，区间重叠；“用户表扬 / 抱怨”分项同样是 Opus 5.5 第一（0.453）。
- **LiveBench 10-25 改为加权 Overall**：长程代理 ×2，编程、设计 ×1.5。Fable 5.1 85.7、Astra 85.6、Opus 5.5 85.1、Sol 6.1 84.1；Sol 6.1 每成功任务 $0.761。10-14 版是等权，两版不能直接比较。
- **HLE Diamond**：前 15 名与 10-23 相同，新增 DeepSeek V4 Pro 与 Inkling。
- **OpenRouter**：DeepSeek V4.1 Flash 1017 周用量 37.3T（+224%），Opus 5.5 8.07T（+19%）。
- **AA v5 社区质疑**：HN 讨论集中在开放权重模型普遍下降（Kimi K3.1 Pro −9、DeepSeek V4.1 Flash 1017 与 GLM-5.3 −13、MiMo −16）、FrontierCode 用 GPT-6 Luna 做评分模型、编程与科学题量较小。本页不判断对错，只在“本期更新”中提示：同一批开放模型在 LiveBench、WebDev 与 OpenRouter 用量中靠前。

## 跨榜对照

选 14 款模型（四家主力 + DeepSeek V4.1 Flash 1017、Kimi K3.1 Pro、GLM-5.3、MiMo V2.6 Pro），在每个来源内部只对这 14 款排名，每款取该来源最好的一个配置。AA v5 是选录榜，内部名次只在这 14 款之间有意义；Arena 三个榜单另保留了关注模型的低名次行，所以“—”只表示来源没有收录或没有上榜。“名次跨度”不计 OpenRouter 用量。

本期最明显的分歧：GPT-6 Astra 在 HLE Diamond 第 1、LiveBench 第 2，但 Arena 文本偏好只排第 9（全榜第 32）；Gemini 3.8 Flash 文本偏好第 4，其余来源第 12–13。Opus 5.5 在所有来源都排前三。

## 社区声音

`community-consensus.json`（取代 10-25 版）：

- 10-25 的 15 条检索摘要逐条打开原页核对，`verification` 改为 `source-checked`，`checkedAt` 为 10-29。10 条成立；5 条修正，`correction` 字段记录原因并在页面显示：
  - Astra 科学题：所列原文找不到“68.1% / 57.0%”，改用 AA v5 Terminal-Bench-Science（max 63.3% 对 58.1%）。
  - Sol 6.1：500K 是 Codex / ChatGPT Work 的默认窗口，API 为 1.05M；>272K 的整次长价只适用于 API。依据 OpenAI 模型页。
  - Fable 5.1：缓存读取 $0.25 比 Opus 5.5 的 $0.20 贵，只是比 Fable 5 的 $1 便宜。
  - Grok 4.7：token 数出自 AA 数据而非所列文章；“前端 / 3D 参差”找不到出处，删除。
  - Argon：补 v5 用量（high 每任务约 11.6 万输出 token）与 AA 计价变化。
- 打不开（403）或找不到对应论述的来源已移除：Crypto Briefing、Vidmuse、Korben、MindStudio、MyClaw 日文页。
- 新增 8 条：Sonnet 5.5 高档位不如 Opus 5.5 划算（AA v5 数字印证）、Claude 护栏回退、Haiku 5.5 与 Luna 分工、Argon 交互式编码偏慢、Sol 6.1 缓存价、Agent Arena 中的 Opus 5.5、Astra 的对话偏好落差、发布节奏与可替换性。

社区条目仍只作文字参考，不进入甜蜜点、避坑、更优替代或任何计算。

## 未核实与边界

- Agent Arena 方法页（IPS 与各信号定义）被 Cloudflare 拦截，本期未直接打开；描述来自数据集说明。
- Sonnet 5.5 System Card 8.5 节的回退比例来自 HN 评论转述，未打开原文。
- LiveBench 每成功任务成本的重算值与页面显示最多差 0.001（页面对中间值的取舍略有不同）；站点显示两位小数。
- HN 评论只取每帖前 25 条顶层评论，代表讨论热点，不是抽样调查。

## 刷新

```bash
python3 research/2026-10-28/fetch_aa_v5.py
python3 research/2026-10-28/fetch_aa_v5_releases.py
python3 research/2026-10-29/fetch_arena.py      # 需要 pyarrow；先把 REVISION 改成数据集最新提交
python3 research/2026-10-29/fetch_livebench.py  # 新 release 需更新 RELEASE、NAMES 与 PAGE_CHECK
python3 research/2026-10-29/build_snapshot.py   # Scale、OpenRouter 先在 manual-boards.json 手动更新
python3 build_report.py
```
