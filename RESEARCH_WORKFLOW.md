# 按需研究、独立复核与后续自动化

本网站是个人参考资料。内容要求大抵靠谱、链接和日期可查；允许清楚标注的估算与社区反馈。独立复核重点抓明显的模型、单位、过时价格、比较口径和页面错误，不强制逐项交叉验证，不默认付费复跑基准。

## 已提供的入口

本地运行 `python scripts/research_workflow.py packet --scope pricing`，或在 main 上手动运行 **Research work packet**，operation=`packet`。scope 可选 all/models/pricing/benchmarks。输出包含基线提交、现有来源及两个角色的提示词：

- [研究者](research/automation/researcher.md)：按厂商或主题分工，修改源码与证据输入，提交 PR。
- [独立复核者](research/automation/reviewer.md)：查看当前 head、来源与预览，给出可接受/需修改及具体问题。
- [轻量更新记录](research/automation/update-note.md)：PR 中记录变化、日期、未核实项和复核 head。

该入口只生成任务包，没有调用任何模型。没有配置 LLM API secret、定时任务、GitHub App/PAT 或 Hermes 连接。现有 `build_report.py` 仍离线构建，不会自行调研数据。

完整流程是：用户发起任务包 → 研究者分别提交源码 PR → 无密钥确定性 CI → 独立 Worker 的原生 PR 预览 → 另一执行主体轻量复核 → 用户合并 → 现有 main 正式发布。研究者不能批准自己的研究变化。让多个 Agent 并行按厂商分工时，优先各自独立 PR；修改共享目录/模型身份映射前先协调，避免覆盖。

## 独立身份与复核状态

`research/automation/policy.json` 初始 `reviewer_logins=[]`、`auto_merge_enabled=false`、允许自动合并路径为空。配置为空表示身份未知，不能视为已经复核。

**Research work packet** 的 operation=`review-status`、PR=编号，会只读核查 GitHub reviews。仅统计用户配置的 reviewer login、非 PR 作者、当前 head 上最新有效的 APPROVED；过期、撤销、自评和未映射身份不计入。当前仍由用户决定合并。Agent 的文本复核结果可以供用户参考，但不自动等价于独立 GitHub 身份。

## 接入 SOP（后续经用户确认再启用）

1. 先手动跑通一次实际研究与独立复核，明确主题、频率、模型预算，以及哪类结果值得更新；示例是每周一次目录/价格变化检查，有重大变化再补充基准。没有变化时不要制造 PR。
2. 用户选择研究执行环境。GitHub Workflow 负责 dispatch/调度与可追溯 run；执行器接收 `work-packet.json`，只返回源码分支和 PR。研究者权限限于此仓库内容与 PR，复核者权限只够读取和提交 review；两者均不接触 Cloudflare token。新增 GitHub App、PAT 或长期身份权限先报告具体范围，由用户确认配置。
3. 用户提供或确认研究与复核的不同执行主体及 GitHub 登录映射，然后通过单独 PR 更新 `reviewer_logins`。同一个 bot 代替两个 Agent 发言不能证明独立身份；这种情况下保留用户人工复核，不开启自动合并。
4. 如用 Hermes，由用户先明确本机路径、连接方式、可调用模型与授权范围。再把“手动 dispatch 工作流 / 接收任务包 / 提交源码 PR”接到它的任务入口，不直接让 Hermes 发布 Worker。当前没有连接或改动 Hermes。
5. 用户批准频率、预算和凭据后，另一个 PR 接入实际模型执行器与 schedule；先保持 schedule/LLM 调用关闭完成审阅，再开启。密钥只配置在研究执行环境，不能进入任务包、报告、日志或公开 artifact。失败应保留可复核的原因，不自动重试付费调用。
6. branch protection/ruleset、Required reviewers、GitHub App 安装等持久权限变化分别确认；本 PR 不创建它们。需要时建议 main 通过 PR、通过 Verify static report，并由独立审阅者确认内容。具体规则名称以届时 CI check context 为准。

## 自动合并方案：默认关闭

当前不调用 merge API，也不配置 GitHub auto-merge。`auto_merge_enabled=false` 是明确状态；即使手改为 true，复核状态脚本也会拒绝，避免半成品策略意外生效。

启用前需要用户确认低风险范围和独立身份。建议先只考虑指定数据/说明文件的更新；发布工作流、脚本、依赖、模板/JS、安全策略、模型身份映射及权限设置都留给人工审阅。允许路径只是第一层，不能把“路径命中”当作研究内容一定低风险。

后续实现应在可信 main 上重新核查：PR 仍打开、head/base 未变化、确定性 CI 在当前 head 成功、当前 head 有已映射且非作者的独立有效批准、改动均在允许范围、没有权限/基础设施变更，再以 expected head SHA 调用受限合并入口。任一步未知就停在待审阅。启用开关、范围、执行身份和持久权限需另一个独立审阅 PR；本阶段不自动合并任何研究或基础设施 PR。
