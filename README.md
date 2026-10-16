# 模型能力、成本与任务选型报告

打开 [model-capability-cost.html](model-capability-cost.html)。这是包含数据、样式和脚本的单文件报告，可直接离线打开，无需安装依赖或联网加载。

静态发布准备、跨 macOS/Linux 验证、GitHub Actions、公开产物边界与回滚步骤见 [DEPLOYMENT.md](DEPLOYMENT.md)。发布使用独立 `dist/` 白名单；默认关闭实际 Cloudflare 部署，研究结论保持不变。

报告更新于 **2026-10-16（Asia/Taipei）**；本轮核验 Claude，并复核 Sol 6.1 的官方档位、选型及工具协议；其余 GPT / Gemini 规格仍为 10-15。范围是通用模型的 API 规格与公开评测；包括 20 个选型与兼容候选（含 14 款 Claude）、3 个 GPT 代际基线，另列 Mythos 的受限入口。专用图像、语音、视频生成模型及产品订阅配额不属于此次比较范围。选型建议是基于已列证据的判断，没有执行新的付费模型实验或中文实测。

## 阅读顺序

1. **选型概览**：Claude 全型号速查表覆盖截图 8 款、原有新版 4 款及官方仍可调用的 Opus 4.5 / Sonnet 4.5，支持“仅截图可见”筛选与 CSV 导出。9 类开发任务并列默认模型 / reasoning、Claude 新版及截图替代、升档换模型条件、逐行证据类型；7 类写作与研究建议保留“中文未实测”标记。新增 OpenClaw / Hermes 主控：工程 Sol 6.1 high、日常混合 medium，配套 Vulcan / AA 同档位对照、实际验收指标和配置落点。顶部可直接跳到任务表与主控建议。
2. **分项能力**：AA v4.3.2 共 20 个代表配置，保留各指标单位、快照与原始配置；支持只看 Claude 或截图 8 款。估计值显示星号；补充官方长上下文与多模态材料。
3. **成本与耗时**：AA、Vulcan、ToneBench、Agent Arena 分开筛选，查看来源、缺测、样本量及条件前沿。
4. **规格与预算**：官方 Standard 单价、输入能力、上下文、档位、缓存、推理用量、阶梯价与已公布优惠结束价。
5. **推理档位**：同模型相邻已测档位的分差与额外投入；区分收益变小、点估计下降和预算耗尽。2026-10-16 补充 Opus / Vulcan 的四种可切换证据：Frontier 完整配置、共同无回退 6 题子集、Routine v1 日常工单、官方 SWE-bench Pro 子集；各自保留限制和来源，支持单独导出 CSV。
6. **证据与方法**：核验时间、证据层级、方法、限制与直接来源。

## 数据与维护

- `九模型图表数据与来源/`：原附件，保持不变。
- `archive/model-capability-cost-2026-10-14.html`：修改前的原报告。
- `report-data.json` / `report-data.csv`：166 条记录，含原 121 条、新增 AA 14 条、ToneBench 19 条、Arena 12 条。本轮追加 22 条，前一版 144 条保持不变；原记录的原有字段和值保持不变，另加行 ID。
- `report-content.json`：官方规格、价格、补充指标和来源目录。报告中的“当前候选”是本报告的筛选范围，不表示官方停止供应其他型号。
- `research/2026-10-15/`：公开来源提取与复核说明；AA 比较页按实际表头映射；ToneBench 原始榜单与附件的 SHA256 一致。
- `research/2026-10-16/`：Opus 编码补充证据、来源快照与 SHA256；`recompute_opus55.py` 从 115 条公开运行记录、Routine 聚合 CSV 和官方档位表离线复算。共同无回退子集为事后选择，仅供探索，不能替代完整重跑；Routine 未披露 solver 回退明细。补充数据嵌入 JSON 的 `opus_coding_evidence`，不混入原 144 条记录与前沿。
- `research/2026-10-16/claude-catalog/`：官方生命周期、旧型号规格、effort / thinking、定价快照，以及 5 个 AA 比较页的同版提取。`recompute_claude.py` 离线追加 10 个 AA 配置与 12 个同快照 ToneBench 配置，输出 `claude-supplement.json`；3 个旧 Opus 综合分标为估计、缺费保留空值；Fable 5 max 的 AA / Tone 数据保留 4.8 回退标记。完整 14 款均纳入筛选、规格和预算，不以旧版 Vulcan 代填缺测。
- `research/2026-10-16/task-routing/`：本轮任务与主控选型的官方文档快照、URL / SHA256 清单、冻结报告记录子集及费用变化复算。`routing-evidence.json` 的主控配置属于推断建议；没有 OpenClaw / Hermes 同工作流实测。原 166 条记录、20 个 AA 代表配置和 Opus 四种证据保持不变。
- `research/2026-10-16/agent-division/`：固定 Sol 6.1 high 主控下的子 agent / 辅助任务分工，12 份官方文档与上游实现快照。报告新增 6 类子任务、6 类辅助调用、升级规则与框架配置对照；明确 Hermes 统一 delegation、独立 `/review`、同模型 background review 继承限制，以及原生 Codex compaction 的控制边界。并发 2、深度 1 属于待验收策略，不是框架默认或实测最优值。
- `report.template.html` / `report.css` / `report.js`：可维护的报告内容与交互源码。
- `build_report.py`：从原报告和本次证据构建，不访问网络。
- `validate_report.py`：数据保真与浏览器检查；`verification/validation.json` 保存检查结果和截图文件名。
- `verification/task-routing-validation-2026-10-16.json`：任务表、主控表、证据标记、快照保真、快捷跳转以及桌面 / 手机布局的本轮定向验收结果。
- `verification/agent-division-validation-2026-10-16.json`：新增分工表、配置字段、中文未实测提示、既有内容保真与桌面 / 手机布局的定向验收结果。此次只编辑报告，未写入 OpenClaw / Hermes 实际配置。

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

## 已保留的解释边界

不同基准的费用、分数、样本和时间不可直接混算。AA 的任务时间是估算值；Vulcan 和 ToneBench 的耗时来自各自运行口径。缺失费用保持为空，失败不会被剔除。默认配置、混合回退、Ultra 与未确认档位单独标记；前沿仅是当前筛选内的点估计，不证明统计显著性。

用户截图只证明选择器可见，不证明 API 授权或实际调用成功。Sonnet 4.5 已弃用但到 2026-11-30 才退役；Haiku 4.5 当前仍 Active。Haiku 4.5 / Sonnet 4.5 没有 effort 档位，Opus 4.5 的 thinking 预算独立于 effort；Opus / Sonnet 4.6 没有 xhigh。中文任务甜蜜点全部未实测。AA 中 Sonnet 4.5 的 1M 标注与当前官方 200k 不一致，规格和预算采用官方 200k / 64k，保留原始评测而不据此声称在当前窗口下复测过。

官方 API 单价不能换算产品订阅额度。预算计算器固定各模型使用相同 token 数，未保证同任务同用量；推理输出计费，工具、缓存写入/存储、税费和重试另算。Google 优惠结束情景只应用已公布的 Google 价格，其余维持核验日价格。研究整理阶段未执行发布或部署；静态发布阶段的范围和操作入口见 DEPLOYMENT.md。
