# 2026-10-31 五厂评测刷新

本轮为源码与离线产物更新，未调用模型或改动生产；合并与正式发布另行决定。读取日期不等于评测日期。Meta 的监测范围按用户要求限定为主流闭源 Muse Wonder、Wonder Full、Spark 1.3，排除 Meta 开放权重系列；早期原始研究文件保留存档，不进入本期监测选录。

## 已读取来源

| 来源 | 本期快照与内容 | 保留方式 |
| --- | --- | --- |
| [AA 当前榜单](https://artificialanalysis.ai/leaderboards/models) | 智能指数 v5（10-27 发布），本期 62 个配置选录；来源没有披露榜单更新时间，字段保持空值 | `aa-index-v5.json`，原页 URL / SHA-256；包含各厂商在当前榜单的全部已测配置及既有其他厂商参照，不是完整全球榜 |
| [AA 发布版本](https://artificialanalysis.ai/zh/models/releases) | 20 个发布版本、58 个配置；54 个配置有九项底层评测；57 个配置有六域指数 | `aa-v5-series.json`；Spark 1.3 max 从发布页补入榜单，逐行和 CSV 保留来源；Wonder Full 从榜单单点补入，领域、费用、用时、用量均不外推 |
| [Arena 官方数据集](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset) | 文本 / WebDev / Agent / 表扬抱怨均为 10-28 发布；固定 revision `323062f70843f40e3f739865c3fe9d806126e412` | `arena.json` 保留来源名次、分数、区间、票数 / 会话数及文件哈希；选前 40 名与关注型号，Meta 开放权重型号排除 |
| [LiveBench](https://livebench.ai/#/) | 最新题集仍为 10-25；本期重新读取 table / categories / cost，成绩未变、成本文件已变 | `livebench.json` 记录文件哈希；沿用页面的加权成绩与成功任务费用公式。当前网页只读核对七款指定型号，另核对 Spark 1.3；不使用旧费用断言 |
| [Scale HLE Diamond](https://labs.scale.com/leaderboard/hle-diamond) | 页面全榜 19 项；新增 Terra 与 DeepSeek V4.1 Flash 1017；本期选录 18 项，排除 Meta 开放权重型号 | `manual-boards.json`，原页顺序与名次保留；来源未披露发布日期，不填造日期 |
| [OpenRouter](https://openrouter.ai/rankings) | 本期页面可读到 10-30 截止说明，但未得到与旧版相同的周用量完整表 | 保留 10-27 周用量及原核验日期，不称为本期新用量，不使用其他指标替代 |

社区声音沿用 10-29 已核对的文件。本轮新增型号没有整理社区观点，界面如实显示缺少资料，不把其他型号的观点留在新型号下。

## 五厂结论与可用性

| 厂商 | AA v5 本期读数 | 影响选型的限制 |
| --- | --- | --- |
| Google | Carbon high 59.43；Argon high 50.41 | [Carbon 官方发布](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-carbon/)说明先向部分安全合作方开放；不列为可直接使用的公开 API 预算。AA 对 Argon 的任务费用采用 12-01 后价格，与当前优惠价不同 |
| Meta | Wonder Full max 49.73；Wonder max 43.32；Spark 1.3 max 36.42 | [官方型号](https://dev.meta.ai/docs/models)区分 Wonder 与独立的 Full：前者有 API 预览，后者仅 Muse Code 指定订阅。Spark 1.3 xhigh 未重测，不从 v4.3.2 补值 |
| xAI | Grok 4.7 high 35.01，xhigh 34.34 | [官方模型与发布说明](https://docs.x.ai/developers/release-notes)确认支持 medium、无独立文本输出上限；未得到 medium 的 AA 成绩，不画该档位点。prompt 达到 200k 的既有阶梯计价边界保持不变 |
| OpenAI | Astra max 56.85；Sol 6.1 max 54.51；Terra max 50.98 | 新增 [Terra 官方规格与价格](https://developers.openai.com/api/docs/models/gpt-6.1-terra)：1.05M 上下文、128k 最大输出，Standard $1 / $0.05 / $5；>272k 的整次长上下文计价单列，none 与 low 分别保留实测 |
| Anthropic | Opus 5.5 max 58.41、xhigh 56.99；Sonnet 5.5 max 54.24；Haiku 5.5 max 36.23 | [官方型号发布目录](https://www.anthropic.com/news/models)复核；补齐原先未选录的 Opus xhigh。AA 的 Opus / Sonnet / Fable 回退标记保留 |

LiveBench 本期页面核对：Fable 5.1 85.7 / $7.406、Astra 85.6 / $4.828、Opus 5.5 85.1 / $4.820、Sol 6.1 84.1 / $0.819、Terra 77.8 / $0.665、Wonder 1.0 74.2 / $2.015、Grok 4.7 70.1 / $2.913；另见 Spark 1.3 63.0 / $1.372。网页无 Carbon 或 Wonder Full。

## 页面和计算

- 新增五厂速览，保留当前模型、档位、分数、任务费用、可用性与官方来源。
- 跨榜对照扩为 19 款，仍只在各来源内部对这批型号排名，各列不相加、不平均；新增型号的空格保留为缺测。
- 目录和模型档案增至 29 款，新增 Meta 三款、Terra、Carbon。六域、逐档曲线与速查默认读取本期 v5；v4.3.2 输入不改写。
- 缺少费用不参与性价比前沿，单点不标成计算出的甜蜜点；预算不把未知价或受限型号转换成零费用。
- AA 榜单保留到四位小数的任务费用，避免 Luna low 一类低费用配置被过度舍入；排序使用原始精度。
- 旧四家全景明确保留 v4.3.2 的 AA 参照；其他来源列按各自最新可读数据更新，不混算为一个综合总榜。

## 复算入口

从仓库根目录使用当前机器配置的 Python 环境：

```sh
python3 research/2026-10-31/refresh_aa.py
python3 research/2026-10-31/refresh_boards.py
python3 research/2026-10-31/build_snapshot.py
python3 build_report.py
python3 scripts/publish.py build
python3 scripts/publish.py check
```

AA 抓取器使用 `test-results/refresh-2026-10-31/aa-pages/` 的本轮缓存；要重新联网读取发布页，先移走该临时缓存目录。Arena 固定数据集 revision，LiveBench 新 release 会停止自动导入，要求先检查名称与口径。Scale 本轮为官方页面人工读取，不由脚本猜测更新。历史抓取器只增加可传入的元数据和请求间隔，默认行为不变。

验证：77 项单元测试、静态构建 / 产物检查、Chrome 全量 smoke 均 PASS，覆盖 1440 / 390 / 320 视口、v4 / v5 切换、CSV 与缺值、预算边界、逐格参考计算、无 JS 错误与无外部资源请求。独立只读 GUI 复核确认五厂速览、Meta 仅闭源范围、Spark 补充来源、Wonder Full 单点与缺价展示，以及移动端换行。日志与截图保存在忽略目录 `test-results/refresh-2026-10-31/`；未验证云端发布。

## 最后一轮复核与定向优化

本轮没有重新抓取或改写评测快照，针对实际发现的呈现与计算边界问题修复：

- 成本页上图显式显示当前 AA 版本，随成本、耗时、输出 Token 横轴更新标题；下图及旧分项矩阵标明 v4.3.2 历史口径，避免同页不同分数误读。
- 发布版本与配置数量、规格目录数量从数据生成；图旁区分已选、可绘、未绘配置，列出缺横轴的型号和档位，缺值不当零。
- 原固定纵轴从 14 分起，会使 Luna non-reasoning / low（9.39 / 9.67）及 Flash-Lite high（11.66）落到绘图区外；现按实际分数取含边距的范围，全部可绘点都在绘图区内。无可绘点时清空旧图并展示空态。
- Carbon 与 Wonder Full 的发布版本详情直接显示访问限制及 AA 加权任务费用的适用口径；缺少耗时不再追加单位。
- 发布版本 CSV 保留指数版本、快照、原始来源和可用性，文件名使用实际版本与快照；手机端图表下拉控件占整行，缩短选项文字。
- AA 抓取脚本复用同一份榜单响应解析分数、费用和页面哈希，避免一次刷新中重复读取造成来源错位；未改变本轮冻结输入。

77 项单元测试、静态产物检查与最终全量 Chrome smoke 均 PASS。新增浏览器断言覆盖三种横轴的动态标题、计数、点坐标边界、缺测单位、访问说明与 CSV 元数据；独立只读 GUI 复核再次确认 390 / 320 无溢出。记录与截图在 `test-results/refresh-2026-10-31/final-review/`；这些是本地验证结果，云端 CI / 预览以 PR 当前 head 的记录为准，尚未正式发布。
