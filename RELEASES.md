# 版本记录与回滚

公开 `version.json` 记录 source commit、内容核查日期和四个资产 SHA-256；新增构建还记录公开的 CI run/attempt/event/build SHA，PR 构建补充 PR/head/base。它不包含凭据。源码、构建产物、Cloudflare 部署和线上验收是不同状态，必须分别核对。

| 已验证的正式版本 | 变化 | GitHub 发布证据 |
| --- | --- | --- |
| `4e415ccc42761781d6181716b6b54347f73f0151` | 静态发布；明确探针 User-Agent | [run 38899413377](https://github.com/pysugar/model-observatory/actions/runs/38899413377) |
| `fad60bb217e1dcdaf56f520f22520fb2eef0c428` | 自定义域名、no-transform、双入口验收 | [run 38904557119](https://github.com/pysugar/model-observatory/actions/runs/38904557119) |
| `976dbc0b46a173705bd3ad206cd3fb5ba2e84b56` | 账户 ID 改读 Environment variable | [run 38929252801](https://github.com/pysugar/model-observatory/actions/runs/38929252801) |
| `12c638cca189eada0bac59fdff2044cad06a8e16` | PR #5：可信原生预览与研究工作流 | [run 39155391041](https://github.com/pysugar/model-observatory/actions/runs/39155391041) |
| `06af55ffdbe94b7c8b34cb3fcc89dd2e488015b9` | PR #6：补齐静态配置白名单 | [run 39156303630](https://github.com/pysugar/model-observatory/actions/runs/39156303630) |
| `06b59e39a9ec8085928788e6fb1914ce414bff52` | PR #7：版本化 Wrangler JSONL 输出 | [run 39156779873](https://github.com/pysugar/model-observatory/actions/runs/39156779873) |
| `7129c59f816b060ef0df846da667a769cc120050` | PR #8：独立预览 Worker 地址初始化入口 | [run 39157322608](https://github.com/pysugar/model-observatory/actions/runs/39157322608) |
| `e36e8f9e01e8b2362849a2009c62769e2138fa95` | PR #10：页脚构建身份、生产切换至受保护的 release | [run 39160593783](https://github.com/pysugar/model-observatory/actions/runs/39160593783) |
| `5eab3d03a4abf61cdaa500669cd5d712e48d8428` | PR #14：能力完整性、档位交互与建议、Computer Use、避坑经验卡 | [run 39397926762](https://github.com/pysugar/model-observatory/actions/runs/39397926762) |
| `1ed2900a756c1833611e5fb89d6f242399827f8d` | PR #16：选档速查矩阵、官方/社区参考、本页目录、数据中位数象限、系列聚焦、深色模式 | [run 39423917650](https://github.com/pysugar/model-observatory/actions/runs/39423917650) |
| `d8ae6c3088429599c2883c0c6bba07569cf4c268` | PR #18：最新榜单五站选录、官方价格复核、页面改版与主题选择 | [run 39987003757](https://github.com/pysugar/model-observatory/actions/runs/39987003757) |
| `f8e36ec7e18c97a5f799afe167355ea3a7c699ae` | PR #19：模型档案页签（单模型 × 任务 × 档位、选档卡、深链） | [run 40132928451](https://github.com/pysugar/model-observatory/actions/runs/40132928451) |
| `8040c1f58e2ba09e33d23703a7b0b296eb081241` | PR #21：模型档案统一“甜蜜点”说法与门槛演示、更优替代、避坑指南、固定评测行 | [run 40136499170](https://github.com/pysugar/model-observatory/actions/runs/40136499170) |
| `3c4080fd844c4d401b70b2449682a7310c09b7d7` | PR #23：更优替代列名改为“同预算最强”、去掉页面上的内部说明（仅文案） | [run 40161424122](https://github.com/pysugar/model-observatory/actions/runs/40161424122) |
| `288defa3ffc7029e20c2a98a52e1ccf95a2a7e22` | PR #24：不限预算推荐、过度思考避坑、别默认最高档的场景、按工作阶段的主流档位、社区主流声音 | [run 40163673486](https://github.com/pysugar/model-observatory/actions/runs/40163673486) |
| `8d5ab9af93773d2d3e3701925b181611ea7f2638` | PR #25：社区主流声音覆盖四家全部当前主力型号（并带入 PR23 / PR24 发布记录） | [run 40168720237](https://github.com/pysugar/model-observatory/actions/runs/40168720237) |
| `9ac686c2ba8057c1fa1d993ebb915b5054f04dd0` | PR #28：最新榜单新增 AA 智能指数 v5 页签（新口径、较 v4.3.2 变化、来源一致性、新版计算方式） | [run 40650595388](https://github.com/pysugar/model-observatory/actions/runs/40650595388) |
| `c6ab1d6b6463aa49073b8aba1cc99a87633272db` | PR #30：AA v5 榜单改用原页数据（26 个配置含费用、速度、子评测）并默认打开，能力指数图标明版本 | [run 40658487724](https://github.com/pysugar/model-observatory/actions/runs/40658487724) |

以上版本均有成功发布 run；2026-10-18 的工作流修复与初始化没有改动研究数据内容。Cloudflare 版本 ID 以各 run 的上传日志与 Worker 控制台为准，不猜测 ID。

新预览每次生成 `preview-record-<run>-<attempt>` artifact（保留 90 天）：PR、head/base/build、验证 run/attempt、artifact ID/digest、发布脚本的 main SHA、Cloudflare Preview/deployment ID、稳定/固定 URL、内容日期、轻量行数变化及最终状态。`upload-started`/`uploaded` 不等于验收成功；`verified` 才确认两个地址与原产物一致。清理后 PR 评论变为已清理，固定地址也失效。

后续正式版本的最小记录包括：合并 PR、main SHA、GitHub run、Cloudflare 版本 ID（上传日志）、线上 `version.json` 与两个地址的探针结果。可在下一次更新本文件时追加，或把原工作流 evidence 长期归档；不要在日志中保存 Token。仅凭版本字符串或页面打开不足以证明内容一致。

## 2026-10-19 预览与 release 实测

[PR #10](https://github.com/pysugar/model-observatory/pull/10)完成实际功能的完整流程，未改动模型数据（166 条、23 模型、44 来源）：

| 阶段 | 可核对记录 |
| --- | --- |
| PR 验证 | head `8cc77117803993e7eb120371590d7f030b7ed028`；合成 build `cc6bb7521bbe4bd718a81cc944c2921dd33460eb`；[CI 39160237482](https://github.com/pysugar/model-observatory/actions/runs/39160237482)成功 |
| 原生预览 | [run 39160333711](https://github.com/pysugar/model-observatory/actions/runs/39160333711)成功；`preview-record-39160333711-1` 记录 status=verified；Cloudflare deployment `afa5c7f6-ce25-47a9-9dff-b86bfb2a3a1a`；稳定及固定地址均与原 CI 产物一致 |
| 正式发布 | merge `e36e8f9e01e8b2362849a2009c62769e2138fa95`；[run 39160593783](https://github.com/pysugar/model-observatory/actions/runs/39160593783)成功；Environment=`release`，GitHub deployment=`7159831108`；Cloudflare version=`8befdde6-01d1-4272-8182-e3c3eac330b2`；两个正式入口通过版本、资产哈希与响应头核验 |
| 自动清理 | [run 39160593391](https://github.com/pysugar/model-observatory/actions/runs/39160593391)成功；artifact 记录 `pr=10 / cleanup=deleted`；[原机器人评论](https://github.com/pysugar/model-observatory/pull/10#issuecomment-6254053994)已更新为清理完成，原稳定/固定链接均失效 |
| 页面验收 | 27 项测试通过；预览和正式站的桌面、390/320px 无横向溢出，页脚 commit 链接正确，无 JS 错误；禁用 JS 仍能查看版本。CI 的 `checks-<build>-1` artifact 保存页脚截图 |

本节记录已完成的验收，不自动追随每次文档发布。最新线上版本以 [生产 version.json](https://models.localgpt.net/version.json) 和对应 [正式发布 run](https://github.com/pysugar/model-observatory/actions/workflows/deploy.yml)为准。GitHub site/checks artifact 保留 14 天，preview-record 保留 90 天；过期后应结合 Git 提交、PR 评论与 run 日志核对，不能把临时预览 URL 当永久归档。

## 2026-10-20 PR14 功能与正式发布收束

[PR #14](https://github.com/pysugar/model-observatory/pull/14) 已于 **2026-10-20T09:03:44Z** 合并。以下是协调线程已完成并提供的验收记录；本次文档收束未重新执行部署，也不授予后续 PR 合并或生产变更权限。

| 阶段 | 已完成事实 |
| --- | --- |
| 最终源码与合并 | PR 最终 head `121a4edf314441c44aa8790dfb1af5be413c764f`；main merge `5eab3d03a4abf61cdaa500669cd5d712e48d8428` |
| 最后预览（历史） | [CI 39393905185](https://github.com/pysugar/model-observatory/actions/runs/39393905185) 与 [preview deploy 39394160732](https://github.com/pysugar/model-observatory/actions/runs/39394160732) 成功；它们是 PR 预览证据，不是正式生产发布 |
| main CI 与正式发布 | [run 39397926762](https://github.com/pysugar/model-observatory/actions/runs/39397926762) 成功：39 项单元测试、干净构建、生产/预览 Wrangler dry-run、完整浏览器 smoke（1440/390/320、键盘及真实触屏） |
| 正式版本 | [models.localgpt.net](https://models.localgpt.net) 与 [独立正式验收入口](https://model-observatory.openai-proxy-local.workers.dev) 的 source/build 均为 `5eab3d03a4abf61cdaa500669cd5d712e48d8428`，Environment=`release`、branch=`main`、clean；两个入口的资产哈希分别核验通过 |
| Cloudflare 版本 | `123f7a8e-c2c1-4f7a-9a4f-dd9d6e934ca8` |
| 线上交互验收 | OSWorld 模型固定高亮、真实分数下降、七模型任务建议矩阵、三张可展开来源/边界的经验卡均已浏览器核验 |

上线功能包括 AA 智能指数七项面板与排名/缺测一致性、固定与临时强调分离的已测档位曲线、官方/社区/经验分层建议、Arena 方法说明、分协议 Computer Use 与限定范围的观测替代组合。三张多源经验卡已补齐；待验证提醒没有卡片是有意的空状态。当前功能和后续入口集中在 [README](README.md#当前功能决策与不可回归边界)，不从旧 PR 中“待合并”或旧验收记录中的 pending 推断当前状态。

本轮分阶段本地证据保留于：

- [能力完整性与恢复](verification/capability-effort-2026-10-20/validation.json)、[空来源/嵌套按钮恢复](verification/capability-effort-2026-10-20/recovery/validation.json)。
- [术语、评测说明与任务矩阵](verification/selection-guidance-2026-10-20/validation.json)。
- [曲线、Computer Use 与观测替代](verification/computer-use-scaling-2026-10-20/validation.json)。
- [三张经验卡](verification/experience-cards-2026-10-20/validation.json)。

这些文件与相邻截图对应各自的源码阶段；其中较早的“待卡片文案”等状态保留为历史，不代表最终 PR head 的缺项。最新线上版本仍须将 `version.json` 的 source/build、分支、clean 和资产哈希与具体成功 run 对齐，不能仅凭页面打开或短 SHA。

## 常规回滚

对有问题的源码提交开 `git revert` PR，经原 CI 和人工审阅后合并 main，由现有流程发布。回退后的 source commit 是新的 revert 提交，资产内容可以恢复到已知版本。旧 run 会被 main 过期检查拦截，不通过重跑旧发布绕过历史。

## 紧急恢复

仅在用户明确授权具体 Worker 和目标 Cloudflare 版本后执行平台版本回滚。先记录当前 Git SHA、线上版本和平台版本；在 Cloudflare 恢复选定的已知版本后，立即核验两条正式入口及内容哈希，再通过 revert/修复 PR 使 Git main 与线上内容对齐。工作流损坏时先修复可信发布链路；不要把平台回滚视为永久绕开 Git。

如果恢复发生在正常 main 发布仍可能运行时，先由用户批准暂停相关发布开关，避免旧的排队任务覆盖恢复结果；修复对齐后再恢复。此次没有执行回滚、修改正式开关或改变 DNS。

## 2026-10-20 PR16 界面与选档功能正式发布收束

[PR #16](https://github.com/pysugar/model-observatory/pull/16) 已于 **2026-10-20T12:39:09Z** 合并。本轮只改展示与交互，研究数据不变（169 条记录、24 款模型、41 条来源，预览评论中的行数与来源数均未变化）。

| 阶段 | 已完成事实 |
| --- | --- |
| 最终源码与合并 | PR 最终 head `a5cf105da2820aa9092beecfff9c0cc376e4edc6`；main merge `1ed2900a756c1833611e5fb89d6f242399827f8d` |
| PR 验证与预览（历史） | 最终 head 的 [CI 39423649779](https://github.com/pysugar/model-observatory/actions/runs/39423649779) 成功；各提交均有原生预览；它们是 PR 预览证据，不是生产发布 |
| main CI 与正式发布 | [run 39423917650](https://github.com/pysugar/model-observatory/actions/runs/39423917650) 成功：43 项单元测试、干净构建、生产/预览 Wrangler dry-run、完整浏览器 smoke（系统 Chrome、sandbox 开启，含选档矩阵与 Python 参考逐格一致、中位数象限、系列聚焦与本页目录） |
| 正式版本 | 部署后 `publish.py probe` 对 [models.localgpt.net](https://models.localgpt.net) 与 [独立正式验收入口](https://model-observatory.openai-proxy-local.workers.dev) 均为 PASS，commit `1ed2900a756c1833611e5fb89d6f242399827f8d` |
| Cloudflare 版本 | `6fa1312f-5d04-44db-89be-48dc1ee6ae21`（本次上传 `index.html`、`version.json` 两个变化资产） |

上线功能：选档速查矩阵（边际收益拐点规则，省钱 / 均衡 / 性能优先三档门槛）、官方 / 经验起点与社区实测并排参考、各档位避坑清单、吸顶本页目录、按数据中位数或个人预算划分的 Most attractive quadrant、点击聚焦 / 悬停预览、档位曲线自适应纵轴、语义颜色变量与深色模式、长口径说明折叠。功能决策与不可回归边界见 [README](README.md#当前功能决策与不可回归边界)，本地验收记录见 [ui-refresh 记录](verification/ui-refresh-2026-10-20/validation.json)。

本轮在云端容器内开发：该环境以 root 运行，本地浏览器检查未开 Chromium sandbox，仅用于迭代；sandbox 开启的验收以上述 CI 为准。容器网络策略不允许直接访问正式域名，线上核验采用发布工作流内的 probe 结果。

## 2026-10-24 PR19 模型档案正式发布收束

[PR #19](https://github.com/pysugar/model-observatory/pull/19) 已于 **2026-10-24T21:08:51Z** 合并。新增“模型档案”页签；逐档分数与成本沿用冻结输入，主表仍为 169 条记录、24 款模型、50 条来源（预览评论中的行数与来源数均未变化）。

| 阶段 | 已完成事实 |
| --- | --- |
| 最终源码与合并 | PR 最终 head `5ff1308577067dbcb41e4551bae8e4a703db35c1`；main merge `f8e36ec7e18c97a5f799afe167355ea3a7c699ae` |
| PR 验证与预览（历史） | 最终 head 的 [CI 40132434290](https://github.com/pysugar/model-observatory/actions/runs/40132434290) 成功；原生预览已部署（Cloudflare deployment `6936e361-b42b-410d-824f-d5286d14cec0`）。它们是 PR 预览证据，不是生产发布 |
| main CI 与正式发布 | [run 40132928451](https://github.com/pysugar/model-observatory/actions/runs/40132928451) 成功：53 项单元测试、干净构建、完整浏览器 smoke（含模型档案 24 款 × 三档门槛与 Python 参考逐行一致、七个页签无溢出） |
| 正式版本 | 部署后 `publish.py probe` 对 [models.localgpt.net](https://models.localgpt.net) 与 [独立正式验收入口](https://model-observatory.openai-proxy-local.workers.dev) 均为 PASS，commit `f8e36ec7e18c97a5f799afe167355ea3a7c699ae`；用户另行打开 `#profiles?m=claude-opus-5-5` 确认页面可用 |
| Cloudflare 版本 | `967d0305-bfb6-41a0-8812-c348bffb1d4e`（本次上传 `index.html`、`report-data.json`、`version.json` 三个变化资产） |

上线功能：模型档案页签（`#profiles`，深链 `#profiles?m=<目录 id>`），覆盖目录 24 款四家活跃型号；9 类任务 × 原生档位表（分数、成本、成本每翻倍得分、实测拐点 / 起步档 / 最高分）；分任务选档卡（起步档、实测拐点、降档候选、升档上限、相关证据）；选档速查与档位建议详情跳转。功能决策见 [README](README.md#当前功能决策与不可回归边界)，研究说明见 [2026-10-24 研究记录](research/2026-10-24/README.md)，本地验收见 [模型档案验收记录](verification/model-profile-2026-10-24/README.md)。

本轮在云端容器内开发：容器以 root 运行，本地浏览器检查未开 Chromium sandbox，仅用于迭代；sandbox 开启的验收以上述 CI 为准。容器网络只放行搜索，14 条补充证据为检索摘要（原页待复核），线上核验采用发布工作流内的 probe 结果与用户本人打开页面的确认。PR #18 的正式发布也已由 run 39987003757 完成双入口验收（该 run 的 Cloudflare 版本 ID 本文未记录，以其上传日志为准）。

## 2026-10-24 PR21 模型档案甜蜜点、更优替代与避坑指南正式发布收束

[PR #21](https://github.com/pysugar/model-observatory/pull/21) 已于 **2026-10-24T21:57:52Z** 合并。只改模型档案的展示与计算规则，研究数据不变（169 条记录、24 款模型、50 条来源，预览评论中的行数与来源数均未变化）；`model-effort-profiles.json` 仅新增产品线字段 `line`。

| 阶段 | 已完成事实 |
| --- | --- |
| 最终源码与合并 | PR 最终 head `844be63948950187125b0575b170ff9f1df50463`；main merge `8040c1f58e2ba09e33d23703a7b0b296eb081241` |
| PR 验证与预览（历史） | 最终 head 的 [CI 40136281156](https://github.com/pysugar/model-observatory/actions/runs/40136281156) 成功；各提交均有原生预览，它们是 PR 预览证据，不是生产发布 |
| main CI 与正式发布 | [run 40136499170](https://github.com/pysugar/model-observatory/actions/runs/40136499170) 成功：56 项单元测试、干净构建、完整浏览器 smoke（含模型档案甜蜜点、避坑列表与每档更优替代在两种范围下与 Python 参考逐项一致） |
| 正式版本 | 部署后 `publish.py probe` 对 [models.localgpt.net](https://models.localgpt.net) 与 [独立正式验收入口](https://model-observatory.openai-proxy-local.workers.dev) 均为 PASS，commit `8040c1f58e2ba09e33d23703a7b0b296eb081241`；用户另行确认线上页面可用 |
| Cloudflare 版本 | `7d6bbe03-c9fa-41ec-ba1e-f32762d27aa9`（本次上传 `index.html`、`report-data.json`、`version.json` 三个变化资产） |

上线功能：模型档案统一称“甜蜜点”（边际收益拐点）并附三档门槛（省钱 20% / 均衡 12% / 性能优先 6% × 评测分差）的逐步演示；“更优替代”按任意一档逐评测给出同分最省 / 同价最高替代（同厂商或四家全部）；可选避坑指南（费用刺客、档位倒退、新一代更省、被同家全面超越）；每类任务的评测行对所有模型固定并标单位。规则见 [README](README.md#当前功能决策与不可回归边界)，本地验收见 [模型档案避坑验收记录](verification/model-profile-pitfalls-2026-10-24/README.md)。PR #20 只改文档（发布 run 40133573211），不单列版本。

本轮仍在云端容器内开发：本地浏览器检查未开 Chromium sandbox，仅用于迭代；sandbox 开启的验收以上述 CI 为准，线上核验采用发布工作流内的 probe 结果与用户本人确认。

## 2026-10-25 PR23 / PR24 模型档案文案、不限预算推荐与主流档位正式发布收束

两次发布都只改模型档案的展示、计算规则与参考文字，研究数据不变（169 条记录、24 款模型、50 条来源，预览评论中的行数与来源数均未变化）。

| 阶段 | PR #23（仅文案） | PR #24 |
| --- | --- | --- |
| 合并 | 2026-10-25T04:18:47Z；PR 最终 head `cd4f7c5c8ba18939a93392ad5c0d9d4960e1d344`；main merge `3c4080fd844c4d401b70b2449682a7310c09b7d7` | 2026-10-25T04:55:53Z；PR 最终 head `c8388bf2ea2200b406550ad2cde0761267abf7c7`；main merge `288defa3ffc7029e20c2a98a52e1ccf95a2a7e22` |
| PR 验证与预览（历史） | 最终 head 的 [CI 40161172094](https://github.com/pysugar/model-observatory/actions/runs/40161172094) 成功，原生预览已部署 | 最终 head 的 [CI 40163409349](https://github.com/pysugar/model-observatory/actions/runs/40163409349) 成功，原生预览已部署 |
| main CI 与正式发布 | [run 40161424122](https://github.com/pysugar/model-observatory/actions/runs/40161424122) 成功（56 项单元测试、完整浏览器 smoke） | [run 40163673486](https://github.com/pysugar/model-observatory/actions/runs/40163673486) 成功（62 项单元测试、完整浏览器 smoke，含三种替代、过度思考避坑与工作阶段档位换算） |
| 正式版本 | 双入口 `publish.py probe` 均为 PASS，commit `3c4080fd844c4d401b70b2449682a7310c09b7d7` | 双入口 `publish.py probe` 均为 PASS，commit `288defa3ffc7029e20c2a98a52e1ccf95a2a7e22`；用户另行确认线上页面可用 |
| Cloudflare 版本 | `628fb809-d0fd-47c1-8269-f75fa4bb760c`（上传 `index.html`、`version.json`） | `7b80cf72-4a74-4302-8c78-d94ba52d03fb`（上传 `index.html`、`report-data.json`、`version.json`） |

上线功能：PR #23 把“同价最高”改为“同预算最强”并在表头说明两种替代的含义，去掉页面上的改版过程说明。PR #24 把第三种替代定为“不限预算推荐”（与最高分相差不到分差 3% 的视为打平，取最快的；无耗时数据时取最便宜）；避坑新增“过度思考”；新增“不差钱时什么情况不该用最高档”九类场景与当前模型的实测信号；新增“按工作阶段的主流档位”（综合整理，按模型原生档位换算）；新增 GPT-6 Astra / GPT-6.1 Sol 的社区主流声音。社区与工作阶段内容只作文字参考、不参与计算，来源见 [2026-10-25 研究记录](research/2026-10-25/README.md)；规则见 [README](README.md#当前功能决策与不可回归边界)。PR #22 只改文档（发布 run 40160478249），不单列版本。

本轮仍在云端容器内开发：本地浏览器检查未开 Chromium sandbox，仅用于迭代；sandbox 开启的验收以上述 CI 为准，线上核验采用发布工作流内的 probe 结果与用户本人确认。

## 2026-10-25 PR25 社区主流声音覆盖全部主力型号正式发布收束

[PR #25](https://github.com/pysugar/model-observatory/pull/25) 已于 **2026-10-25T06:20:05Z** 合并。只新增社区主流声音条目与文档，研究数据不变（169 条记录、24 款模型、50 条来源，预览评论中的行数与来源数均未变化）。

| 阶段 | 已完成事实 |
| --- | --- |
| 最终源码与合并 | PR 最终 head `000b301c1bed668e21944951e7caeeb1038d9c94`；main merge `8d5ab9af93773d2d3e3701925b181611ea7f2638` |
| PR 验证与预览（历史） | 最终 head 的 [CI 40165550752](https://github.com/pysugar/model-observatory/actions/runs/40165550752) 成功，原生预览已部署 |
| main CI 与正式发布 | [run 40168720237](https://github.com/pysugar/model-observatory/actions/runs/40168720237) 成功：63 项单元测试、完整浏览器 smoke（含每款主力型号都显示社区声音） |
| 正式版本 | 双入口 `publish.py probe` 均为 PASS，commit `8d5ab9af93773d2d3e3701925b181611ea7f2638`；用户另行确认线上页面可用 |
| Cloudflare 版本 | `e1a35191-bc8e-4dde-b1bf-8e872e4e6027`（上传 `index.html`、`report-data.json`、`version.json`） |

上线内容：社区主流声音从 GPT-6 Astra / GPT-6.1 Sol 扩展到四家全部 11 款当前主力型号（共 15 条，见 [2026-10-25 研究记录](research/2026-10-25/README.md)），每条标出来源一致性与证据强弱，只作文字参考、不参与计算；测试要求每款主力至少一条。本次合并同时带入了 PR23 / PR24 的发布收束记录（提交 `5813914`）。上一代与兼容旧版型号暂未覆盖，社区条目原页仍待逐条核对。

本轮仍在云端容器内开发：本地浏览器检查未开 Chromium sandbox，仅用于迭代；sandbox 开启的验收以上述 CI 为准，线上核验采用发布工作流内的 probe 结果与用户本人确认。

## 2026-10-28 PR28 AA 智能指数 v5 正式发布收束

[PR #28](https://github.com/pysugar/model-observatory/pull/28) 已于 **2026-10-28T07:31Z** 合并。新增 AA v5 冻结输入与榜单页签；169 条记录、24 款模型、50 条来源不变，原 AA v4.3.2 选录、逐档曲线、甜蜜点与模型档案不变。

| 阶段 | 已完成事实 |
| --- | --- |
| 最终源码与合并 | PR 最终 head `6756df555f18d7195d0a2a980c261bf355a82166`；main merge `9ac686c2ba8057c1fa1d993ebb915b5054f04dd0` |
| PR 验证（历史） | 首次 [CI 40649763288](https://github.com/pysugar/model-observatory/actions/runs/40649763288) 失败：新增 smoke 断言用 Playwright `is_disabled()` 判断 `<option>`，恒为 false；`6756df5` 改读 `option.disabled` 后 [CI 40650247992](https://github.com/pysugar/model-observatory/actions/runs/40650247992) 成功 |
| main CI 与正式发布 | [run 40650595388](https://github.com/pysugar/model-observatory/actions/runs/40650595388) 成功：63 项单元测试、干净构建、完整浏览器 smoke（含 AA v5 页签、方法说明与成本排序禁用） |
| 正式版本 | `publish.py check` PASS（commit `9ac686c`、clean、169 行 / 24 模型 / 50 来源）；双入口 `publish.py probe` 均为 PASS：[models.localgpt.net](https://models.localgpt.net) 与 [独立正式验收入口](https://model-observatory.openai-proxy-local.workers.dev) |
| Cloudflare 版本 | `8262ec6c-e613-418d-9bf9-5f1100f9ee82`（上传 `index.html`、`report-data.json`、`version.json`） |

上线内容：“最新榜单”新增 **AA v5 新口径** 页签，12 个配置，每行显示“较 v4.3.2”变化并标出多源一致（8）/ 单一来源（4）；页签下可展开 v5 分类权重、移除评测与阅读提示；首页“综合基准”信号指向 v5。数据来自 10-28 网页检索摘要，见 [2026-10-28 研究记录](research/2026-10-28/README.md)。v5 费用、速度与子评测缺失，单一来源行待原页复核。

本轮在云端容器内开发：本地只跑了单元测试和 Node Playwright 定向检查（容器无 Python Playwright）；完整 smoke 以上述 CI 为准，线上核验采用发布工作流内的 probe 结果。

## 2026-10-28 PR30 AA v5 榜单原页数据与默认页签正式发布收束

[PR #30](https://github.com/pysugar/model-observatory/pull/30) 已于 **2026-10-28T08:40Z** 合并。网络放行 artificialanalysis.ai 后，v5 榜单改由 `research/2026-10-28/fetch_aa_v5.py` 从 AA 公开榜单页重建；169 条记录、24 款模型、50 条来源不变。

| 阶段 | 已完成事实 |
| --- | --- |
| 最终源码与合并 | PR 最终 head `b0ea27ce2a25d25e587216b44da7d041e97cde80`；main merge `c6ab1d6b6463aa49073b8aba1cc99a87633272db` |
| PR 验证与预览（历史） | 最终 head 的 [CI 40658081295](https://github.com/pysugar/model-observatory/actions/runs/40658081295) 成功，原生预览已部署 |
| main CI 与正式发布 | [run 40658487724](https://github.com/pysugar/model-observatory/actions/runs/40658487724) 成功：63 项单元测试、完整浏览器 smoke（含默认 v5 页签与第 2 行为 GPT-6 Astra） |
| 正式版本 | 双入口 `publish.py probe` 均为 PASS，commit `c6ab1d6b6463aa49073b8aba1cc99a87633272db` |
| Cloudflare 版本 | `3ced2e6a-b75a-4963-8ed1-e5a01cda34b4`（上传 `index.html`、`report-data.json`、`version.json`） |

上线内容：v5 页签 26 个配置含总分、加权单任务成本、输出速度与九项子评测，PR #28 中来自检索摘要的 12 个分数全部经原页核实；新增 GPT-6.1 Terra 与开放权重标记；“最新榜单”默认打开 v5（GPT-6 Astra 排第 2），旧页签改名“AA v4.3.2（旧）”；能力指数图标明 v4.3.2。整站迁移到 v5 另见后续 PR。

## 2026-10-28 PR31 整站迁移到 AA 智能指数 v5 正式发布收束

[PR #31](https://github.com/pysugar/model-observatory/pull/31) 已于 **2026-10-28T14:24Z** 合并。全站改为页首“AA 指数版本”切换，默认 v5，可切回 v4.3.2；169 条记录、24 款模型、50 条来源不变。

| 阶段 | 已完成事实 |
| --- | --- |
| 最终源码与合并 | PR 最终 head `cc718feb9abe1c98179b25781051674810f721f7`；main merge `dbf234c49ac1521986bcb86e227e697f1fe3b209` |
| PR 验证与预览（历史） | 最终 head 的 [CI 40662623608](https://github.com/pysugar/model-observatory/actions/runs/40662623608) 成功，[原生预览 40663026112](https://github.com/pysugar/model-observatory/actions/runs/40663026112) 已部署 |
| 合并前独立复核 | 重跑 `fetch_aa_v5_releases.py` 与 `fetch_aa_v5.py`：30 个发布版本页与 2 个榜单页的 SHA-256 及全部数值与提交一致，仅 `fetched_at` 不同；分支重建产物逐字节一致；预览站 v5 默认视图与 `?aa=v4` 视图文案互斥、无控制台错误、无横向溢出 |
| main CI 与正式发布 | [run 40705606470](https://github.com/pysugar/model-observatory/actions/runs/40705606470) 成功：70 项单元测试、干净构建、完整浏览器 smoke（含 `scripts/v5_smoke.py` 与 `?aa=v4` 原有逐格断言） |
| 正式版本 | `publish.py check` PASS（commit `dbf234c`、clean、169 行 / 24 模型 / 50 来源）；双入口 `publish.py probe` 均为 PASS：[models.localgpt.net](https://models.localgpt.net) 与 [独立正式验收入口](https://model-observatory.openai-proxy-local.workers.dev)；发布后本机读取两入口 `version.json`，`source_commit` 均为 `dbf234c` |
| Cloudflare 版本 | `0f0b30dd-8b77-4e97-9e7f-11f1a1ab5e2b`（上传 `index.html`、`report-data.json`、`version.json`） |

上线内容：v5 数据由 `research/2026-10-28/fetch_aa_v5_releases.py` 从 AA 发布版本页读取（16 个发布版本、49 个档位，四大家族 11 款活跃模型 44 个档位的 9 项 v5 评测，6 大领域指数按 v5 构成）；AA 未用 v5 重测的旧型号在 v5 视图显示未测，不用 v4.3.2 填补。v5 任务视图改用新评测（长程代理改为 Terminal-Bench-Science），“均衡”门槛下 77 格甜蜜点有 21 格变化。仍为 v4.3.2 并已标明：最新榜单“较 v4.3.2”列、五站全景表、成本页 169 条历史记录、21 个代表配置的速度矩阵。Gemini 3.8 Flash low 无 v5 费用，甜蜜点计算自动排除。
