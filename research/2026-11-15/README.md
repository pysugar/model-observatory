# 2026-11-15 模型与榜单刷新

本轮基于 `bd80181` 更新源码、研究输入和离线产物。监测范围仍为 Google、Meta、xAI、OpenAI、Anthropic；Meta 只纳入主流闭源系列。研究未付费运行模型；用户随后授权经 PR 验证、合并并发布，发布事实另记于根目录 `RELEASES.md`。核验日期按 Asia/Taipei 记录，不替代来源的发布或评测日期。

## 模型、价格与访问变化

| 变化 | 核对来源与本期处理 |
| --- | --- |
| Claude Fable 5.2 / Mythos 5.2 | [11-09 官方发布](https://www.anthropic.com/claude-fable-and-mythos-5-2)。Fable 加入通用目录和五档 AA 曲线；[API 默认 high](https://platform.claude.com/docs/en/models/fable-5-2/overview)，应用与 Claude Code 默认 medium。Standard 输入 / 缓存读取 / 输出为 $8 / $0.20 / $40 每百万 token，Fast 另列。Mythos 仍需验证机构，仅列受限观察，不复制 Fable 成绩。 |
| Gemini 4 Carbon | [11-10 开放公告](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-carbon-now-available/)确认可使用付费 API；改为可计算预算，默认 medium，补齐 low / medium / high 实测。 |
| Gemini 4 Hydrogen | [11-12 官方发布](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-hydrogen/)。新增四档曲线，默认 high、最高 xhigh；Standard $1.50 / $0.075 / $7.50，整个 1M 窗口统一价。Carbon / Hydrogen 的同步输出上限与 long decode 条件分别说明。 |
| Google 优惠期限 | [官方价格](https://aistudio.google.com/docs/pricing)：Carbon / Argon 当前 $2 / $0.10 / $10，11-30 优惠结束，12-01 起 $4 / $0.20 / $20。本期 AA 费用使用当前优惠价；10-31 的 Argon 费用曾用优惠结束价，跨期费用下降不能当成推理效率改善。 |
| Muse Ember | [官方规格](https://dev.meta.ai/docs/muse-ember)与[价格](https://dev.meta.ai/docs/pricing-rate-limits)：闭源低成本执行型号，原生六档、默认 max；AA 仅测 xhigh / max。1,048,576 共享窗口、524,288 输出上限；Standard $0.10 / $0.004 / $0.50。prompt **严格大于 200k** 时整次三倍计价，缓存输入计入阈值。 |
| 既有主力 | 复核 [OpenAI Standard 价格](https://developers.openai.com/api/docs/pricing)、[Claude 价格](https://platform.claude.com/docs/en/about-claude/pricing)及 Meta 当前价；[xAI 发布说明](https://docs.x.ai/developers/release-notes)未见通用主力代际替换，未全面重读的旧价格保留原日期。领域受限及专用生成模型不并入通用选型。 |

目录与档案为 **32 款**，跨榜对照为 **22 款**。Wonder Full 仍仅限 Muse Code、没有公开 API 费用；本期 AA 已提供其六领域指数，不能继续写作“无领域成绩”。Fable 5.1 仍保留发布页曲线与上一代档案，但已不在当前 AA 榜单。

## 评测与来源边界

| 来源 | 本期快照 | 保存与计算 |
| --- | --- | --- |
| [AA 榜单](https://artificialanalysis.ai/leaderboards/models) / 发布版本页 | v5：75 个榜单配置、23 个发布版本 / 73 个配置；五家当前系列 19 款 / 69 个配置 | `aa-index-v5.json`、`aa-v5-series.json`。发布页全部 73 个配置有领域数据，69 个配置有底层评测；缺值仍为 null。当前榜单选录与发布页覆盖不同，Spark 1.3 max 仅用本期发布页补入，保留逐行来源。 |
| [Arena 官方数据集](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset) | Text / WebDev / Agent / 表扬抱怨均发布于 11-11 | revision `4ca698d9bb5780db156459679d5c7e6dff4edbd3`。三张显示榜选录 43 / 43 / 41 项；分数、区间、票数 / 会话数和来源名次保留。 |
| [LiveBench](https://livebench.ai/) | **11-06 新题集**，35 项原始记录、25 款已识别选录 | `livebench.json` 保留 table / categories / cost 文件及页面 bundle 哈希。Overall 仍为长程代理×2、编程与设计×1.5、其他×1 的加权均值；每成功任务成本沿用页面公式。不能与 10-25 题集直接计算能力涨跌。 |
| [Scale HLE Diamond](https://labs.scale.com/leaderboard/hle-diamond) | 全榜 20 项、选录 19 项；Fable 5.2 新增 72.4±2.8 | 排除 Meta 开放权重型号；保留来源排名和校准误差缺值。来源未披露榜单发布日期，保持 null。 |
| [OpenRouter](https://openrouter.ai/rankings) | Weekly usage 截至 11-13 的滚动七天前十 | 本期取得完整表，记录 URL / 哈希。token 用量只代表平台调用热度，不代表用户数或能力。 |

AA 本期适配了新的内嵌数据结构：发布页 `initialModels` 含显式 UUID / slug，领域在 `capabilities`，子评测位于模型根节点，Briefcase Elo 在 `briefcaseBreakdown.overall`。榜单没有变体 slug 时按 UUID 与发布页关联，不从展示名猜测身份。保留原始精度用于计算，展示时才舍入。

本期选型提示改为对应任务的观测：Fable 5.2 提升复杂推理上限，但 max 的 AA 综合任务费用约 $26.54，high 约 $9.08；编程合成分并非 max 最高。Carbon medium 本期综合指数与费用均优于 low。Grok 4.7 本期 xhigh 指数略高于 high，撤下旧版相反结论。这些均不是显著性检验，也不是业务工作流的最优档位结论。

v4.3.2、旧专项实验和 10-29 社区声音保持原快照；新型号没有社区资料时显示缺少资料，不借用旧型号观点。AA 与 Scale 同名子评测、Arena 偏好 / IPS、LiveBench 每成功任务费用分别参考，不合成跨榜总分。

## 页面与复算

- 官方规格、预算、模型档案、五厂速览、选档矩阵和跨榜对照同步读取新输入。新来源与旧来源分别保留核验日期。
- 任务成本图和逐档图按实际分数扩展纵轴，保证新高分与低分都在绘图区内；聚焦单一档位时背景曲线也纳入范围。任务成本轴的指数版本随 v4 / v5 切换，图例补齐 Meta，缺少耗时显示“未提供”。
- 报告仍可离线打开；研究脚本联网读取公开网页，构建与发布产物检查不联网，不调用模型。

在仓库根目录使用当前机器配置的 Python 环境；Mac 的 uv 执行前缀见本机 `LOCAL_CONTEXT.md`：

```sh
python3 research/2026-11-15/refresh_aa.py
python3 research/2026-11-15/refresh_boards.py
python3 research/2026-11-15/build_snapshot.py
python3 build_report.py
python3 -m unittest discover -s tests -v
python3 scripts/publish.py build
python3 scripts/publish.py check
python3 scripts/smoke.py --browser-channel chrome --output-dir test-results/refresh-2026-11-15/smoke
```

浏览器启动须遵循主机审批要求，使用临时隔离配置。研究抓取使用本轮忽略缓存 `test-results/refresh-2026-11-15/aa-pages/`；重新联网读取前先移走缓存。Arena 固定 revision，LiveBench 遇到未复核的新 release 会停止导入。官方规格和档案建议是人工核对输入，不由抓取脚本推断。研究额外依赖现成的 pyarrow / beautifulsoup4；离线构建仍只需标准库。

验证：79 项单元测试、离线构建 / 产物检查、Chrome 全量 smoke 均通过，覆盖 1440 / 390 / 320 视口、v4 / v5、CSV、32 款档案的三档门槛参考计算、缺值、Carbon 现价与优惠结束价、Ember 含缓存输入的严格 `>200k` 计价，以及七类任务的图表坐标边界。新 AA 页面解析回归测试覆盖显式身份、零值与缺值。

截图复核发现并修正 Meta 图例与缺失耗时展示后，最终 v5 定向浏览器复验通过；无 JS 错误、无外部资源请求。逐项比对确认 `rows`、v4.3.2 发布版本 / 领域 / 底层评测和社区声音与基线完全一致。68 个本地文档链接均有效，来源 ID 无重复，`git diff --check` 通过。日志及截图保存在 `test-results/refresh-2026-11-15/`，其中 `smoke/smoke.json` 为全量结果，`final-v5/result.json` 为定向复验结果。五厂速览随后按 OpenAI / Anthropic / Google / xAI / Meta 调整，六项市场快照测试及源码 / HTML / 发布产物顺序核对通过。云端 CI、预览和生产部署以根目录 `RELEASES.md` 的后续验收为准。

独立 PR 预览复核发现并修正两项展示问题：说明数字改为与浏览器相同的十进制半入舍入，避免 Fable 5.2 同一成绩出现 78.3% / 78.4%；模型档案避坑网格的最小列宽不再超过容器。新增真实 Node 数字格式对照测试，v5 smoke 同时检查 305px 可用宽度（320px 视口扣除传统滚动条）和卡片是否超出网格。79 项单元测试与 v5 定向浏览器检查通过。
