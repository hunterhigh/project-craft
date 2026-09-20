# Project Craft · 项目共创

面向人与 AI 共同开展项目的一组独立技能：澄清方向、设计系统、建立工程基础，并持续承接讨论与执行。适用于完整项目，也适用于有明确协作边界的局部工作。

## 系列成员

| 技能 | 负责的工作 | 何时使用 |
| --- | --- | --- |
| [project-framing](skills/project-framing/SKILL.md) | 项目构思与定位 | 想法、需求或方向尚不清楚，需要明确目标、范围、备选路径和下一步。 |
| [system-architecture](skills/system-architecture/SKILL.md) | 系统架构 | 需要设计或调整职责、依赖、信息与运行方式，并考虑人的协作、现实边界和实验反馈。 |
| [project-foundation](skills/project-foundation/SKILL.md) | 工程起步 | 要在空目录中为长期软件项目建立可验证的工程基础，或检查该技能建立的基础。 |
| [project-continuity](skills/project-continuity/SKILL.md) | 项目持续协作 | 在讨论、执行、插入事项、交接和恢复之间保持目标、边界与必要记录。 |

这些技能按需要组合使用，没有必须依次通过的四道关卡。已有交接、项目认识和记录可直接复用。系统架构也可以用于已经开始实施的 MVP、实验项目或大系统中的局部组件。

每个技能保留自己的使用边界。例如，project-foundation 的开工契约适用于它的项目生成流程，不扩展为其他技能的通用前置审批。

## 安装与调用

克隆本仓库后，将需要的 `skills/<技能名>/` **完整目录**复制到个人 Skills 目录（通常是 `~/.codex/skills/`），或目标环境支持的项目技能目录。已有同名技能时，先比较版本和本地修改，再决定是否替换。

四个技能可分别安装。project-foundation 的 `references/`、`scripts/`、`assets/`、`VERSION` 等文件需要一并保留。其余技能所提及的专业技能按实际工作需要使用，不必为了安装本系列收集全部相关技能。

调用示例：

- `使用 $project-framing，帮我把这个想法梳理到可以开始验证。`
- `使用 $system-architecture，根据交接与合作边界，判断这一部分应该怎样设计。`
- `使用 $project-foundation，为这个长期项目准备工程基础。`
- `使用 $project-continuity，承接已有记录，继续讨论和推进这个项目。`

仓库中的文件用于系列版本维护；复制到运行环境中的安装副本不会随 Git 提交自动同步。

## 来源与版本

- project-framing、system-architecture、project-continuity：2026-09-20 从当前本地技能正文与调用配置收录。
- project-foundation：完整收录自 [hunterhigh/project-foundation](https://github.com/hunterhigh/project-foundation)，版本 **0.2.0**，来源提交 [`ea02de1`](https://github.com/hunterhigh/project-foundation/commit/ea02de16b368c17dae5de755a81b00ee486bd93a)。保留原有变更记录、设计文档、模板和测试；原仓库历史仍可追溯。

本系列不包含 project-commercial-advisor；该技能属于如文系统。

## 验证

在仓库根目录运行 project-foundation 的现有测试：

```text
python -m unittest discover -s skills/project-foundation/tests -v
```

测试覆盖生成、校验、版本模板及适配器；TypeScript 适配器测试需要 npm。运行检查时应查看测试结果中的跳过项。测试通过不代表其他原则型技能已经完成真实项目行为验证。

技能内容调整时，核对入口、内部引用、协作边界和典型使用场景；只针对相关变化运行必要检查。
