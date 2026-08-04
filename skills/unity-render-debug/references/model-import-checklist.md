# 模型与导入检查

## 几何

- 是否存在重合点、重复面、共面叠面或无用内部面。
- 平整板面是否真的共面。
- 五边以上多边形是否在不同工具中产生不同三角化。
- 是否存在长瘦三角形、零面积面和非流形边。
- 倒角段数是否与目标屏幕尺寸相符。

## 法线与切线

- 使用导入法线还是 Unity 重算法线。
- 平面是否使用一致法线与硬边。
- 曲面是否在期望边界平滑。
- 倒角法线是否污染大平面。
- 法线贴图是否与切线空间和导入切线匹配。
- 负缩放或镜像是否反转切线手性。

## Model Importer

- Scale Factor 与真实尺寸。
- Mesh Compression。
- Read/Write。
- Optimize Mesh。
- Weld Vertices。
- Normals 与 Tangents。
- Material Import Mode。
- Rig、Avatar 和 Animation Clips。

Read/Write 只在 CPU 读取 Mesh、运行时合并或修改网格时需要。不要为了绕过架构问题长期全局启用。

## Renderer

- Cast Shadows。
- Receive Shadows；自定义 Shader 是否真正实现。
- Light Probes 与 Reflection Probes。
- Rendering Layer Mask。
- Static Batching、GPU Instancing 和 SRP Batcher。
- 共享材质与 `MaterialPropertyBlock`。

## 输出模型优化要求时

只写可验收要求：

- 拓扑限制。
- 法线与硬边。
- 倒角预算。
- 顶点与三角形预算。
- 材质子网格上限。
- FBX 三角拓扑与自定义法线。
- 不允许出现的视觉问题。

除非用户要求 Blender 操作步骤，否则不要把模型优化要求写成具体修改器教程。
