<div align="right">

[English](README.md) | **简体中文**

</div>

# Project Craft

**一组将不确定想法转化为目标清晰、结构完整且可以持续维护的项目的 Agent Skills。**

Project Craft 把四类经常混在一起的工作拆开：定义问题、设计系统、准备工程基础、保持项目连续性。每个 Skill 都可以独立安装和使用。日常技术责任由工作约定承担，不依赖每轮强制调用 Skill。

## Skills

| Skill | 职责 | 适用场景 |
| --- | --- | --- |
| [`project-framing`](skills/project-framing/SKILL.md) | 澄清目标、形成真实可行的方向集合，并选择下一项有效行动 | 想法或需求仍然模糊时。 |
| [`system-architecture`](skills/system-architecture/SKILL.md) | 设计职责、边界、信息流、运行反馈与生命周期 | 一个系统或局部组件需要建立和演进一致结构时。 |
| [`project-foundation`](skills/project-foundation/SKILL.md) | 在长期软件开发开始前建立可验证的工程基础 | 空白或早期仓库需要形成可持续的工程约定时。 |
| [`project-continuity`](skills/project-continuity/SKILL.md) | 恢复有效状态、传递已确认变化、保存必要恢复点 | 已有项目需要恢复、交接，或将已确认变化传入后续工作时；普通讨论和执行不触发。 |

它们不是必须依次通过的阶段。实验性组件可能需要架构设计，但不需要重新建立工程基础；日常工作也可能完全不需要调用这些 Skill。这套集合按决策边界组织，而不是按仪式组织。

[`goal-discipline`](skills/goal-discipline/SKILL.md) 保留为历史源码，不再推荐默认安装或每轮调用。

## 安装

使用 Skills CLI：

```bash
npx skills add hunterhigh/project-craft
```

从上面的四个 Skill 中按需选择，不默认包含历史技能。手动安装时，将 [`skills/`](skills/) 下选中的完整目录复制到个人或项目级 Skills 目录。请保留目录的完整结构：部分 Skill 同时包含参考资料、脚本、资产、测试或版本文件。

## 使用

```text
使用 $project-framing，把这个想法梳理成真实可行、可以验证的项目方向。
使用 $system-architecture，定义系统职责、边界、反馈和生命周期机制。
使用 $project-foundation，在编写产品代码前准备好这个仓库。
使用 $project-continuity，从已验证状态与剩余已授权工作恢复这个项目。
```

[`AGENTS.example.md`](AGENTS.example.md) 是可选的工作约定模板，涵盖技术责任、完整交付、决策边界、纠正与按需项目承接。请审阅后将适用条款合并到已有约定，不要覆盖权限或项目规则。安装 Skill 不会自动安装此模板；模板不要求每轮命名、目标检查或新增管理文档。

## 设计原则

- **职责分明。** 项目定位、系统架构、工程基础和项目承接保持独立，让每个 Skill 只承担自己真正负责的工作；项目承接不是常驻管理层。
- **尊重现实边界。** 除技术结构外，同时考虑人员、证据、运行限制和不断变化的情境。
- **可以组合，但不强制流程。** Skills 可以协作，不会因此形成必须执行的多阶段工作流。
- **只在有用时创造产物。** 文档、计划、测试和委派必须服务于可观察结果，而不是仅仅展示过程。
- **保持可移植性。** 每个 Skill 都以自包含目录维护，入口和依赖明确。

## 仓库结构

```text
skills/
├── goal-discipline/
├── project-continuity/
├── project-foundation/
├── project-framing/
└── system-architecture/
```

## 验证

使用官方 Skill 验证器检查单个 Skill：

```bash
python /path/to/skill-creator/scripts/quick_validate.py skills/<skill-name>
```

`project-foundation` 还包含可执行测试：

```bash
python -m unittest discover -s skills/project-foundation/tests -v
```

`project-foundation` 当前版本为 `0.2.0`。其他 Skills 作为可独立安装的软件包，由本仓库统一维护。
