# Project Foundation 自动语义版本与生产晋升设计

日期：2026-09-03

状态：已实施；待推送工作流并配置 `VERSION_BOT_TOKEN`
目标版本：`0.2.0`

## 1. 设计目标

Project Foundation 应把版本管理从“存在 SemVer、Changelog、tag 和 Release”提升为一项可验证的交付能力：由更新内容确定下一版本，先验证候选版本，再以同一 commit 进入生产，并禁止无新版本的生产部署。

这一能力属于现有四阶段结构中的“交付”，不增加新的顶层阶段：

1. **理解**项目是否会产生可部署或可分发版本。
2. **决策**选择 `versioning` 与 `release` 模块及适合技术栈的自动化程度。
3. **生成**版本规则、工具、CI/发布门禁和人类可读流程。
4. **验证**机械证明版本计算、文件一致性和生产门禁存在且可执行。

## 2. 适用范围与渐进保障

### 2.1 通用 versioning 模块

所有长期项目继续拥有唯一版本事实来源和 `CHANGELOG.md`。更新日志采用以下影响分类：

- `重大迭代` / `不兼容变更` / `Breaking`：major。
- `新增` / `Added`：minor。
- `修复` / `维护` / `优化` / `安全与运维` / `Fixed` / `Maintenance` / `Security`：patch。
- 混合更新取最高影响级别；major 必须显式声明。

文档、仓库维护或不进入运行产物的变更可以声明为不需要产品版本；代码、配置、依赖和数据库变化必须进入 `Unreleased`。

### 2.2 条件 release 模块

可部署或可分发项目启用 `release`。进入 production 或 critical 阶段时，模块必须要求：

- 版本准备发生在非生产验证之前。
- production 只晋升已验证的同一 commit/build。
- 候选版本严格高于最新正式版本且 tag 不存在。
- 成功生产发布必须固化 tag 和 Release。
- 部署失败不创建正式 tag；代码回退和数据恢复继续分离。

### 2.3 自动化能力声明

Foundation 只对受支持并实际验证过的适配器声明“自动版本晋升已启用”：

- TypeScript/Node 使用 Node 版本工具和 GitHub Actions。
- Python 使用 Python 版本工具和 GitHub Actions。
- Codex Skill 使用 Python 版本工具维护 `VERSION`、`CHANGELOG.md` 和 Git tag；没有可用运行时或 GitHub 模块时保持为可执行文档流程。
- `docs-only` 或其他不受支持适配器只生成规则与待办，验证状态不得声称自动化已经生效。

## 3. 生成产物

启用 `versioning` 时，生成物至少包括：

- 单一版本事实来源；
- 包含 `Unreleased` 分类说明的 `CHANGELOG.md`；
- 与适配器匹配的版本计算与一致性检查入口；
- Agent 规则：生产相关变化必须更新 Changelog，major 必须显式声明；
- 版本工具的自动测试。

同时启用 `github` 与 `release` 时，再生成：

- CI 中的更新日志与版本一致性检查；
- main 检查成功后准备候选版本的工作流；
- 防止机器人提交再次晋升的循环保护；
- production 门禁模板或平台无关的明确集成契约；
- 最小 GitHub contents 写权限说明和受保护分支的 release PR 回退方案。

`docs/project/release-process.md` 应用业务语言解释 patch、minor、major，并明确生产不能跳过版本。

## 4. Manifest 与验证模型

现有 `versioning` 和 `release` 模块名称保持不变，避免无意义的 schema 扩张。manifest 增加的能力事实应描述：

- 版本事实文件；
- 自动化模式：`verified`、`documented` 或 `not-supported`；
- 生产是否存在；
- 是否要求 tag/Release；
- 版本准备与 staging 的先后关系。

如果这些信息可由 adapter、deployment profile、stage 和 modules 确定，则优先作为编译结果写入 verification，不增加用户必须填写的字段。只有无法推导且会改变生成结果时才扩展 schema。

验证器需要检查可观察行为，而不是只匹配文案：

- patch、minor、major 样例得到正确下一版本。
- 混合分类取最高级别。
- 未识别分类失败。
- 候选版本文件保持一致。
- 空 `Unreleased` 不重复晋升。
- production 模板拒绝相等/倒退版本和缺少验证证据的 commit。
- 自动版本提交不会形成循环。

## 5. Project Foundation 自身升级

本仓库把该能力作为向后兼容的新功能发布，因此从 `0.1.0` 晋升为 `0.2.0`：

- 更新 `VERSION`、`CHANGELOG.md` 和必要的元数据。
- 修改 `SKILL.md` 的生产阶段不变量与相关 reference 路由，不把实现细节堆进入口。
- 扩展 `references/risk-and-modules.md`、`references/output-contract.md` 和发布说明。
- 扩展编译器生成物及 deterministic verification。
- 为 Node、Python、Codex Skill 与 docs-only 场景增加行为测试。
- 运行完整单元测试、场景测试和 skill quick validation。

发布 `v0.2.0` tag 或推送远端仍属于独立的外部发布动作，不由本设计批准。

## 6. 失败与安全行为

- 无法可靠计算版本时停止，不猜测。
- 未提供显式 major 声明时不自动升级大版本。
- 自动提交冲突最多基于最新 main 重算一次，之后停止。
- 未验证的技术栈只能报告“已记录流程”，不能报告“自动化完成”。
- Foundation 生成只写入空目录；Advance 只更新由该 Skill 初始化且未被用户冲突修改的文件。
- 生成 GitHub workflow 不等于授权修改远端规则、设置 secret 或部署生产。

## 7. 验收标准

1. Foundation 自身版本为 `0.2.0`，版本事实和 Changelog 一致。
2. 三类版本及混合类别都有确定性测试。
3. 受支持适配器生成可运行的版本工具和对应测试。
4. production 场景生成“先版本、再非生产验证、后生产晋升”的门禁。
5. docs-only 场景明确标记自动化未验证。
6. 现有场景继续通过，且输出不包含真实 secret、外部写入或未经授权的部署。
7. Skill 入口保持精简，细节通过现有 references 渐进披露。
