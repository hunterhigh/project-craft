<div align="right">

[English](README.md) | **简体中文**

</div>

# Project Craft

**一组将不确定想法转化为目标清晰、结构完整且可以持续维护的项目的 Agent Skills。**

Project Craft 把五类经常混在一起的工作拆开：定义问题、设计系统、准备工程基础、保持项目连续性，以及让执行始终服务于真实目标。每个 Skill 都可以独立安装和使用。

## Skills

| Skill | 职责 | 适用场景 |
| --- | --- | --- |
| [`project-framing`](skills/project-framing/SKILL.md) | 澄清目标、形成真实可行的方向集合，并选择下一项有效行动 | 想法或需求仍然模糊时。 |
| [`system-architecture`](skills/system-architecture/SKILL.md) | 设计职责、边界、信息流、运行反馈与生命周期 | 一个系统或局部组件需要建立和演进一致结构时。 |
| [`project-foundation`](skills/project-foundation/SKILL.md) | 在长期软件开发开始前建立可验证的工程基础 | 空白或早期仓库需要形成可持续的工程约定时。 |
| [`project-continuity`](skills/project-continuity/SKILL.md) | 承接项目会议、想法发展、执行切换、复盘和恢复，维持共同工作节奏 | 已存在的项目需要与 Codex 持续讨论和推进时。 |
| [`goal-discipline`](skills/goal-discipline/SKILL.md) | 让工作专注实际任务，抑制为完整性而扩张 | 模型可能把相邻问题、流程或可见工作量误当成任务时。 |

它们不是五个必须依次通过的阶段。成熟项目可能只需要连续性；实验性组件可能需要架构设计，但不需要重新建立工程基础。这套集合按决策边界组织，而不是按仪式组织。

## 安装

使用 Skills CLI：

```bash
npx skills add hunterhigh/project-craft
```

手动安装时，将 [`skills/`](skills/) 下任意一个完整目录复制到个人或项目级 Skills 目录。请保留目录的完整结构：部分 Skill 同时包含参考资料、脚本、资产、测试或版本文件。

## 使用

```text
使用 $project-framing，把这个想法梳理成真实可行、可以验证的项目方向。
使用 $system-architecture，定义系统职责、边界、反馈和生命周期机制。
使用 $project-foundation，在编写产品代码前准备好这个仓库。
使用 $project-continuity，继续我们的项目会议，从当前问题进入讨论或工作。
使用 $goal-discipline，避免为了完整性扩张任务，并在结果完成时停止。
```

## 设计原则

- **职责分明。** 项目定位、系统架构、工程基础、持续协作和目标纪律保持独立，让每个 Skill 只承担自己真正负责的工作。
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
