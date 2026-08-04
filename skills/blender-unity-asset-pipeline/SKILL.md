---
name: blender-unity-asset-pipeline
description: 制作、修改并验收可直接导入 Unity 的 Blender 游戏资产，覆盖静态道具、参数化或可调资产、骨骼动画资产、材质分区、UV、法线、轴心、拓扑预算、FBX 导出和回读验证。用于用户提供参考图或现有 .blend/FBX，要求低模建模、Unity 换色、拆分可动画部件、制作骨骼动画、优化拓扑、设置轴心、生成预览或交付 Unity FBX 的任务。不用于 Unity Shader 排障、仅在 Unity 内实现玩法代码或无需三维资产的图片生成。
---

# Blender Unity 资产管线

## 目标

交付结构、坐标、材质、拓扑和动画都符合实际 Unity 用途的资产，而不只是 Blender 中看起来正确的模型。

## 基本原则

- 修改现有场景前先检查对象、集合、单位、父子关系、共享数据、修改器、材质和动画，不猜测缺失值。
- 尊重现有命名和组织；未经确认不要破坏性重建用户已有资产。
- 优先采用可重复生成、可调整和非破坏流程；最终交付需要固定结果时再应用修改器或烘焙。
- 通过对象拆分、轴心、材质槽和骨骼结构满足 Unity 侧需求，不把结构问题留给导入后补救。
- Blender 中的视觉效果不等于 Unity 可导出的数据。Freestyle、合成器和仅渲染期效果不能当作 FBX 能力。

## 工作流

### 1. 明确资产合同

先从用户信息、参考图、现有文件和目标项目中确认：

- 用途：Unity 游戏资产、展示模型还是动画角色。
- 真实尺寸、观察方向、坐标朝向和默认姿态。
- 风格与几何精度。
- 静态、可调还是骨骼动画。
- Unity 中需要独立移动、旋转、换色或隐藏的部分。
- UV、纹理、PBR、切线空间法线、自定义法线需求。
- 碰撞体、LOD、动画列表和三角形预算。
- 导出形式：单个 FBX、多 FBX、对象拆分或骨骼蒙皮。

只询问会改变结构或交付结果的问题。若用户给出的规格已经充分，直接执行。

### 2. 检查现有场景

1. 检查场景单位与比例。
2. 逐级检查集合，不一次性倾倒大型场景。
3. 确认目标对象类型、父级、变换、旋转模式、修改器和材质。
4. 检查 Mesh 数据是否多对象共享；修改共享数据前先决定是否需要单用户副本。
5. 确认视图隐藏、视图层排除和渲染隐藏状态。
6. 对有骨骼的资产检查 Rest Pose、当前 Action、NLA 和默认保存姿态。

### 3. 选择资产分支

- 普通道具、桶、钥匙、箱子、锁等读取 [references/static-prop.md](references/static-prop.md)。
- 高度、提手、液面或其他参数需要在 Blender 中调整时读取 [references/adjustable-asset.md](references/adjustable-asset.md)。
- 炮台、角色、机械结构或需要动画片段时读取 [references/animated-asset.md](references/animated-asset.md)。

每次只加载与当前任务相关的分支。

### 4. 建模与结构

1. 按主要轮廓和 Unity 结构先搭建低复杂度模型。
2. 将 Unity 需要独立控制的部分拆为独立对象、骨骼或材质区域。
3. 在动画或旋转支点处设置真实轴心；不要依赖 Unity 中临时偏移空物体修正明显的资产错误。
4. 对平整结构使用一致法线和明确硬边；曲面使用足够但不过量的分段。
5. 清除重合点、重复面、共面叠面、无用内部面、退化面和孤立几何。
6. 小凹槽、木纹、颗粒和描边优先考虑纹理或 Shader，不默认堆积几何。
7. 如果需要 Unity 按部件换色，使用稳定对象或材质槽，不依赖 Blender 节点中的临时混色。

### 5. UV、材质与法线

- 先确认是否真的需要 UV；纯色换色资产可以没有 UV。
- 需要滚动或循环纹理时，按运动方向设计连续 UV，并验证边界像素和 Wrap Mode。
- PBR 资产按 Unity 目标管线约定 Base Color、Normal、Metallic、Roughness/Smoothness、AO 和 Emission。
- 法线贴图必须明确切线空间约定。
- 平面、硬边、倒角和曲面法线分别检查，避免倒角法线污染大平面。
- 材质槽数量以 Unity Draw Call 和实际换色需求为依据。

### 6. 可调与动画

- 可调资产保留清楚的控制对象或自定义属性，并验证极值不会穿插、翻面或破坏比例。
- 导出前明确参数是需要烘焙固定，还是只用于 Blender 制作阶段。
- 动画资产使用稳定骨骼层级、默认 Rest Pose 和独立 Action。
- 每个 Action 检查帧范围、循环属性、根骨骼位移和结束姿态。
- 保存 `.blend` 前清除临时 Pose，避免默认打开或导出成倒地、展开等动作末帧。

### 7. 质量检查

在 Blender 中运行：

```text
blender --background <asset.blend> --python scripts/validate_scene.py -- --require-closed --max-triangles <预算>
```

脚本只读取场景并输出 JSON，不修改资产。开放曲面或有意留口的模型不要使用 `--require-closed`。

详细验收项读取 [references/quality-gates.md](references/quality-gates.md)。

### 8. FBX 导出与回读

导出前读取 [references/unity-fbx-contract.md](references/unity-fbx-contract.md)，然后：

1. 保存源 `.blend`。
2. 复制或生成明确的导出状态，不让预览灯光、相机和辅助对象混入。
3. 按合同导出 FBX。
4. 新建空场景重新导入刚导出的 FBX。
5. 再次检查尺寸、朝向、对象、轴心、材质槽、法线、UV、骨骼、Action 和默认姿态。
6. 如能访问 Unity 项目，再检查 Model Importer、Avatar、动画片段、材质映射和实际 Prefab。

没有回读验证的 FBX 不算完成。

### 9. 交付

交付说明至少包含：

- Blender 源文件与 Unity FBX。
- 对象、材质、UV、骨骼和动画结构。
- 尺寸、朝向、轴心和默认姿态。
- 顶点、三角形、非流形边和已执行 QA。
- Unity 中需要手动设置的导入选项或材质。
- 哪些参数只在 Blender 可调，哪些能在 Unity 运行时修改。
- 预览图及尚未在 Unity 真机或实际 Shader 中验证的部分。
