"""只读检查当前 Blender 场景中的 Unity 资产结构与网格质量。"""

import argparse
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


def parse_args():
    """解析 Blender 在 `--` 之后传递给脚本的参数。"""
    script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="检查 Blender 场景并输出 JSON 报告。")
    parser.add_argument("--collection", help="仅检查指定集合及其子集合。")
    parser.add_argument("--output", help="可选的 JSON 输出文件。")
    parser.add_argument("--require-closed", action="store_true", help="把非流形边视为失败。")
    parser.add_argument("--max-triangles", type=int, help="可选的总三角形预算。")
    return parser.parse_args(script_args)


def collect_objects(collection_name):
    """按集合筛选对象；未指定时检查当前场景。"""
    if not collection_name:
        return list(bpy.context.scene.objects)

    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        raise ValueError(f"找不到集合：{collection_name}")

    objects = set(collection.objects)
    pending = list(collection.children)
    while pending:
        child = pending.pop()
        objects.update(child.objects)
        pending.extend(child.children)
    return sorted(objects, key=lambda item: item.name)


def vector_values(vector):
    """把 Blender 向量转换成可序列化的小数列表。"""
    return [round(float(value), 6) for value in vector]


def get_world_bounds(obj):
    """计算对象包围盒的世界坐标范围。"""
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = Vector((min(point.x for point in corners), min(point.y for point in corners), min(point.z for point in corners)))
    maximum = Vector((max(point.x for point in corners), max(point.y for point in corners), max(point.z for point in corners)))
    return {
        "min": vector_values(minimum),
        "max": vector_values(maximum),
        "size": vector_values(maximum - minimum),
    }


def inspect_mesh_object(obj):
    """检查原始 Mesh 数据，不应用或修改修改器。"""
    mesh = obj.data
    mesh.calc_loop_triangles()

    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.normal_update()
        loose_vertices = sum(1 for vertex in bm.verts if not vertex.link_edges)
        non_manifold_edges = sum(1 for edge in bm.edges if not edge.is_manifold)
        zero_area_faces = sum(1 for face in bm.faces if face.calc_area() <= 1e-12)
    finally:
        bm.free()

    return {
        "name": obj.name,
        "dataName": mesh.name,
        "dataUsers": mesh.users,
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "polygons": len(mesh.polygons),
        "triangles": len(mesh.loop_triangles),
        "looseVertices": loose_vertices,
        "nonManifoldEdges": non_manifold_edges,
        "zeroAreaFaces": zero_area_faces,
        "uvLayers": [layer.name for layer in mesh.uv_layers],
        "materialSlots": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "modifiers": [{"name": modifier.name, "type": modifier.type} for modifier in obj.modifiers],
        "shapeKeys": [block.name for block in mesh.shape_keys.key_blocks] if mesh.shape_keys else [],
        "location": vector_values(obj.location),
        "rotationMode": obj.rotation_mode,
        "rotationEulerDegrees": vector_values([math.degrees(value) for value in obj.rotation_euler]),
        "scale": vector_values(obj.scale),
        "hasNegativeScale": obj.scale.x * obj.scale.y * obj.scale.z < 0,
        "worldBounds": get_world_bounds(obj),
        "parent": obj.parent.name if obj.parent else None,
    }


def build_report(objects):
    """汇总场景、网格、骨骼、动作和材质信息。"""
    mesh_objects = [obj for obj in objects if obj.type == "MESH"]
    armatures = [obj for obj in objects if obj.type == "ARMATURE"]
    mesh_reports = [inspect_mesh_object(obj) for obj in mesh_objects]

    total_triangles = sum(item["triangles"] for item in mesh_reports)
    total_non_manifold = sum(item["nonManifoldEdges"] for item in mesh_reports)
    total_zero_area = sum(item["zeroAreaFaces"] for item in mesh_reports)

    unit_settings = bpy.context.scene.unit_settings
    return {
        "blendFile": bpy.data.filepath,
        "scene": bpy.context.scene.name,
        "units": {
            "system": unit_settings.system,
            "scaleLength": unit_settings.scale_length,
            "lengthUnit": unit_settings.length_unit,
        },
        "objectCount": len(objects),
        "objectTypes": {
            object_type: sum(1 for obj in objects if obj.type == object_type)
            for object_type in sorted({obj.type for obj in objects})
        },
        "meshes": mesh_reports,
        "armatures": [
            {
                "name": obj.name,
                "bones": len(obj.data.bones),
                "parent": obj.parent.name if obj.parent else None,
                "scale": vector_values(obj.scale),
            }
            for obj in armatures
        ],
        "actions": [
            {
                "name": action.name,
                "frameRange": [round(float(value), 3) for value in action.frame_range],
                "fcurves": len(action.fcurves),
            }
            for action in bpy.data.actions
        ],
        "materials": sorted({material.name for obj in mesh_objects for material in obj.data.materials if material}),
        "summary": {
            "meshObjects": len(mesh_objects),
            "totalTriangles": total_triangles,
            "totalNonManifoldEdges": total_non_manifold,
            "totalZeroAreaFaces": total_zero_area,
        },
    }


def main():
    """执行检查并按用户选项决定退出码。"""
    args = parse_args()
    objects = collect_objects(args.collection)
    report = build_report(objects)

    failures = []
    summary = report["summary"]
    if args.require_closed and summary["totalNonManifoldEdges"] > 0:
        failures.append(f"发现 {summary['totalNonManifoldEdges']} 条非流形边。")
    if summary["totalZeroAreaFaces"] > 0:
        failures.append(f"发现 {summary['totalZeroAreaFaces']} 个零面积面。")
    if args.max_triangles is not None and summary["totalTriangles"] > args.max_triangles:
        failures.append(
            f"总三角形 {summary['totalTriangles']} 超过预算 {args.max_triangles}。"
        )

    report["failures"] = failures
    output_text = json.dumps(report, ensure_ascii=False, indent=2)
    print(output_text)

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text + "\n", encoding="utf-8")

    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
