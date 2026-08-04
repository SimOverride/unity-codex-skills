# Unity Codex Skills

面向 Unity 游戏开发与 Blender 游戏资产制作的个人 Codex Skill 仓库。

## 包含的 Skill

| Skill | 职责 |
|---|---|
| `unity-feature-module-planning` | 在实现前澄清 Unity 功能模块的边界、数据所有权、状态、依赖、事件和 MVP |
| `unity-module-delivery` | 将基本明确的 Unity 模块需求落地为代码、配置、文档和可验证交付 |
| `blender-unity-asset-pipeline` | 制作并验收可直接导入 Unity 的静态、可调与动画 Blender 资产 |
| `unity-render-debug` | 系统诊断 Unity Shader、阴影、描边、透明、法线和模型导入问题 |

## 职责关系

```text
需求尚未明确
    ↓
unity-feature-module-planning
    ↓ 形成可实施模块计划
unity-module-delivery
    ↓
代码、资源配置、文档与验证

Blender 资产任务 ──→ blender-unity-asset-pipeline
专项渲染问题 ─────→ unity-render-debug
```

## 安装

把需要的 Skill 文件夹复制到 Codex 个人 Skill 目录：

```powershell
$targetRoot = if ($env:CODEX_HOME) {
    Join-Path $env:CODEX_HOME 'skills'
}
else {
    Join-Path $HOME '.codex\skills'
}

Copy-Item -LiteralPath '.\skills\unity-feature-module-planning' -Destination $targetRoot -Recurse
Copy-Item -LiteralPath '.\skills\unity-module-delivery' -Destination $targetRoot -Recurse
Copy-Item -LiteralPath '.\skills\blender-unity-asset-pipeline' -Destination $targetRoot -Recurse
Copy-Item -LiteralPath '.\skills\unity-render-debug' -Destination $targetRoot -Recurse
```

更新已安装 Skill 前，先确认目标目录中的同名文件是否包含尚未同步回仓库的个人改动。

## 使用

可以显式调用：

```text
使用 $unity-feature-module-planning 规划这个 Unity 功能模块。
使用 $unity-module-delivery 实现已经确认的模块方案。
使用 $blender-unity-asset-pipeline 制作并验收这个 Unity 模型。
使用 $unity-render-debug 分析这个描边和阴影问题。
```

Skill 的 `description` 也支持根据自然语言请求自动触发。

## 维护

- 项目总体说明：[docs/项目总体文档.md](docs/项目总体文档.md)
- 月度复盘与 Skill 维护流程：[docs/月度复盘与Skill维护流程.md](docs/月度复盘与Skill维护流程.md)
- 定时任务提示词：[docs/定时任务提示词.md](docs/定时任务提示词.md)
- 版本变化：[docs/CHANGELOG.md](docs/CHANGELOG.md)

## 验证

修改 Skill 后至少运行：

```powershell
python -X utf8 <skill-creator目录>\scripts\quick_validate.py .\skills\<skill-name>
```

若 Skill 包含脚本，还必须实际运行代表性成功与失败场景。脚本测试通过不等于真实项目前向测试通过。
