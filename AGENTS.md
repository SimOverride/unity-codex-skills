# 仓库约束

## 内容范围

- 仓库只维护可跨项目复用的 Unity 与 Blender Codex Skill。
- 项目专属玩法规则、场景结构和资源路径不得写入通用 Skill。
- Unity 项目专属约束应写入对应项目的 `AGENTS.md`。

## Skill 结构

- 每个 Skill 位于 `skills/<skill-name>`。
- `SKILL.md` frontmatter 只包含 `name` 和 `description`。
- `SKILL.md` 保持精简，详细检查表放入一级 `references`。
- 确定性、重复且容易出错的操作放入 `scripts`。
- 不在 Skill 目录中增加 README、CHANGELOG 或安装说明。
- `agents/openai.yaml` 的默认提示必须显式包含 `$skill-name`。

## 文档

- 仓库文档统一放在 `docs`，根 README 与本约束文件除外。
- 文档与注释使用中文。
- 文档只描述当前有效流程，不保留方案演变过程。
- 有影响的版本变化记录在 `docs/CHANGELOG.md`。

## 修改与验证

- 修改现有 Skill 时直接删除失效规则，不保留多余兼容逻辑。
- 新建或更新 Skill 必须使用 `skill-creator`。
- 修改后运行 `quick_validate.py`。
- 新增或修改脚本必须实际运行成功场景；存在失败分支时同时验证失败场景。
- 复杂 Skill 应使用不泄漏预期答案的真实案例做前向测试。
- 代码脚本使用 CRLF 行尾。

## 月度复盘

- 自动月度任务默认只生成报告，不直接修改 Skill。
- 只有至少两个不同真实任务暴露同一可复用缺陷时，才建议更新 Skill。
- 新工作流必须在不同任务中重复出现，且输入、步骤、输出与验收相对稳定，才建议创建 Skill。
- 项目约束、一次性知识和单一数据源批处理不应直接封装为通用 Skill。
