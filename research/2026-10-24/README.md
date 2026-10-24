# 2026-10-24 模型档案与选档证据补充

本期基于 `main` 的 `d8ae6c3`（PR18 合并后）。新增文件 [model-effort-profiles.json](model-effort-profiles.json)，由 `build_report.py` 读入 `model_effort_profiles`，驱动新页签“模型档案”（`#profiles`）。

## 整理环境与核验方式

本期在云端会话中完成。会话的网络策略只放行网页搜索，`artificialanalysis.ai`、`docs.x.ai` 等原页无法直接打开（代理拒绝连接）。因此：

- 新增的 14 条证据都来自 2026-10-24 的网页检索摘要，保留检索到的原始 URL（转述来源另记 `via`），统一标 `verification: "search-summary"`，页面显示“检索摘要，原页未直接打开”。
- 逐档分数与成本**没有新增或改写**，全部来自既有冻结输入：AA v4.3.2 逐档与子评测（10-19/20）、Vulcan 编码（10-16）、ToneBench 写作、OSWorld 分协议记录（10-20）。
- 检索结果与冻结数据冲突时只作提醒，不覆盖原值。具体见下文。
- 五站榜单沿用 10-23 快照。10-24 检索没有发现四大家族在 10-23 之后的新型号或 AA 逐档新数据；AA 新收录的 Kimi K3.1 Pro（55 分，第 4）不属于四大家族，未纳入目录与榜单。

## 文件结构

| 字段 | 含义 |
| --- | --- |
| `taskAxis` | 9 类任务：综合、编程、复杂推理、工具自动化、知识工作交付、方案规划、长文档·事实、写作、Computer Use。前 7 类与选档速查一致；`guideTasks` 把档位建议的 4 类任务映射进来（复杂问题→复杂推理，日常代码 / 仓库 BUG→编程，方案设计→方案规划）。 |
| `models` | 目录全部 24 款（四家活跃型号，含 GPT 5.6 Sol / Luna；Sonnet 4.5 标已弃用），分“当前主力 / 上一代仍可用 / 兼容旧版”。`aaRelease`、`guidanceId`、`cuIds` 把目录 id 接到 AA 发布系列、档位建议与 Computer Use 记录；缺数据保持 `null`，不借相邻型号。 |
| `evidence` | 按模型和任务归属的补充证据：类型（官方建议 / 厂商自报 / 第三方评测 / 社区经验 / 检索结论）、陈述、可执行动作、可选的 `efforts.start / ceiling / avoid`、来源与核验日。 |
| `marketWatch` | 本期检索到但未纳入页面的市场动态。 |

后续的避坑指南更新为 `models` 补了 `line`（产品线，如 opus、sol）与 `lineNote`，只用于避坑指南判断“新一代更省”；证据条目未改。

`build_report.py:check_model_profiles` 在构建时校验所有 id 能对上目录、AA 发布系列与档位建议，证据必须带 https 来源与核验日。

## 计算规则

- 每行只在同一评测内比较。实测拐点沿用选档速查的边际收益规则（`kneeOf` + 省钱 / 均衡 / 性能优先三档门槛）；AA 行直接复用 `sweetThreshold`，因此和概览矩阵逐格一致。Vulcan、ToneBench、OSWorld 行的门槛是各自全部配置分差的同一比例。
- 选档卡：起步档优先取档位建议记录，其次取任务范围内的补充证据，再取适用全部任务的证据，最后取官方默认；降档候选 / 升档上限分别是省钱 / 性能优先门槛的拐点。只有单点时不给拐点。
- Python 参考实现在 `scripts/sweet_spot.py:profile_series`，`tests/test_model_profiles.py` 与 `scripts/smoke.py:check_profile_ui` 逐模型、逐门槛比对。

## 冲突与待核验

| 项目 | 处理 |
| --- | --- |
| Grok 4.7 是否支持 medium | 目录（10-15 官方页摘录）记 low / high / xhigh；10-20 档位建议文件和 10-24 检索到的 Oracle、Amazon Bedrock 页面列出 low / medium / high / xhigh。xAI 原页未能打开，页面把 medium 标为“待核验”，目录不改。 |
| Gemini 3.8 Flash 逐档费用 | 第三方转述 AA 优惠价 low $0.24 / medium $0.41 / high $0.58，与冻结的 AA 值（medium $0.931、high $1.243）不同，只作提醒。 |
| GPT 6 Astra 默认档 | 来源分别称 low、medium；目录保持“按端点明确设置”。 |
| Grok 4.7 xhigh 与 high | 检索到的“同为约 46 分、费用高 37%”与冻结 AA 值一致（46.33→46.45，$2.73→$3.74），无需修正。 |

## 未覆盖

中文任务全部未实测；Argon、Flash-Lite、Grok 等仅有单点或少数档位的任务不补造曲线；补充证据中的厂商自报与社区经验不进入任何前沿或拐点计算。
