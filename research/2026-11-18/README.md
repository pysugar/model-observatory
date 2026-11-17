# 2026-11-18 GPT-6.2 上线与 AA 刷新

本轮基于 `3cc37bd`（PR40 后的 main）补入 11-17 发布的 GPT-6.2 Astra / Sol，并重读 AA v5。研究未付费运行模型；核验日期按 Asia/Taipei 记录，不替代来源的发布或评测日期。11-16 至 11-18 未发现 Anthropic、Google、xAI、Meta 的新通用主力；Meta Muse Glimmer 是 8 月发布的开放权重型号，不在监测范围。

## 模型、价格与访问变化

| 变化 | 核对来源与本期处理 |
| --- | --- |
| GPT-6.2 Astra | [模型页](https://developers.openai.com/api/docs/models/gpt-6.2-astra)：1.05M 上下文（最大输入 922k）、最大输出 128k，文本 / 图像输入；low / medium / high / xhigh / max，API 拒绝 none。Standard 输入 / 缓存 / 输出 $8 / $0.40 / $40，较 GPT-6 Astra 降 20%；输入 **严格大于 272k** 时整次输入与缓存 ×2、输出 ×1.5。 |
| GPT-6.2 Sol | [模型页](https://developers.openai.com/api/docs/models/gpt-6.2-sol)：窗口、档位与 Astra 相同；Standard $2 / $0.10 / $10，与 GPT-6.1 Sol 同价，长上下文规则相同。 |
| 默认档位 | 模型页与[迁移指南](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6.2-astra)未写明 API 默认档位；指南建议新集成从 medium 起步，原用 none / minimal 的改用 low。目录写“未公布”，档案起步档取指南建议。 |
| 发布与上一代 | [API 更新日志](https://developers.openai.com/api/docs/changelog) 11-17 条目；[弃用页](https://developers.openai.com/api/docs/deprecations)未列 GPT-6 Astra / 6.1 Sol / Luna。两款上一代改为“上一代 · 仍可用”，曲线与档案保留。官方发布文章对自动读取返回 403，本期不引用其中的厂商自报成绩。 |

目录与档案为 **34 款**，跨榜对照为 **24 款**。Terra 6.1 与 Luna 单价复核未变。

## 评测与来源边界

| 来源 | 本期快照 | 处理 |
| --- | --- | --- |
| [AA 榜单](https://artificialanalysis.ai/leaderboards/models) / 发布版本页 | v5：71 个榜单配置、25 个发布版本 / 83 个配置；五家当前系列 21 款 / 79 个配置有 9 项底层评测 | 既有 23 个发布版本的分数与费用与 11-15 逐项一致。GPT-6.2 Astra 五档均有任务费用；**Sol 6.2 只有 max 有 AA 任务费用**，其余四档保持 null，不推算。GPT-6 Astra、GPT-6.1 Sol、Gemini 3.8 Flash 已离开当前榜单，发布页曲线保留。 |
| Arena / LiveBench / Scale / OpenRouter | 沿用 11-15 快照与核验日期 | 11-18 检查：Scale HLE Diamond、LiveBench（最新仍为 11-06 题集）与 OpenRouter 排名均无 GPT-6.2；Arena 数据集 11-16 有新版本，早于 GPT-6.2 发布，本期未导入。跨榜对照里 GPT-6.2 只有 AA 列，跨度为空。 |

AA 观测（点估计，不是显著性检验）：Astra 6.2 max 指数 62.1、$4.00 / 任务，xhigh 61.6、$2.52；Sol 6.2 max 57.3、$1.01。任务视图里 Astra 6.2 在编程（xhigh 56.5%）和长程科研代理（xhigh 78.6%）领先，max 均略低于 xhigh；复杂推理仍是 Fable 5.2 max 最高。

## 页面

- 甜蜜点规则不变；一款模型只有一个带费用的档位时（Sol 6.2），矩阵与档案只标“仅 max 有费用 / 仅此档有费用”，不再显示为甜蜜点，计算演示也跳过。参考实现 `scripts/sweet_spot.py` 的选档结果不变。
- 五厂速览按模型分组，档位、分数条与单任务费用对齐；7 天内发布的型号标“新”。页首加入本期更新入口。

## 复算

在仓库根目录使用当前机器配置的 Python 环境：

```sh
python3 research/2026-11-18/refresh_aa.py
python3 research/2026-11-18/build_snapshot.py
python3 build_report.py
python3 -m unittest discover -s tests -v
python3 scripts/publish.py build
python3 scripts/publish.py check
python3 scripts/smoke.py --browser-channel chrome --output-dir test-results/refresh-2026-11-18/smoke
```

研究抓取缓存在忽略目录 `test-results/refresh-2026-11-18/aa-pages/`；重新联网读取前先移走缓存。`build_snapshot.py` 读取 11-15 目录的 Arena / LiveBench / 人工榜单原始文件，只替换 AA。
