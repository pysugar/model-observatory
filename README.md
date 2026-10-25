# 模型观测站 · Model Observatory

打开 [model-capability-cost.html](model-capability-cost.html)。这是包含数据、样式和脚本的单文件报告，可直接离线打开，无需安装依赖或联网加载。

在线报告：<https://models.localgpt.net>。静态发布、跨 macOS/Linux 验证、GitHub Actions、公开产物边界与回滚步骤见 [DEPLOYMENT.md](DEPLOYMENT.md)。发布使用独立 `dist/` 白名单，研究结论保持不变。

页面底部显示环境、分支与可点击的短 commit；存在实际 tag 时一并显示。版本来源和实测记录见 [发布与验收记录](RELEASES.md)。

原生 PR 预览及 `preview` Environment 配置见 [PREVIEWS.md](PREVIEWS.md)；按需研究与独立轻量复核见 [RESEARCH_WORKFLOW.md](RESEARCH_WORKFLOW.md)；已验证版本与回滚见 [RELEASES.md](RELEASES.md)。原生 PR 预览已启用，创建/更新/清理权限 smoke 已通过；定时 LLM 调用和自动合并仍未开启。正式环境已切换为 `release`；旧 `cloudflare-preview` 保留备用，记录见 [环境迁移](RELEASE_ENVIRONMENT.md)。

## 当前项目状态（2026-10-24 模型档案）

[PR #21](https://github.com/pysugar/model-observatory/pull/21) 也已合并并正式发布（main merge `8040c1f58e2ba09e33d23703a7b0b296eb081241`，双入口 probe 通过，见 [PR21 发布收束](RELEASES.md#2026-10-24-pr21-模型档案甜蜜点更优替代与避坑指南正式发布收束)）：模型档案统一称“甜蜜点”并演示三档门槛，新增“更优替代”与可选的避坑指南，评测行对所有模型固定。

[PR #19](https://github.com/pysugar/model-observatory/pull/19) 已合并并完成正式发布：main merge 为 `f8e36ec7e18c97a5f799afe167355ea3a7c699ae`，两个正式入口的部署后 probe 均通过，记录见 [PR19 发布收束](RELEASES.md#2026-10-24-pr19-模型档案正式发布收束)。本轮基于 `main` 的 `d8ae6c3`（PR18 合并后）新增第 6 个页签**模型档案**（`#profiles`）：选一个模型，系统看它在 9 类任务 × 各原生档位下的实测分数、成本、边际收益、实测拐点和起步档，并给出每类任务的选档卡。范围是目录全部 24 款四家活跃型号（含 GPT 5.6 Sol / Luna），按“当前主力 / 上一代仍可用 / 兼容旧版”分组。“推理档位”页保持不变。

逐档数据全部沿用既有冻结输入；新增的 14 条补充证据来自 10-24 网页检索摘要（整理环境只能搜索、无法直接打开原页），逐条标注并只作参考，冲突项不覆盖原值。五站榜单仍为 10-23 快照。研究记录见 [2026-10-24 研究记录](research/2026-10-24/README.md)，验收见 [本地验收记录](verification/model-profile-2026-10-24/README.md)。

## 上一轮项目状态（2026-10-23 研究更新）

本轮改版基于 `main` 的 `f34421104d89d517a44be685a1338ec8845365cb`（PR17）；开始工作时只读核对远端 `main`，与本地一致。工作分支 `feat/observatory-refresh-2026-10-23`；提交后的 CI 与独立预览状态以该分支 PR 的检查及机器人评论为准，合并与正式发布仍由用户另行决定。本次用户明确要求在当前目录更新网站，因此在 Mac 本地完成实现；此前的 Hermes 分工记录不代表本次执行环境。

新增“最新榜单”：Artificial Analysis 23 条、Arena Text 17 条、LiveBench 22 条、Scale HLE Diamond 15 条、OpenRouter 周用量 10 条，共 **87 条选录**。支持来源切换、搜索、厂商筛选、排序、展开与保留来源元数据的 CSV。补入 DeepSeek、Muse、MiMo、MiniMax 等观测型号，未取得同协议逐档数据的型号不补造曲线。24 款规格型号的基础 Standard 价格复核至 10 月 23 日，修正 Grok 4.7 在完整 prompt **≥200,000 tokens** 时的整次阶梯计费。研究来源、变更和未核验项见 [本期研究记录](research/2026-10-23/README.md)。

界面采用深蓝页首、浅色研究工作区与蓝紫强调色；新增本期观察、价格日期提醒及浅色 / 深色 / 跟随系统选项，保留原有六个维度和逐档交互。截图及验证入口见 [本地验收记录](verification/observatory-refresh-2026-10-23/README.md)。

以下是更早记录的发布事实（PR18 的正式发布记录已补入 [RELEASES.md](RELEASES.md)）：

[PR #16](https://github.com/pysugar/model-observatory/pull/16) 已合并并完成正式发布：main merge 为 `1ed2900a756c1833611e5fb89d6f242399827f8d`，两个正式入口的部署后 probe 均通过，记录见 [PR16 发布收束](RELEASES.md#2026-10-20-pr16-界面与选档功能正式发布收束)。本轮把报告定位为个人选型参考：首屏是选档速查矩阵与避坑清单，象限改由数据决定，新增本页目录、系列聚焦和深色模式；研究数据未变。上一轮 [PR #14](https://github.com/pysugar/model-observatory/pull/14) 的记录见 [PR14 发布收束](RELEASES.md#2026-10-20-pr14-功能与正式发布收束)。后续线上状态仍以 `version.json` 与对应发布 run 为准。

报告内容核对日为 **2026-10-23**，各来源保留自己的快照/评测日期，不能把目录复核日当成评测日。当前有 169 条历史基准记录、87 条独立榜单选录、24 款目录模型（21 个选型与兼容候选）、21 个 AA 代表配置、50 条全局来源；组件内另有具名来源链接。AA 六域覆盖 90 个配置，发布系列为 30 版 / 94 个配置，其中 11 款模型的 44 个配置沿用 10 月 19–20 日的冻结子评测。范围仍是 API 规格、公开评测及明确标注的任务建议；专用生成模型、订阅配额换算、新付费评测和中文实测均未纳入。

## 阅读顺序

1. **选型概览**（`#overview`）：顶部是五站最新榜单、更新说明与价格日期提醒，其后是个人选档速查矩阵（每个模型 × 七类任务的甜蜜点档位，按“成本每翻倍的边际收益”找拐点，可切换省钱 / 均衡 / 性能优先门槛；每格附官方 / 经验起点与社区实测对照，点格子看逐档边际收益）和各档位避坑清单；再往下为四大家族五站全景、任务与主控/辅助分工建议、Claude 14 款速查、来源配置及 CSV。任务视图保留既有自定义公式与原始单位，不能重命名成官方通用任务指数。
2. **分项能力**（`#capabilities`）：AA 智能指数与六域排名、固定选中配置的完整七项面板；各模型已测档位曲线支持固定高亮、临时 hover/focus、重置及原始分数/差分表。另列分协议 Computer Use 证据和“避坑指南”的实测参考、多源经验、待验证提醒。
3. **成本与耗时**（`#explorer`）：AA、Vulcan、ToneBench、Agent Arena 各守分数与成本口径；可切换发布版本轨迹、来源、缺测、样本和点估计前沿。
4. **规格与预算**（`#specs`）：官方 Standard 单价、输入能力、上下文、原生档位、缓存、推理用量、阶梯价及来源已公布的价格情景；假设同 token 用量不等于同任务成本。
5. **推理档位**（`#reasoning`）：七模型×四任务的建议起点/甜点候选，与实测曲线分开。实测可选 AA 智能指数、HLE、CritPt、Terminal-Bench 4.0、SciCode 和六域；只有 AA 智能指数显示其综合加权成本，子评测无同口径费用时隐藏成本图。另有四张第三方能力证据卡、同模型差分和 Opus/Vulcan 四种独立证据视图。
6. **模型档案**（`#profiles`）：选一个模型（深链 `#profiles?m=<目录 id>`），看它在 9 类任务 × 原生档位下的实测分数、成本和“成本每翻倍得分”，标出当前门槛的甜蜜点、起步档和最高分，并附甜蜜点与三档门槛的计算演示；“更优替代”查任意一档的同分最省 / 同预算最强 / 不限预算最强替代（同厂商或四家全部），并附社区主流声音；可选的避坑指南列出费用刺客、档位倒退、新一代更省和被同家全面超越的档位；下方每类任务一张选档卡（起步档 / 甜蜜点 / 降档候选 / 升档上限 + 相关证据）。只有单点或无实测的型号如实显示，不补造曲线。
7. **证据与方法**（`#evidence`）：“如何参考评测”区分回答是否合意、任务是否省心、结果是否正确、成本是否值得；列方法、限制、核验时间与原始来源。英文原名仅在术语/原文来源语境保留。

## 更新线上报告

修改下面的源文件后提交 PR，通过验证并合入 `main`，既有流水线会自动构建并发布。`model-capability-cost.html` 与根目录 `report-data.json` / `report-data.csv` 是生成的离线产物；仅手改它们不会改变重建后的线上内容。

| 要修改的内容 | 编辑入口 |
| --- | --- |
| 页面文字、章节和静态表格 | [`report.template.html`](report.template.html) |
| 样式、布局 | [`report.css`](report.css) |
| 筛选、计算、图表与导出交互 | [`report.js`](report.js) |
| 模型目录、官方规格、价格、补充指标与来源 | [`report-content.json`](report-content.json) |
| 基准记录与证据汇总逻辑 | [`build_report.py`](build_report.py) 及下列证据输入 |

构建输入与实际实现入口如下；根目录生成产物不是编辑源。原 121 条记录来自 [原报告](archive/model-capability-cost-2026-10-14.html)，ToneBench 指纹与 [原附件](九模型图表数据与来源/tonebench.json) 对照；保真基线不改写。

| 功能 / 数据结构 | 冻结输入与渲染入口 | 回归入口 |
| --- | --- | --- |
| 最新榜单、官方价格日期提醒、主题选择 | [market-snapshot.json](research/2026-10-23/market-snapshot.json) → `market_snapshot`；`scripts/market_snapshot.py:refresh_panorama` 同步全景；`report.js:renderMarket` / `marketRows` / `marketExportRows` / `renderMarketIntro`；价格日历来自目录 `promo_end` / `future_*` | [test_market_snapshot.py](tests/test_market_snapshot.py)、`scripts/smoke.py:check_market_ui` |
| 既有记录、AA 代表配置、Opus 独立证据 | `research/2026-10-15/aa-pair-*.json`、[tonebench-leaderboard.json](research/2026-10-15/tonebench-leaderboard.json)、[arena-web-extract.json](research/2026-10-15/arena-web-extract.json)；`research/2026-10-16/claude-catalog/claude-supplement.json`、`research/2026-10-16/opus55-coding-supplement.json`；后者进入 `opus_coding_evidence` | `tests/test_publish.py`、`scripts/smoke.py`；历史复算入口见下文 |
| AA 六域、发布系列与五站全景 | [multi-benchmark-supplement.json](research/2026-10-19/multi-benchmark-supplement.json) → `aa_capability_indexes`、`aa_release_series`、`external_leaderboards`；`build_report.py:bind_panorama_capabilities`，`report.js:renderCapIndexChart` / `renderCapDetail`，计算/CSV 共用 `capScore` / `capRanking` / `capExportRows` | [test_capability_integrity.py](tests/test_capability_integrity.py)、[capability_smoke.py](scripts/capability_smoke.py) |
| 44 配置底层子评测 | [aa-effort-evals.json](research/2026-10-20/aa-effort-evals.json) → `aa_effort_evals` 及精确 variant 的 `evalMetrics` / `evalSourceUrl`；构建中另保留并标注派生 `taskScores`；`effortRows` / `renderReasoningCharts`、`renderEffortScalingChart` | `tests/test_report_claims.py`、`tests/test_capability_integrity.py`、`scripts/capability_smoke.py`、`scripts/scaling_smoke.py` |
| 原生档位建议 | [task-effort-guidance.json](research/2026-10-20/task-effort-guidance.json) → `task_effort_guidance`；`renderTaskAdvice`（`#taskEffortAdvice`） | [test_selection_guidance.py](tests/test_selection_guidance.py)、[selection_smoke.py](scripts/selection_smoke.py) |
| 第三方方法导航、实战证据卡 | [practical-evidence.json](research/2026-10-20/practical-evidence.json) → `practical_evidence`；`report.js` 中 `#practicalEvidence`，静态说明 `report.template.html:#benchmarkGuide` | `scripts/capability_smoke.py`、`scripts/selection_smoke.py` |
| 选档速查矩阵、官方/社区参考、避坑清单、象限分界 | `aa_release_series` 逐档数据 + `task_effort_guidance` + 编码行（Vulcan）；`report.js:renderSweetSpot` / `sweetPick` / `kneeOf` / `sweetRefs`，`taskQuadrant`；避坑数字用 `{{aa:…}}` 构建时解析；Python 参考实现 [sweet_spot.py](scripts/sweet_spot.py) | [test_sweet_spot.py](tests/test_sweet_spot.py)、`scripts/smoke.py:check_overview_ui` |
| 模型档案（单模型 × 任务 × 档位、选档卡、避坑指南、深链） | [model-effort-profiles.json](research/2026-10-24/model-effort-profiles.json) → `model_effort_profiles`（构建校验 `build_report.py:check_model_profiles`）；`report.js:renderModelProfile` / `mpSeries` / `mpPick` / `mpStart` / `mpExplain` / `mpPitfalls` / `mpAlternatives`，AA 行复用 `upperHull` / `kneeOf` / `sweetThreshold`；Python 参考 `scripts/sweet_spot.py:profile_series` / `profile_pitfalls` | [test_model_profiles.py](tests/test_model_profiles.py)、`scripts/smoke.py:check_profile_ui` |
| Computer Use、限定协议替代组合、三张经验卡 | [computer-use-evidence.json](research/2026-10-20/computer-use-evidence.json) → `computer_use_evidence`；`renderComputerUseEvidence`、`renderPitfallGuide` / `renderObservedConfig`；同一 `renderEffortScalingChart` 切换 OpenAI 曲线；`scalingRows` / `scalingPath`、`osworldSweepPoints` / `observedAlternatives` 负责差分、缺档和限定范围计算 | [test_computer_use.py](tests/test_computer_use.py)、[scaling_smoke.py](scripts/scaling_smoke.py) |

建议记录含 `modelId`、`nativeEffort`、`taskType`、`evidenceType`、`sourceUrl`、`checkedAt`、`caveats` 和已知时的 `sampleSize` / `harness`；`support` 将官方支持与任务经验映射分开。Computer Use 使用 `openaiSweep`、`anthropicMax`、`geminiReference`、`grokReference`、`pitfallExperience`、`pitfallReminders` 独立分组。来源 URL、版本、统计量、原生档位与未知协议字段应随记录保存；未知保持 null，不借用相邻来源补齐。

新增研究应保留带日期的快照、来源和核验记录，按需更新构建逻辑及验收预期。Claude / Opus 补充数据的复算命令见下文；CI 只读已有补充 JSON，不会自动运行复算脚本或联网调研。需要同步仓库里的离线报告时运行 `python3 build_report.py`，将生成变化随源码一起提交。

提交 PR 后，等待 CI 与原生预览两阶段成功，到 PR Conversation 中找 `github-actions[bot]` 的“最新预览 / 本次固定部署”评论；查找方式、Head 核对和 Draft 限制见 [PR 预览入口](PREVIEWS.md#提交-pr-后在哪里找预览)。合并 `main` 后自动正式发布，完整条件见 [发布触发条件](DEPLOYMENT.md#修改内容与自动上线条件)。

## 数据与维护

- `九模型图表数据与来源/`：原附件，保持不变。
- `archive/model-capability-cost-2026-10-14.html`：修改前的原报告。
- `report-data.json` / `report-data.csv`：当前 169 条基准记录；原 121 条原有字段和值保持不变，另加行 ID。166 条及 144 条是先前补充阶段的历史基线，不再代表当前总数。Computer Use 与经验卡是 JSON 独立结构，不混入这 169 条记录。
- `report-content.json`：官方规格、价格、补充指标和来源目录。报告中的“当前候选”是本报告的筛选范围，不表示官方停止供应其他型号。
- `research/2026-10-23/market-snapshot.json`：87 条独立榜单选录、来源日期与本期核验日期。它不进入原 169 条记录、旧 AA 逐档曲线或跨源前沿；JSON 和单独的榜单 CSV 都保留缺失值。
- `research/2026-10-15/`：公开来源提取与复核说明；AA 比较页按实际表头映射；ToneBench 原始榜单与附件的 SHA256 一致。
- `research/2026-10-16/`：Opus 编码补充证据、来源快照与 SHA256；`recompute_opus55.py` 从 115 条公开运行记录、Routine 聚合 CSV 和官方档位表离线复算。共同无回退子集为事后选择，仅供探索，不能替代完整重跑；Routine 未披露 solver 回退明细。补充数据嵌入 JSON 的 `opus_coding_evidence`，不混入原 144 条记录与前沿。
- `research/2026-10-16/claude-catalog/`：官方生命周期、旧型号规格、effort / thinking、定价快照，以及 5 个 AA 比较页的同版提取。`recompute_claude.py` 离线追加 10 个 AA 配置与 12 个同快照 ToneBench 配置，输出 `claude-supplement.json`；3 个旧 Opus 的 AA 智能指数标为估计、缺费保留空值；Fable 5 max 的 AA / Tone 数据保留 4.8 回退标记。完整 14 款均纳入筛选、规格和预算，不以旧版 Vulcan 代填缺测。
- `research/2026-10-16/task-routing/`：该阶段任务与主控选型的官方文档快照、URL / SHA256 清单、冻结报告记录子集及费用变化复算。`routing-evidence.json` 的主控配置属于推断建议；没有 OpenClaw / Hermes 同工作流实测。原 166 条记录、20 个 AA 代表配置和 Opus 四种证据保持不变。
- `research/2026-10-16/agent-division/`：固定 Sol 6.1 high 主控下的子 agent / 辅助任务分工，12 份官方文档与上游实现快照。报告新增 6 类子任务、6 类辅助调用、升级规则与框架配置对照；明确 Hermes 统一 delegation、独立 `/review`、同模型 background review 继承限制，以及原生 Codex compaction 的控制边界。并发 2、深度 1 属于待验收策略，不是框架默认或实测最优值。
- `report.template.html` / `report.css` / `report.js`：可维护的报告内容与交互源码。
- `build_report.py`：从原报告和本次证据构建，不访问网络。
- `validate_report.py`：数据保真与浏览器检查；`verification/validation.json` 保存检查结果和截图文件名。
- `verification/task-routing-validation-2026-10-16.json`：任务表、主控表、证据标记、快照保真、快捷跳转以及桌面 / 手机布局的本轮定向验收结果。
- `verification/agent-division-validation-2026-10-16.json`：新增分工表、配置字段、中文未实测提示、既有内容保真与桌面 / 手机布局的定向验收结果。该阶段只编辑报告，未写入 OpenClaw / Hermes 实际配置。

重建：

```sh
# 在仓库根目录运行（仅 Python 标准库）：
python3 build_report.py
# 发布目录构建，不改写根目录报告：
python3 scripts/publish.py build
```

修改 Opus 原始补充证据后，先运行 `research/2026-10-16/recompute_opus55.py`，再重建报告。复算过程不访问网络或调用模型。

修改 Claude 扩展快照后，先运行 `research/2026-10-16/claude-catalog/recompute_claude.py`，再重建报告。两份补充脚本相互独立；原附件保持不变。

如需复跑浏览器验证，在一个终端启动本地服务，在另一个终端运行验证脚本。脚本使用已安装的 Google Chrome 和临时空白配置，不读取个人浏览器资料；Codex 在 macOS 上执行启动 Chrome 的命令时，必须从第一次尝试就使用 `sandbox_permissions="require_escalated"` 并获准后执行，不在默认沙箱中启动，不用 `--no-sandbox` 绕过主机限制。

```sh
# 在仓库根目录运行：
python3 -m http.server 8766 --bind 127.0.0.1
```

```sh
python3 validate_report.py
```

## 当前功能决策与不可回归边界

- **最新榜单**：序号仅表示当前筛选的排列位置，来源排名另列；AA 保留公开榜单舍入精度，含回退配置显式标记。LiveBench 的每成功任务成本与 AA 的加权单任务成本不同；Arena、Scale 与 OpenRouter 本视图不提供费用。来源更新日期未知保留 null。OpenRouter 是周 token 用量热度，free 版本独立，不是能力或用户数；保留 CC BY 4.0 归属。
- **价格边界**：`tier_inclusive=true` 用于 Grok 4.7 的 ≥200k 整次计费；其余已有 `tier_threshold` 默认严格大于，不能统一改成含边界。本轮价格复核不自动改变未复核的模型生命周期、原生档位或评测协议。
- **术语与排名**：用户可见文字和 CSV 表头统一“AA 智能指数”，不用裸缩写 II。内部字段和原始引用不盲目重命名。代表配置按该版整体最高分选取，不等于每个子领域最佳；按来源精度并列（1、1、3），分母为有效样本，当前筛选排名与来源全球排名分开。
- **缺失与来源**：缺失领域/子评测不借总体分填充、不填零、不参排，不跨缺测档连线；已测档位图的相邻档位差分遇缺档留空，显式跨档比较须标明两端实测配置。没有该指标成绩来源就显示普通空状态，不能生成空 href 或伪造评测来源。不同版本、harness、单位和成本定义不混算。
- **图表交互**：点击模型图例/选择器固定高亮，hover/focus 只临时强调并保留固定选择；再次点击或重置回到总览。原始分数与差分明细同步固定模型，逐点键盘和真实触屏可用，不能重新引入嵌套按钮。少于两点仅显示单点与解释；保留真实下降，不强制单调。标题为“各模型在已测推理档位下的成绩”；原生 effort 是离散类别，各厂商的 high 不等预算，也不假定各模型都有 non-reasoning 起点。
- **建议与测量**：七模型×四任务是建议起点/甜点候选，不是通用最优；官方建议、社区小样本和经验先验分别标记。未知版本显示“暂无版本级建议”，不继承厂商或旧版先验；Grok 的原生支持不包含 max。实际模型/框架配置不会因网页选型建议而自动改变。
- **Arena**：Text 是匿名成对回答偏好；Agent 是真实会话因果追踪的净改善，不是配对投票或绝对成功率；事实性调整后的 Text/Search 与纯偏好排名分开。原始百分比、净改善、事实核验和成本互补参考，不相加成总能力分。Agent 信号采用 2026-10-12 定义：Steerability 是用户纠偏负担，Bash Reliability 替代旧 Recovery；未回应完成确认不等于客观失败。
- **Computer Use**：OpenAI `OSWorld 2.0 / offline / v2026.08.08 / partial reward` 是 3 模型×5 档的 15 点同评测费用曲线，协议未知字段保留 null；Sol high→xhigh 的实际下降保留。Anthropic 是 `2026-09-10` 全套、max 单点，partial reward 与 strict success rate 分列，保留 Opus 文档称 2.0、Sonnet 文档称 v2.1 的原始命名。Gemini 是独立的最高 thinking、原生 effort 未核验、3 次取最大单点，不叠加到均值/其他曲线。Grok 为“未发现公开可核实成绩”，不填零、不推断不支持；旧 OSWorld-Verified 和 WebArena/浏览器任务也不混入。
- **避坑指南**：实测参考仅在上述 OpenAI 15 个完整分数/费用点中，按同协议、单位与成本定义的原始精度计算观测支配：替代分数不低、费用不高，且至少一项严格改善。每项最多两个去重替代：达到当前分数的最低费用配置、当前预算内最高分配置；同分同价用稳定键排序，显示时才舍入。区分同模型较低档替代与跨模型“切换配置”，不推断品牌档次。无置信区间不声称显著优势或退化，无延迟不声称更快；非支配点不认证为最优。
- **选档速查（个人偏好）**：报告定位是个人选型参考。甜蜜点是“边际收益拐点”：在（log₂ 单任务成本，分数）上取上凸包，从最便宜的已测档往上走，只要成本每翻一倍仍提升本列全部配置分差的 20% / 12% / 6%（省钱 / 均衡 / 性能优先）就继续升档。不要退回“离最高分 N 分内取最便宜”，它对一路上升的曲线会选到 max。门槛是可切换的个人偏好预设，不是通用最优；成本统一用 AA 综合单任务成本，只比较档位间的相对费用。官方 / 经验起点与社区实测（任务档位建议、Vulcan 同规则拐点）并排展示，不加权合成一个“综合档位”。规则改动须同步 `scripts/sweet_spot.py`，smoke 会逐格比对。
- **模型档案**：每类任务的评测行对所有模型固定（编程永远是 AA · Terminal-Bench + SciCode 再 Vulcan，行标题写明单位），没测的行显示“未测”，避免切换模型时把不同评测的数字放在同一位置比较。每行只在同一评测内比较，甜蜜点（边际收益拐点）规则与选档速查完全相同（AA 行逐格一致，smoke 覆盖 24 款 × 三档门槛）；页面统一称“甜蜜点”，并附按所选模型演示的计算步骤；页面只写面向读者的规则，不写改版过程等内部决策。避坑指南的四条规则固定、不随门槛切换：费用刺客 = 相邻两档成本 ≥2 倍且分数提升 < 该评测分差 12%；档位倒退 = 更高档低于同模型某更低档 0.5 分 / 10 Elo 以上；新一代更省 / 被同家全面超越 = 同厂商活跃型号的某一档在双方共同测过的所有评测上分数不低、费用不高（至少一项更好），同产品线（`line`）且 AA 发布日期更晚记为新一代。规则改动须同步 `scripts/sweet_spot.py:profile_pitfalls`，smoke 会逐项比对。“更优替代”回答特定模型 × 特定档位有没有更好的选择：逐个评测给出“同分最省”（分数不低、费用最低）与“同预算最强”（费用不超过当前、分数最高）两种替代，以及“不限预算最强”（不看费用、分数最高，回答不差钱时选谁），范围可选同厂商或四家全部活跃型号，本模型其它档位也算候选并标“降档/换档”；默认档位取官方默认，参考实现 `profile_alternatives`。表下写明覆盖不到的维度（长时 agent 稳定性、最难题上限、需求模糊时的判断等），并列出“社区主流声音”（[community-consensus.json](research/2026-10-25/community-consensus.json)）：只是文字参考，标出来源一致性与检索摘要，不进入任何计算；目前覆盖 GPT-6 Astra 与 GPT-6.1 Sol。起步档的优先级：档位建议记录 > 任务范围补充证据 > 全任务补充证据 > 官方默认。检索摘要类证据只出现在文字里，不进入拐点、前沿或任何计算。目录未列但有实测的档位标“目录未列”，补充证据提到但目录未列的档位标“待核验”（目前仅 Grok 4.7 medium），不回写目录。
- **象限与聚焦**：Most attractive quadrant 的分界取当前任务全部已测档位的分数中位数 × 成本中位数（发布版本图同理），也可选个人预算；不再用手填常量（旧的 $1.10 恰好框住 Sol 6.1 整条曲线）。点击胶囊 / 圆点聚焦一个系列，其他系列与标签淡化，再点或“显示全部模型”恢复；悬停只临时预览。
- **视觉与导航**：颜色走 `report.css` 顶部的语义变量，深色模式只重定义变量；`report.js` 里 SVG 的硬编码颜色靠 CSS 属性选择器映射到变量，新增图表颜色要么用变量，要么加进这组映射。本页目录用按钮而非 `#锚点`，因为 hash 表示页签。长口径说明默认折叠为两行（悬停 / 聚焦展开、打印全文）；概览大表不用 `<details>` 折叠，smoke 会直接操作其中的控件。
- **多源经验也可参考**：不是每条提醒都要求完整测量；必须保留任务/版本、条件、行动与独立原始来源，转载不计第二来源。当前三张“多源经验参考”默认只显示坑点和动作，来源/边界折叠；不视为所有当前模型的既定缺陷，不套用用户节省比例。`pitfallReminders.cards` 为空是有意的有效状态，不能造填充内容。

## 已知限制与后续优化入口

- 档位建议与社区证据不建立任务最优结论，中文任务、真实业务成功交付成本与订阅消耗仍需独立验证；现有资料不授权新付费调用。
- Computer Use 尚缺跨厂商统一 harness、预算、重复次数和置信区间；OpenAI 协议未知项不能从 Anthropic/Gemini 继承。Anthropic 只有 max，Gemini 统计量不同，不能拼曲线或自动扩展 Pareto 范围。
- 方案/架构设计仍“暂无直接可比公开成绩”；第三方导航不表示已抓取完整新榜单，不用通用指数代替架构质量。新增来源/分数需另有范围授权及可比协议证据。
- 先沿既有组件改善可读性、筛选/空状态和可访问性，再补证据；不用重复图表、任意价值阈值或负面传闻替代现有数据路径。选档门槛是用户可切换、在页面写明的偏好预设，属于展示规则，不是证据结论。
- 选档矩阵的社区参考目前只覆盖编程列（Vulcan 23 题、一条修 bug 社区甜点）；七个任务的官方起点多为不分任务的默认档位。补社区实践需按研究流程带来源与日期并入 `task-effort-guidance.json`，矩阵会自动显示。
- 模型档案的 10-24 补充证据全部是检索摘要，原页待有网络权限时逐条复核；Grok 4.7 medium 是否受支持、Gemini 3.8 Flash 逐档费用口径、GPT 6 Astra 默认档仍待核验。
- 概览图在右上角模型密集时，聚焦系列的个别档位标签仍可能被模型名标签遮挡，明细以图下表格为准。
- 自动调研、定时付费模型执行、自动合并及云端迁移均未启用。持久权限、执行器和网络变更须另行明确授权，见 [协作与环境边界](RESEARCH_WORKFLOW.md#当前手动协作与环境边界2026-10-20)。

## 后续 agent 交接

1. 先读本页、[RELEASES.md](RELEASES.md) 和与任务相应的发布/研究文档，检查实际 HEAD、分支、状态及仓库指引；PR14、PR16、PR18、PR19、PR21 已合并关闭，后续从当前 main 新建分支，不复用它们或重置他人工作。
2. 对照上表查原始输入、JSON 字段、现有渲染与测试，区分已实现、冻结观测、经验建议和待验证。旧验收记录的 pending/dirty 属于当时 head，不能覆盖当前已完成状态。
3. 改产品时只编辑真实源文件/冻结补充输入，再用 `python3 build_report.py` 同步必要生成文件；不要只手改生成 HTML/JSON。文档任务只改文档，不顺手重建报告。
4. 验证按改动影响选择：数学/数据不变量用相应单元测试；交互沿 `scripts/smoke.py` 调用既有三个浏览器模块。真实产品改动在提交后做干净构建、准确 SHA 校验和 1440/390/320 键盘/真实触屏检查；纯文档做链接、路径、命令与差异校验即可。命令和 sandbox 要求见 [本地验证](DEPLOYMENT.md#本地验证)。
5. 研究/方案与只读复核由协调线程准备，Hermes 顺序实现、测试、提交；Mac 做低成本中转、只读验收及当次明确授权的 API 操作。身份和权限边界见 RESEARCH_WORKFLOW，不读取或复制私钥/凭据，不改模型/reasoning 或全局环境。
6. 提交/普通 SSH 推送后区分源码 head、CI build、预览部署与生产版本。新 Draft PR 可触发 CI，但原生预览不接收 Draft；查 [PREVIEWS.md](PREVIEWS.md)，不把旧预览当生产或用旧合并授权发布下一次变更。合并、正式发布和新持久授权都按当次任务范围处理。

## 已保留的解释边界

不同基准的费用、分数、样本和时间不可直接混算。AA 的任务时间是估算值；Vulcan 和 ToneBench 的耗时来自各自运行口径。缺失费用保持为空，失败不会被剔除。默认配置、混合回退、Ultra 与未确认档位单独标记；前沿仅是当前筛选内的点估计，不证明统计显著性。

用户截图只证明选择器可见，不证明 API 授权或实际调用成功。Sonnet 4.5 已弃用但到 2026-11-30 才退役；Haiku 4.5 当前仍 Active。Haiku 4.5 / Sonnet 4.5 没有 effort 档位，Opus 4.5 的 thinking 预算独立于 effort；Opus / Sonnet 4.6 没有 xhigh。中文任务甜蜜点全部未实测。AA 中 Sonnet 4.5 的 1M 标注与当前官方 200k 不一致，规格和预算采用官方 200k / 64k，保留原始评测而不据此声称在当前窗口下复测过。

官方 API 单价不能换算产品订阅额度。预算计算器固定各模型使用相同 token 数，未保证同任务同用量；推理输出计费，工具、缓存写入/存储、税费和重试另算。Google 优惠结束情景只应用已公布的 Google 价格，其余维持核验日价格。最初研究整理阶段未执行部署；PR14 的正式上线已另行完成，见 RELEASES.md，后续发布入口仍见 DEPLOYMENT.md。
