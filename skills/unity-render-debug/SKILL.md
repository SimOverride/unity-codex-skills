---
name: unity-render-debug
description: 系统诊断 Unity 中由 Shader、材质、Renderer、URP Pass、渲染顺序、深度、模板、透明、阴影、描边、模型法线、拓扑或导入设置造成的画面异常。用于分析或修复条纹、黑面、伪描边、轮廓断裂、透明排序、阴影开关无效、自阴影、材质不一致、网格不可读、深度或法线纹理缺失、Shader 编译和跨平台渲染问题。用户只要求分析时保持只读；不用于一般玩法代码、纯审美调色或 Blender 资产从零制作。
---

# Unity 渲染排障

## 目标

用证据把问题定位到正确层级，再做最小修复。不要用反复调参数掩盖模型、导入或渲染流程错误。

## 路由

- 只要求解释或分析：保持只读，给出根因、证据和建议实验。
- 明确要求修复：定位根因后再修改，并同步项目当前状态文档。
- 问题源于 Blender 几何、轴心、UV 或动画资产本身：配合 `blender-unity-asset-pipeline`。
- 问题属于普通 Unity 模块接入而非渲染：改用 `unity-module-delivery`。

## 工作流

### 1. 固定现象

先记录：

- 正常与异常画面、摄像机、平台、分辨率和质量档。
- 使用的 Unity 版本、渲染管线和 Renderer。
- 受影响对象、材质、Shader、模型和 Prefab。
- 何时出现：编辑器、Game View、构建、特定角度、特定灯光或动画阶段。
- 哪些开关会使问题消失。

用户提供截图时，把截图现象与实际项目配置对应起来，不仅凭图片猜测。

### 2. 建立渲染事实

1. 读取项目 `AGENTS.md` 和渲染相关文档。
2. 检查 Git 状态，保留用户已有修改。
3. 确认 URP/Built-in/HDRP、Renderer Data、Renderer Feature、相机堆叠和后处理。
4. 定位目标 Renderer、材质、Shader、ShaderGraph、公共 HLSL、模型与 `.meta`。
5. 检查完整 Pass，不只检查 Fragment 主函数。
6. 可运行 `scripts/scan_unity_rendering.ps1 -Path <项目目录>` 生成只读渲染特征清单。

### 3. 按层定位

严格按以下层级检查：

1. **场景与相机**：灯光、相机、Renderer、质量档、HDR、MSAA、深度纹理、Opaque Texture。
2. **Renderer 与材质**：材质实例、PropertyBlock、Cast/Receive Shadows、渲染层、Queue、排序。
3. **Shader Pass**：Forward、ShadowCaster、DepthOnly、DepthNormals、Meta、Stencil、Blend、ZWrite、Cull。
4. **模型与导入**：拓扑、法线、切线、硬边、UV、负缩放、Read/Write、压缩和材质映射。
5. **多对象交互**：透明前后关系、屏幕空间遮罩、模板覆盖、共享深度、Render Feature 执行顺序。
6. **平台差异**：图形 API、精度、关键字、变体裁剪、WebGL/移动端限制。

症状到层级的映射读取 [references/diagnosis-matrix.md](references/diagnosis-matrix.md)。

### 4. 做最小隔离实验

每次只改变一个变量，并记录结果。优先使用不会破坏资产的临时副本、运行时开关或独立测试场景。

常用实验：

- 禁用高光、漫反射、阴影衰减或法线贴图中的一个。
- 使用 Unlit 材质区分几何轮廓与光照问题。
- 关闭 Cast Shadows 与 Receive Shadows，比较自阴影和受影。
- 使用统一法线或平面法线检查导入法线。
- 切换透明/不透明、ZWrite、Queue 和排序。
- 单独显示源遮罩、扩张遮罩和最终合成结果。
- 临时启用 Mesh Read/Write 验证运行时合并错误，但不要把它当作最终性能方案。

详细实验读取 [references/minimal-experiments.md](references/minimal-experiments.md)。

### 5. 形成根因链

在修改前明确写出：

```text
现象：
直接证据：
排除项：
根因所在层：
触发机制：
最小修复范围：
可能副作用：
```

不要把相关性当根因。例如“关闭 Cast Shadows 后条纹消失”说明问题与阴影投射链有关，但还要检查自定义 Shader 是否真正实现 Receive Shadows 开关、模型是否自遮挡，以及 ShadowCaster Pass 是否正确。

### 6. 修复

- 修改根因所在层，避免跨层补丁。
- 替换方案时删除旧 Pass、旧纹理、旧遮罩和失效配置，不保留多余兼容逻辑。
- 保持项目现有材质属性和运行时换色合同，除非用户要求破坏性迁移。
- Shader 需要同时考虑 Forward、ShadowCaster、DepthOnly、DepthNormals 和项目依赖的自定义 Pass。
- 对透明材质明确 Blend、ZWrite、Queue、Cull、阴影投射和深度参与策略。
- 对屏幕空间效果明确源遮罩、扩张、扣除和合成的数学关系与执行顺序。
- 模型问题不要长期用 Shader 特判掩盖；输出明确的模型优化要求。

URP 专项检查读取 [references/urp-shader-checklist.md](references/urp-shader-checklist.md)。
模型与导入专项检查读取 [references/model-import-checklist.md](references/model-import-checklist.md)。

### 7. 验证

至少完成：

1. Shader 或 C# 编译。
2. Unity 重新导入，无新的 Console 错误。
3. 正常案例与原失败案例的对比。
4. 不同观察角度、灯光方向和目标质量档。
5. 受影响材质、Prefab 和 Renderer Feature 的回归。
6. 如果目标是 WebGL、微信小游戏或移动端，使用对应构建或真机验证。
7. 检查 `git diff --check`、文档、CHANGELOG、CRLF 和 CodeGraph。

视觉问题没有画面对比或可复现人工步骤时，不要声称“效果已经验证”。

### 8. 输出

分析任务输出：

- 最可能根因及证据强度。
- 已排除原因。
- 最小验证实验。
- 推荐修复层和副作用。

修复任务额外输出：

- 修改的 Shader、材质、模型导入或 Renderer 配置。
- 保留和删除的旧流程。
- 自动验证结果。
- 仍需用户在 Unity 画面或目标平台确认的项目。
