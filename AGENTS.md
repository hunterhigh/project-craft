# Project Craft 协作约定

- 本仓库维护 project-framing、system-architecture、project-foundation、project-continuity、goal-discipline 五个独立技能；project-commercial-advisor 属于如文系统，不在本仓库范围内。
- 每个 `skills/<name>/` 保持可独立安装，运行所需文件放在该目录内，不依赖本仓库以外的源码或个人绝对路径。
- 系列成员按需要组合，不建立强制执行顺序，不把某个技能的专用流程扩展成全系列要求。
- 延续用户确认的工作情境、人的因素、责任边界、轻量架构与实验迭代原则；保留各技能具体适用范围。
- 仓库副本与个人安装副本不自动同步。修改其他仓库或安装副本须属于当前用户授权范围。
- 修改 project-foundation 的生成器或模板后，在根目录运行 `python -m unittest discover -s skills/project-foundation/tests -v`；纯文档修改采用相关性检查。
