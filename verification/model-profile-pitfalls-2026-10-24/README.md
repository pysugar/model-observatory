# 模型档案：甜蜜点说明与避坑指南 · 本地验收

2026-10-24，基线 `a037858`（PR20 合并后的 main），分支 `claude/nice-euler-cj5s04`。本记录对应提交前的工作树；CI 与预览以 PR 检查为准。

## 本次改动

- 术语统一：模型档案里的“实测拐点”改称**甜蜜点**，与选档速查一致；新增“甜蜜点与三档门槛怎么算”说明，并用所选模型的一条逐档曲线演示每一步的计算（`report.js:mpExplain`，复用 `upperHull` / `kneeOf`）。
- 新增**避坑指南**（可在顶部取消“显示避坑”），由同一批冻结数据计算（`report.js:mpPitfalls`，Python 参考 `scripts/sweet_spot.py:profile_pitfalls`）：
  - 费用刺客：相邻两档成本至少翻倍，分数提升不到该评测分差的 12%；
  - 档位倒退：更高档低于同模型某个更低档（0.5 分 / 10 Elo 容差）；
  - 新一代更省：同产品线、发布更晚型号的某一档在所有共同评测上分数不低、费用不高；
  - 被同家其它型号全面超越：同一厂商其它活跃型号满足同样条件。
  前两类按单个评测标在格子里，后两类按整个档位标在列头。证据中标为慎用的档位（如 Sonnet 5.5 max）也列入费用刺客组，注明为检索摘要。
- 新增**更优替代**（`report.js:mpAlternatives`，Python 参考 `profile_alternatives`）：选一个档位（或点表格格子），逐个评测列出“同分最省”和“同价最高”两种替代；范围可选同厂商 / 四家全部，本模型其它档位也算候选。默认档位取官方默认。

## 结果

- 单元测试 56 项通过（新增避坑已知案例、产品线字段、更优替代）。
- 完整浏览器 smoke 通过（[smoke.json](smoke.json)）：24 款模型的甜蜜点（三档门槛）、避坑列表，以及每个档位在两种范围下的更优替代，都逐项等于 Python 参考；开关、深链与跳转可用；1440 / 390 / 320 无溢出，无 JS 错误或外部请求。
- 截图：[桌面 · Sonnet 5.5](desktop-sonnet55.png)、[桌面 · GPT 5.6 Sol](desktop-gpt56sol.png)、[深色 · Opus 5](dark-opus5.png)、[390px · Grok 4.7](mobile-390-grok47.png)、[320px · Fable 5.1](mobile-320-fable51.png)；参数见 [screenshots.json](screenshots.json)；[更优替代 · Grok 4.7 high · 四家全部](alternatives-grok47-all.png)。

运行环境与上一轮相同：云端容器、临时 venv 中的 Python Playwright 1.58.0、预装 Chrome for Testing 153（root 容器，本地关闭 Chromium 沙箱，仓库脚本未改）。
