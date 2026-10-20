# 按需研究、独立复核与后续自动化

本网站是个人参考资料。内容要求大抵靠谱、链接和日期可查；允许清楚标注的估算与社区反馈。独立复核重点抓明显的模型、单位、过时价格、比较口径和页面错误，不强制逐项交叉验证，不默认付费复跑基准。

## 已提供的入口

本地运行 `python3 scripts/research_workflow.py packet --scope pricing`，或在 main 上手动运行 **Research work packet**，operation=`packet`。scope 可选 all/models/pricing/benchmarks。输出包含基线提交、现有来源及两个角色的提示词：

- [研究者](research/automation/researcher.md)：按厂商或主题分工，修改源码与证据输入，提交 PR。
- [独立复核者](research/automation/reviewer.md)：查看当前 head、来源与预览，给出可接受/需修改及具体问题。
- [轻量更新记录](research/automation/update-note.md)：PR 中记录变化、日期、未核实项和复核 head。

该入口只生成任务包，没有调用任何模型。没有配置自动研究执行器所需的 LLM API secret、定时任务、GitHub App/PAT 或 Hermes 自动接入；下述已授权的手动 Hermes 实现不等于启用了自动流水线。现有 `build_report.py` 仍离线构建，不会自行调研数据。

完整流程是：用户发起任务包 → 研究者分别提交源码 PR → 无密钥确定性 CI → 独立 Worker 的原生 PR 预览 → 另一执行主体轻量复核 → 用户合并 → 现有 main 正式发布。研究者不能批准自己的研究变化。让多个 Agent 并行按厂商分工时，优先各自独立 PR；修改共享目录/模型身份映射前先协调，避免覆盖。

## 当前手动协作与环境边界（2026-10-20）

PR14 已按“协调线程研究/方案与只读验收 → Hermes 实现/测试/提交 → 既有预览与正式发布链路”完成并上线，见 [版本记录](RELEASES.md#2026-10-20-pr14-功能与正式发布收束)。这修正了早期“尚未使用 Hermes”的阶段描述，但没有启用自动调研、定时模型调用或自动合并。

- Hermes 执行主机是 `ubuntu-desktop.local`，实际 hostname=`ubuntu-gk55`，用户 `james`。本轮延续 checkout 为 `/home/james/projects/model-observatory-pr14`；目录名是历史名称，不表示仍在旧 PR 分支。每次先核实当前分支/HEAD/状态，保留未预期修改，只允许一个写入者顺序实现。
- 协调线程准备研究、方案和只读复核；Hermes/Codex CLI 在 Ubuntu 实际编辑和测试。Mac 只作低成本中转、只读验收及当次明确授权的 GitHub 操作，不在那里另行实现产品或文档。不擅自更换现有模型/reasoning 配置或派发其他 agent。
- Git remote 保持 `git@z.github.com:pysugar/model-observatory.git`，它是选择已验证 pysugar 身份的 **Git SSH** 入口；只用正常分支推送，不 reset/force 覆盖他人工作。`z.github.com` 不是 GitHub API host；API 使用 `github.com`，绝不设置 `GH_HOST=z.github.com`。
- Ubuntu `gh` 当前身份是 muchenzhan，不允许用它对该仓库做 API 写操作，也不切换账号。已有 Mac pysugar 身份由协调线程操作；新 PR、评论、描述等外部写入只按当次明确授权执行。本次文档 Draft PR 由 Hermes 准备标题/正文文件、Mac 创建并核验 draft；不授权合并或自动合并。
- 先前 PR14 描述改写曾因缺少公开审阅/验收声明写入授权被自动审批拒绝，该拒绝仍有效。新的文档 Draft PR 授权不允许重试或间接改写 PR14 描述；被拒动作须报告目标、原因与是否执行，不换工具/路径/身份绕过。
- 不读取、复制或保存私钥内容、Token 或其他凭据；不新增长期授权/API key，不改全局 SSH、安全、网络或环境配置。用户讨论未来云迁移不等于授权执行网络或主机迁移。
- PR14 合并/发布授权已在该 PR 履行，不沿用到后续分支。后续从 main 新开任务分支；源码、CI build、预览和正式版本分开核验。Draft CI 与无预览的行为见 [PREVIEWS.md](PREVIEWS.md)。

工程入口和功能决策只维护在 [README](README.md)，发布事实只维护在 [RELEASES.md](RELEASES.md)；不要另建平行上下文/决策文档栈。现有 `research/automation/*.md` 是任务包模板，不是新权限或已启用自动执行器的证据。

## 独立身份与复核状态

`research/automation/policy.json` 初始 `reviewer_logins=[]`、`auto_merge_enabled=false`、允许自动合并路径为空。配置为空表示身份未知，不能视为已经复核。

**Research work packet** 的 operation=`review-status`、PR=编号，会只读核查 GitHub reviews。仅统计用户配置的 reviewer login、非 PR 作者、当前 head 上最新有效的 APPROVED；过期、撤销、自评和未映射身份不计入。当前仍由用户决定合并。Agent 的文本复核结果可以供用户参考，但不自动等价于独立 GitHub 身份。

## 接入 SOP（后续经用户确认再启用）

1. PR14 已跑通手动实现、只读验收、预览与正式发布；接入自动研究前仍须明确主题、频率、模型预算，以及哪类结果值得更新；示例是每周一次目录/价格变化检查，有重大变化再补充基准。没有变化时不要制造 PR。
2. 用户选择研究执行环境。GitHub Workflow 负责 dispatch/调度与可追溯 run；执行器接收 `work-packet.json`，只返回源码分支和 PR。研究者权限限于此仓库内容与 PR，复核者权限只够读取和提交 review；两者均不接触 Cloudflare token。新增 GitHub App、PAT 或长期身份权限先报告具体范围，由用户确认配置。
3. 用户提供或确认研究与复核的不同执行主体及 GitHub 登录映射，然后通过单独 PR 更新 `reviewer_logins`。同一个 bot 代替两个 Agent 发言不能证明独立身份；这种情况下保留用户人工复核，不开启自动合并。
4. 如用 Hermes，由用户先明确本机路径、连接方式、可调用模型与授权范围。再把“手动 dispatch 工作流 / 接收任务包 / 提交源码 PR”接到它的任务入口，不直接让 Hermes 发布 Worker。自动化执行器仍未接入；PR14 的手动实现已使用 Hermes，不代表 Workflow 可以调度它。
5. 用户批准频率、预算和凭据后，另一个 PR 接入实际模型执行器与 schedule；先保持 schedule/LLM 调用关闭完成审阅，再开启。密钥只配置在研究执行环境，不能进入任务包、报告、日志或公开 artifact。失败应保留可复核的原因，不自动重试付费调用。
6. branch protection/ruleset、Required reviewers、GitHub App 安装等持久权限变化分别确认；本 PR 不创建它们。需要时建议 main 通过 PR、通过 Verify static report，并由独立审阅者确认内容。具体规则名称以届时 CI check context 为准。

## 自动合并方案：默认关闭

当前不调用 merge API，也不配置 GitHub auto-merge。`auto_merge_enabled=false` 是明确状态；即使手改为 true，复核状态脚本也会拒绝，避免半成品策略意外生效。

启用前需要用户确认低风险范围和独立身份。建议先只考虑指定数据/说明文件的更新；发布工作流、脚本、依赖、模板/JS、安全策略、模型身份映射及权限设置都留给人工审阅。允许路径只是第一层，不能把“路径命中”当作研究内容一定低风险。

后续实现应在可信 main 上重新核查：PR 仍打开、head/base 未变化、确定性 CI 在当前 head 成功、当前 head 有已映射且非作者的独立有效批准、改动均在允许范围、没有权限/基础设施变更，再以 expected head SHA 调用受限合并入口。任一步未知就停在待审阅。启用开关、范围、执行身份和持久权限需另一个独立审阅 PR；本阶段不自动合并任何研究或基础设施 PR。
