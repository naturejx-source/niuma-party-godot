"""
Meshy API -> Blender 桥接工具
用法:
  1. 填入你的 MESHY_API_KEY
  2. 运行: python meshy_to_blender.py
  3. 脚本会自动：上传图片 → 等待生成 → 下载模型 → 导入 Blender
"""

import requests
import time
import json
import socket
import os
import sys
import base64

# ============================================================
# 配置区 — 在这里填你的 Key 和图片路径
# ============================================================
MESHY_API_KEY = "msy_L2CcXpBLWfT9Qc5qyG7SvlgHiv70VXbg4mg2"

# 菠蘿包参考图（白底那张效果最好）
IMAGE_PATH = r"C:\Users\natur\Desktop\GAMEFI\螢幕擷取畫面 2026-04-14 193941.png"

# 输出目录
OUTPUT_DIR = r"C:\Users\natur\Desktop\GAMEFI"

# Blender addon 地址
BLENDER_HOST = "localhost"
BLENDER_PORT = 9876

# ============================================================
# Meshy API 封装
# ============================================================
MESHY_BASE = "https://api.meshy.ai/openapi/v2"


def meshy_headers():
    return {
        "Authorization": f"Bearer {MESHY_API_KEY}",
    }


def step1_create_task(image_path):
    """上传图片，创建 Image-to-3D 任务"""
    print(f"\n[1/4] 上传图片到 Meshy: {os.path.basename(image_path)}")

    url = f"{MESHY_BASE}/image-to-3d"

    # Meshy v2 支持 image_url 或 file upload
    # 先尝试用 base64 data URI
    with open(image_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("ascii")

    ext = os.path.splitext(image_path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    data_uri = f"data:{mime};base64,{img_data}"

    payload = {
        "image_url": data_uri,
        "enable_pbr": True,
        "should_remesh": True,
        "topology": "quad",
        "target_polycount": 30000,
    }

    resp = requests.post(url, headers={**meshy_headers(), "Content-Type": "application/json"}, json=payload)

    if resp.status_code != 202 and resp.status_code != 200:
        # 尝试 multipart upload 方式
        print(f"  Data URI 方式返回 {resp.status_code}, 尝试 file upload...")
        with open(image_path, "rb") as f:
            files = {"image_file": (os.path.basename(image_path), f, mime)}
            data = {
                "enable_pbr": "true",
                "should_remesh": "true",
                "topology": "quad",
                "target_polycount": "30000",
            }
            resp = requests.post(url, headers=meshy_headers(), files=files, data=data)

    if resp.status_code in (200, 202):
        result = resp.json()
        task_id = result.get("result", result.get("id", ""))
        print(f"  Task 创建成功! ID: {task_id}")
        return task_id
    else:
        print(f"  ERROR {resp.status_code}: {resp.text[:500]}")
        sys.exit(1)


def step2_poll_status(task_id, max_wait=600):
    """轮询任务状态，直到完成"""
    print(f"\n[2/4] 等待 Meshy 生成 3D 模型 (最多 {max_wait}s)...")

    url = f"{MESHY_BASE}/image-to-3d/{task_id}"
    start = time.time()

    while time.time() - start < max_wait:
        resp = requests.get(url, headers=meshy_headers())
        if resp.status_code != 200:
            print(f"  Poll error {resp.status_code}: {resp.text[:200]}")
            time.sleep(10)
            continue

        data = resp.json()
        status = data.get("status", "UNKNOWN")
        progress = data.get("progress", 0)

        elapsed = int(time.time() - start)
        print(f"  [{elapsed:3d}s] status={status}  progress={progress}%", end="\r")

        if status == "SUCCEEDED":
            print(f"\n  生成完成! 耗时 {elapsed}s")
            return data
        elif status in ("FAILED", "EXPIRED", "CANCELED"):
            print(f"\n  任务失败: {status}")
            print(f"  详情: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            sys.exit(1)

        time.sleep(8)

    print(f"\n  超时 ({max_wait}s)!")
    sys.exit(1)


def step3_download_model(task_data):
    """下载生成的 3D 模型"""
    print(f"\n[3/4] 下载 3D 模型...")

    # Meshy 返回多种格式
    model_urls = task_data.get("model_urls", {})
    # 优先 glb, 其次 fbx, obj
    download_url = model_urls.get("glb") or model_urls.get("fbx") or model_urls.get("obj")

    if not download_url:
        # 有时候在 model_url 字段
        download_url = task_data.get("model_url", "")

    if not download_url:
        print("  ERROR: 找不到模型下载链接!")
        print(f"  完整返回: {json.dumps(task_data, ensure_ascii=False, indent=2)[:1000]}")
        sys.exit(1)

    ext = ".glb"
    if "fbx" in download_url.lower():
        ext = ".fbx"
    elif "obj" in download_url.lower():
        ext = ".obj"

    out_path = os.path.join(OUTPUT_DIR, f"PineappleBun_Meshy{ext}")

    resp = requests.get(download_url, stream=True)
    if resp.status_code == 200:
        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        size_mb = os.path.getsize(out_path) / 1024 / 1024
        print(f"  下载完成: {out_path} ({size_mb:.1f} MB)")

        # 同时下载纹理贴图（如果有）
        texture_urls = task_data.get("texture_urls", [])
        if isinstance(texture_urls, dict):
            for tex_name, tex_url in texture_urls.items():
                tex_path = os.path.join(OUTPUT_DIR, f"PineappleBun_Meshy_{tex_name}.png")
                r = requests.get(tex_url)
                if r.status_code == 200:
                    with open(tex_path, "wb") as f:
                        f.write(r.content)
                    print(f"  纹理: {tex_path}")

        return out_path
    else:
        print(f"  下载失败: {resp.status_code}")
        sys.exit(1)


def step4_import_to_blender(model_path):
    """通过 socket 发送命令给 Blender addon，导入模型"""
    print(f"\n[4/4] 导入到 Blender...")

    # 构造 Blender Python 代码
    path_escaped = model_path.replace("\\", "\\\\")
    ext = os.path.splitext(model_path)[1].lower()

    if ext == ".glb" or ext == ".gltf":
        import_code = f'bpy.ops.import_scene.gltf(filepath=r"{model_path}")'
    elif ext == ".fbx":
        import_code = f'bpy.ops.import_scene.fbx(filepath=r"{model_path}")'
    elif ext == ".obj":
        import_code = f'bpy.ops.wm.obj_import(filepath=r"{model_path}")'
    else:
        print(f"  不支持的格式: {ext}")
        return False

    code = f"""
import bpy

# 导入 Meshy 生成的模型
{import_code}

# 重命名导入的对象
imported = bpy.context.selected_objects
for obj in imported:
    if obj.type == 'MESH':
        obj.name = "PineappleBun_Meshy"
        # 移到原点旁边方便对比
        obj.location = (3, 0, 0.5)
        break

print(f"IMPORT_OK: imported {{len(imported)}} objects from Meshy")
"""

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((BLENDER_HOST, BLENDER_PORT))
        cmd = json.dumps({"type": "execute_code", "params": {"code": code}})
        sock.sendall(cmd.encode("utf-8"))
        sock.settimeout(30)

        data = b""
        while True:
            chunk = sock.recv(8192)
            if not chunk:
                break
            data += chunk
            try:
                json.loads(data)
                break
            except:
                continue

        sock.close()
        result = json.loads(data)

        if result.get("status") == "success":
            output = result.get("result", {}).get("result", "")
            print(f"  {output}")
            return True
        else:
            print(f"  Blender 错误: {result.get('message', str(result))[:300]}")
            return False

    except ConnectionRefusedError:
        print("  无法连接 Blender! 请确保 BlenderMCP addon 已启动 (port 9876)")
        print(f"  模型已保存到: {model_path}")
        print("  你可以手动在 Blender 中 File > Import > glTF 导入")
        return False


# ============================================================
# 主流程
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Meshy Image-to-3D -> Blender 桥接工具")
    print("=" * 60)

    if MESHY_API_KEY == "YOUR_MESHY_API_KEY_HERE":
        print("\n请先在脚本顶部填入你的 MESHY_API_KEY!")
        print("获取方式: https://app.meshy.ai -> Settings -> API Keys")
        sys.exit(1)

    if not os.path.exists(IMAGE_PATH):
        print(f"\n找不到图片: {IMAGE_PATH}")
        sys.exit(1)

    # 执行完整流程
    task_id = step1_create_task(IMAGE_PATH)
    task_data = step2_poll_status(task_id)
    model_path = step3_download_model(task_data)
    step4_import_to_blender(model_path)

    print("\n" + "=" * 60)
    print("  完成! 在 Blender 中可以看到两个菠蘿包:")
    print("  - 左边 (0,0,0): 脚本建模版")
    print("  - 右边 (3,0,0): Meshy AI 生成版")
    print("=" * 60)
