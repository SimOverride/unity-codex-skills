# URP Shader 检查

## SubShader

- `RenderPipeline` 标签是否指向 Universal Pipeline。
- `RenderType` 与 `Queue` 是否和透明策略一致。
- LOD、Target、关键字与目标平台是否匹配。

## Forward Pass

- 正确声明 `LightMode`。
- 顶点位置、世界法线、视线和阴影坐标来自一致空间。
- 正确处理主光、附加光、距离衰减和阴影衰减。
- 如果设计为不接收阴影，不要仍无条件乘 `shadowAttenuation`。
- Alpha Clip、透明度和雾效在所有相关 Pass 中保持一致。

## ShadowCaster

- 需要投影的材质包含正确 ShadowCaster Pass。
- Alpha Clip 物体使用相同裁剪规则。
- 透明物体是否投影必须明确决定。
- 检查 Cull 和顶点位移是否与 Forward 一致。

## DepthOnly 与 DepthNormals

- Renderer Feature、SSAO、描边或后处理依赖深度时必须有正确 Pass。
- 顶点动画和 Alpha Clip 必须与 Forward 一致。
- 法线空间和编码方式与 URP 版本匹配。

## 透明

- 明确 `Blend`。
- 明确 `ZWrite`。
- 明确 Queue 与排序优先级。
- 避免相互穿插的大面积透明面依赖对象级排序。
- 明确是否写深度、接收阴影、投射阴影和参与屏幕空间效果。

## 模板与屏幕空间效果

- 记录每个 Stencil 位的所有者。
- 检查 Render Feature 注入点。
- 检查相机堆叠、MSAA 和动态分辨率。
- 确认临时 RenderTexture 的格式、尺寸、清除方式和生命周期。
- 检查源遮罩、扩张、扣除和合成顺序。

## 兼容性

- 保留项目运行时依赖的属性名。
- 检查 SRP Batcher 所需常量缓冲布局。
- 检查 Instancing、GPU Skinning 和 MaterialPropertyBlock。
- 目标平台构建时检查 Shader 变体和编译日志。
