# 开发上下文

- 先阅读 `README.md`；若根目录存在 `LOCAL_CONTEXT.md`，一并读取当前机器的开发约定。该本地文件由 Git 忽略，每台机器独立维护。
- 通用文档和代码使用仓库相对路径；不要把本机 checkout、解释器、主机或账号别名写成所有开发环境的统一要求。
- 保留当前 checkout 的 `origin` 与账号路由。文档中的标准仓库地址不构成改写本机 remote 的授权；外部写入前分别核实 Git SSH 与 API 身份。
- 使用当前机器配置的 Python 环境；本地环境约定放在 `LOCAL_CONTEXT.md`，跨机器验证入口见 `DEPLOYMENT.md`。
- 工程入口和功能决策维护在 `README.md`，研究流程维护在 `RESEARCH_WORKFLOW.md`，已验证的发布事实维护在 `RELEASES.md`。
