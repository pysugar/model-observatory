# 2026-10-25 社区主流声音

新增 [community-consensus.json](community-consensus.json)，由 `build_report.py` 读入 `community_consensus`（构建时 `check_community` 校验型号、任务与 https 来源），在模型档案的概况、“更优替代”表下方和分任务选档卡中以文字显示。

## 为什么需要

“更优替代”只比较带费用的公开评测。以 GPT-6.1 Sol 与 GPT-6 Astra 为例：每个档位 Sol 都便宜得多，所以“同分最省 / 同预算最强”从不推荐 Astra；但网上多数对比的结论是不考虑预算时默认用 Astra。差别来自评测覆盖不到的维度：长时 agent 稳定性、最难题与科研计算的上限、需求模糊时的判断等。本期因此：

- 在“更优替代”加“不限预算推荐”列：不看费用，与最高分相差不到该评测分差 3% 的视为打平，取其中最快的（AA 耗时、Vulcan 分钟、ToneBench 秒；无耗时数据时取最便宜）。只看分数会几乎总选 max，而例如 Sol 6.1 xhigh→max 耗时约翻倍、AA 智能指数只多 0.8。按冻结数据，Sol 6.1 max 的综合推荐是 Astra xhigh（52.4，比 Astra max 只低 0.3、快约 1.4 倍）。
- 新增 `maxEffortScenarios`：不差钱时也不该默认最高档的九类场景，混合本页实测、官方建议、配对实验与社区经验；`measure` 为 overthink / regress / ttfa 的场景对当前模型显示实测信号（如 Sol 6.1 首字等待 low 3 秒 → max 178 秒）。
- 避坑新增“过度思考”：相邻两档耗时 ≥1.5 倍，分数提升 < 分差 3%。
- 新增 `workPhases`：按工作阶段记录主流档位（头脑风暴 medium、方案设计 xhigh、具体执行 medium、日常小改 low、复杂 BUG xhigh、环境 / 依赖问题 medium、代码审查 high、调研 high、写作 medium、数学推导 max、长时 agent high），每项附常见范围、升降条件、原因与依据。这类选择没有统一客观标准，条目是官方建议、主流工具工作流（如先计划再执行、architect / editor 分工）与社区经验的综合整理，页面标为“主流做法”，不参与计算；部分依据来自既有公开实践文章，原页未在本期逐条复核。
- 列出这张表覆盖不到的维度（`uncoveredDimensions`）。
- 新增社区主流声音条目：结论、可执行动作、来源一致性（`agreement`）与来源列表。

## 边界

- 条目来自 2026-10-25 的网页检索摘要，原页尚未逐条核对，页面统一注明；数字与本页冻结数据口径不同时只在文字中说明。
- 社区条目没有 `efforts` 字段，不影响起步档、甜蜜点、避坑或更优替代的计算（测试会检查）。
- 目前只覆盖 GPT-6 Astra 与 GPT-6.1 Sol；其它型号需要按同样格式补充，并至少给出一个可追溯来源。
