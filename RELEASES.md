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

## 常规回滚

对有问题的源码提交开 `git revert` PR，经原 CI 和人工审阅后合并 main，由现有流程发布。回退后的 source commit 是新的 revert 提交，资产内容可以恢复到已知版本。旧 run 会被 main 过期检查拦截，不通过重跑旧发布绕过历史。

## 紧急恢复

仅在用户明确授权具体 Worker 和目标 Cloudflare 版本后执行平台版本回滚。先记录当前 Git SHA、线上版本和平台版本；在 Cloudflare 恢复选定的已知版本后，立即核验两条正式入口及内容哈希，再通过 revert/修复 PR 使 Git main 与线上内容对齐。工作流损坏时先修复可信发布链路；不要把平台回滚视为永久绕开 Git。

如果恢复发生在正常 main 发布仍可能运行时，先由用户批准暂停相关发布开关，避免旧的排队任务覆盖恢复结果；修复对齐后再恢复。此次没有执行回滚、修改正式开关或改变 DNS。
