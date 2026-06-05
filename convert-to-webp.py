import os
from pathlib import Path
import cv2
import numpy as np
import time

# ============================================================
# 配置常量
# ============================================================

# 仓库根目录（脚本所在目录）
REPO_DIR = Path(__file__).parent

# 源图像目录（存放原始格式图像）
SOURCE_DIR = REPO_DIR / "blog" / "images" / "original"

# 目标输出目录（存放转换后的WebP图像）
DEST_DIR = REPO_DIR / "blog" / "images" / "webp"

# WebP压缩质量（1-100，值越大质量越高但文件越大）
WEBP_QUALITY = 80

# 支持转换的图像格式列表
SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif"]


# ============================================================
# 目录创建函数
# ============================================================


def ensure_dir(dir_path):
    """
    确保目录存在，如果不存在则创建

    Args:
        dir_path: 目录路径（Path对象或字符串）
    """
    Path(dir_path).mkdir(parents=True, exist_ok=True)


# ============================================================
# 图像转换函数
# ============================================================


def convert_image(input_path, output_path):
    """
    将单个图像转换为WebP格式

    Args:
        input_path: 输入图像路径
        output_path: 输出WebP图像路径

    Returns:
        dict: 包含成功状态的字典
              - success: bool 表示转换是否成功
              - inputPath: 输入文件路径
              - outputPath: 输出文件路径（成功时）
              - error: 错误信息（失败时）
    """
    try:
        # 确保输出目录存在
        ensure_dir(Path(output_path).parent)

        # 读取图像（OpenCV 使用 BGR 格式）
        img = cv2.imread(str(input_path))
        if img is None:
            raise ValueError(f"无法读取图像: {input_path}")

        # 保存为 WebP 格式
        # OpenCV 的 imwrite 自动根据扩展名选择编码器
        success = cv2.imwrite(
            str(output_path), img, [cv2.IMWRITE_WEBP_QUALITY, WEBP_QUALITY]
        )

        if not success:
            raise ValueError(f"无法保存 WebP 文件: {output_path}")

        return {
            "success": True,
            "inputPath": str(input_path),
            "outputPath": str(output_path),
        }
    except Exception as e:
        # 捕获并返回错误信息
        return {"success": False, "inputPath": str(input_path), "error": str(e)}


# ============================================================
# 目录处理函数
# ============================================================


def process_directory(source_dir, dest_dir):
    """
    处理源目录中的所有图像文件，转换为WebP格式

    功能包括：
    1. 递归扫描源目录中的支持格式图像
    2. 检查目标文件是否需要更新（比较修改时间）
    3. 执行图像格式转换
    4. 清理孤立的WebP文件（没有对应源文件的）

    Args:
        source_dir: 源图像目录路径
        dest_dir: 目标WebP输出目录路径

    Returns:
        dict: 处理结果统计
              - converted: 成功转换的文件列表
              - failed: 转换失败的文件列表
              - skipped: 跳过的文件列表（已存在且为最新）
              - deleted: 删除的孤立文件列表
    """
    # 初始化结果统计字典
    results = {"converted": [], "failed": [], "skipped": [], "deleted": []}

    # 检查源目录是否存在
    if not source_dir.exists():
        print(f"Source directory does not exist: {source_dir}")
        print("Skipping image conversion.")
        return results

    # 用于记录源文件路径（用于后续检查孤立文件）
    source_files = {}

    def process_path(current_dir, relative_dir=Path(".")):
        """
        递归处理目录中的文件和子目录

        Args:
            current_dir: 当前处理的目录
            relative_dir: 相对于源目录的相对路径
        """
        # 遍历当前目录的所有条目
        for entry in current_dir.iterdir():
            if entry.is_dir():
                # 递归处理子目录
                process_path(entry, relative_dir / entry.name)
            elif entry.is_file():
                # 获取文件扩展名并转为小写
                ext = entry.suffix.lower()

                # 检查是否为支持的图像格式
                if ext in SUPPORTED_FORMATS:
                    # 计算相对路径并去除扩展名作为基础名称
                    rel_path = relative_dir / entry.name
                    base_name = str(rel_path).replace(rel_path.suffix, "")
                    source_files[base_name] = entry

                    # 构建输出WebP文件路径
                    output_path = dest_dir / str(rel_path).replace(
                        rel_path.suffix, ".webp"
                    )

                    # 检查目标文件是否已存在
                    if output_path.exists():
                        # 获取源文件和目标文件的修改时间
                        source_stat = entry.stat()
                        dest_stat = output_path.stat()

                        # 比较修改时间：如果源文件没有更新，则跳过转换
                        if source_stat.st_mtime <= dest_stat.st_mtime:
                            results["skipped"].append(
                                {
                                    "inputPath": str(entry),
                                    "outputPath": str(output_path),
                                    "reason": "WebP file already exists and is up-to-date",
                                }
                            )
                            continue

                    # 执行图像转换
                    result = convert_image(entry, output_path)

                    # 根据转换结果更新统计
                    if result["success"]:
                        results["converted"].append(result)
                    else:
                        results["failed"].append(result)

    # 开始处理源目录
    process_path(source_dir)

    # 检查并清理孤立的WebP文件
    if dest_dir.exists():

        def check_orphaned_files(current_dir):
            """
            递归检查并删除孤立的WebP文件

            孤立文件定义：在目标目录中存在，但没有对应源文件的WebP文件
            （可能是因为源文件已被删除或重命名）

            Args:
                current_dir: 当前检查的目录
            """
            for entry in current_dir.iterdir():
                if entry.is_dir():
                    # 递归检查子目录
                    check_orphaned_files(entry)
                elif entry.is_file() and entry.name.lower().endswith(".webp"):
                    # 计算相对于目标目录的路径
                    rel_path = entry.relative_to(dest_dir)
                    base_name = str(rel_path).replace(".webp", "")

                    # 检查是否存在对应的源文件
                    if base_name not in source_files:
                        try:
                            # 删除孤立的WebP文件
                            entry.unlink()
                            results["deleted"].append(
                                {
                                    "outputPath": str(entry),
                                    "reason": "No corresponding source file found",
                                }
                            )
                        except Exception as e:
                            # 记录删除失败的文件
                            results["failed"].append(
                                {
                                    "inputPath": str(entry),
                                    "error": f"Failed to delete orphaned WebP: {str(e)}",
                                }
                            )

            # 清理空目录（如果不是根目录）
            if current_dir != dest_dir:
                try:
                    remaining = list(current_dir.iterdir())
                    if len(remaining) == 0:
                        current_dir.rmdir()
                except OSError:
                    # 忽略删除空目录时的错误（如目录非空）
                    pass

        # 执行孤立文件检查
        check_orphaned_files(dest_dir)

    return results


# ============================================================
# 主函数
# ============================================================


def main():
    # 打印头部信息
    print("=" * 60)
    print("Image to WebP Conversion Tool")
    print("=" * 60)
    print(f"Source Directory: {SOURCE_DIR}")
    print(f"Destination Directory: {DEST_DIR}")
    print(f"WebP Quality: {WEBP_QUALITY}%")
    print("=" * 60)
    print()

    # 记录开始时间并执行处理
    start_time = time.time()
    results = process_directory(Path(SOURCE_DIR), Path(DEST_DIR))
    elapsed_time = f"{(time.time() - start_time):.2f}"

    # 打印转换摘要
    print("Conversion Summary:")
    print("-" * 60)

    # 输出删除的孤立文件
    if results["deleted"]:
        print(f"\n🗑  Deleted {len(results['deleted'])} orphaned WebP file(s):")
        for r in results["deleted"]:
            rel_path = Path(r["outputPath"]).relative_to(REPO_DIR)
            print(f"  {rel_path}")

    # 输出成功转换的文件
    if results["converted"]:
        print(f"\n✓ Successfully converted {len(results['converted'])} image(s):")
        for r in results["converted"]:
            rel_path = Path(r["inputPath"]).relative_to(REPO_DIR)
            rel_output = Path(r["outputPath"]).relative_to(REPO_DIR)
            print(f"  {rel_path} → {rel_output}")

    # 输出跳过的文件
    if results["skipped"]:
        print(f"\n⊘ Skipped {len(results['skipped'])} image(s) (already up-to-date):")
        for r in results["skipped"]:
            rel_path = Path(r["inputPath"]).relative_to(REPO_DIR)
            print(f'  {rel_path} ({r["reason"]})')

    # 输出转换失败的文件
    if results["failed"]:
        print(f"\n✗ Failed to convert {len(results['failed'])} image(s):")
        for r in results["failed"]:
            rel_path = Path(r["inputPath"]).relative_to(REPO_DIR)
            print(f'  {rel_path}: {r["error"]}')

    # 打印尾部信息
    print()
    print("-" * 60)
    print(f"Total time: {elapsed_time}s")
    print("=" * 60)

    # 如果有失败的文件，返回错误码
    if results["failed"]:
        exit(1)


# ============================================================
# 模块入口点
# ============================================================

if __name__ == "__main__":
    # 当直接运行此脚本时执行主函数
    # 当作为模块导入时不执行
    main()
