# 渲染问题诊断矩阵

| 现象 | 优先检查 | 首个隔离实验 |
|---|---|---|
| 平面出现条纹 | 顶点法线、非共面多边形、自阴影 | 换 Unlit，再分别关闭 Cast/Receive Shadows |
| 关闭 Cast Shadows 后条纹消失 | 自阴影、ShadowCaster、模型共面叠面 | 保留 Cast，临时让 Forward 不乘阴影衰减 |
| 关闭 Receive Shadows 无效 | 自定义 Shader 未实现该开关 | 检查 `GetMainLight` 与 `shadowAttenuation` |
| 透明物体前后错乱 | Queue、ZWrite、排序、相交透明面 | 临时改不透明并开启 ZWrite |
| 物体边缘有伪描边 | 源遮罩空洞、深度、模板、扩张范围 | 分别显示源遮罩与扩张遮罩 |
| 描边断裂 | 法线外扩、模板覆盖、MSAA、分辨率 | 关闭 MSAA 并固定描边像素宽度 |
| 内部结构也描边 | 每个子网格独立描边 | 合并为整体投影遮罩后再扩张 |
| 黑面或消失 | Cull、法线翻转、负缩放、深度 | 改 `Cull Off` 并显示法线方向 |
| 材质颜色互相影响 | 修改共享材质 | 检查是否应使用 `MaterialPropertyBlock` |
| 运行时合并网格报不可读 | Model Importer Read/Write | 临时启用 Read/Write 验证调用链 |
| Scene 正常、Build 异常 | Shader 变体裁剪、图形 API、精度 | 固定关键字并检查构建日志 |
| Game View 与 Scene View 不同 | 相机 Renderer、后处理、深度纹理 | 使用同一相机和 Renderer 截图 |
| 深度法线效果缺失 | DepthNormals Pass、Renderer Feature | 用调试 Shader 显示深度法线纹理 |
| 纹理滚动到接缝断裂 | UV、Wrap Mode、边界像素 | 显示 UV 棋盘并设 Repeat |

## 判断原则

- Unlit 仍异常：优先模型、深度、透明或屏幕空间流程。
- Unlit 正常、Lit 异常：优先法线、灯光、高光和阴影。
- 只有某角度异常：优先法线插值、共面面、透明排序和背面剔除。
- 只有某平台异常：优先图形 API、精度、变体和平台能力。
- 只有运行时异常：优先动态材质、PropertyBlock、网格可读性和 Render Feature 顺序。
