#!/usr/bin/env python3
"""
性能优化文档整理脚本
整理和归档重复的性能优化文档
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

# 核心文档 - 保留在根目录
CORE_DOCS = {
    'PERFORMANCE_OPTIMIZATION_FINAL.md',  # 最终总结报告
    'PERFORMANCE_OPTIMIZATION.md',  # 详细优化指南
    'CDN_SETUP_GUIDE.md',  # CDN配置指南
    'PERFORMANCE_QUICK_GUIDE.md',  # 快速参考指南
    'README_PERFORMANCE_OPTIMIZATION.md',  # 项目README
}

# 归档目录
ARCHIVE_DIR = 'docs/archive/performance-reports'

def create_archive_dir():
    """创建归档目录"""
    archive_path = Path(ARCHIVE_DIR)
    archive_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ 创建归档目录: {ARCHIVE_DIR}")
    return archive_path

def find_performance_docs():
    """查找所有性能优化文档"""
    current_dir = Path('.')
    performance_docs = []

    for file in current_dir.glob('PERFORMANCE_*.md'):
        if file.is_file():
            performance_docs.append(file)

    return performance_docs

def organize_docs():
    """整理文档"""
    print("=" * 80)
    print("📚 性能优化文档整理工具")
    print("=" * 80)
    print()

    # 创建归档目录
    archive_path = create_archive_dir()

    # 查找所有性能文档
    all_docs = find_performance_docs()
    print(f"📄 找到 {len(all_docs)} 个性能优化文档")
    print()

    # 分类文档
    core_docs = []
    archive_docs = []

    for doc in all_docs:
        if doc.name in CORE_DOCS:
            core_docs.append(doc)
        else:
            archive_docs.append(doc)

    # 显示核心文档
    print("📌 核心文档 (保留在根目录):")
    print("-" * 80)
    for doc in sorted(core_docs):
        size_kb = doc.stat().st_size / 1024
        print(f"  ✅ {doc.name:<50} {size_kb:>6.1f} KB")
    print()

    # 显示待归档文档
    print("📦 待归档文档:")
    print("-" * 80)
    for doc in sorted(archive_docs):
        size_kb = doc.stat().st_size / 1024
        print(f"  📄 {doc.name:<50} {size_kb:>6.1f} KB")
    print()

    # 统计信息
    print("=" * 80)
    print("📊 统计信息")
    print("=" * 80)
    print(f"总文档数:       {len(all_docs)}")
    print(f"核心文档:       {len(core_docs)}")
    print(f"待归档文档:     {len(archive_docs)}")
    print()

    # 询问是否执行归档
    print("=" * 80)
    print("⚠️  归档操作说明")
    print("=" * 80)
    print(f"将移动 {len(archive_docs)} 个文档到: {ARCHIVE_DIR}")
    print("核心文档将保留在根目录")
    print()

    response = input("是否执行归档操作? (yes/no): ").strip().lower()

    if response in ['yes', 'y']:
        print()
        print("🚀 开始归档...")
        print("-" * 80)

        archived_count = 0
        for doc in archive_docs:
            try:
                dest = archive_path / doc.name
                shutil.move(str(doc), str(dest))
                print(f"  ✅ 已归档: {doc.name}")
                archived_count += 1
            except Exception as e:
                print(f"  ❌ 归档失败: {doc.name} - {e}")

        print()
        print("=" * 80)
        print("✅ 归档完成")
        print("=" * 80)
        print(f"已归档文档数: {archived_count}")
        print(f"归档位置: {ARCHIVE_DIR}")
        print()

        # 创建归档索引
        create_archive_index(archive_path, archive_docs)
    else:
        print()
        print("❌ 已取消归档操作")
        print()

def create_archive_index(archive_path, archived_docs):
    """创建归档索引文件"""
    index_file = archive_path / 'INDEX.md'

    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("# 性能优化文档归档索引\n\n")
        f.write(f"**归档日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write("## 归档文档列表\n\n")

        for doc in sorted(archived_docs, key=lambda x: x.name):
            f.write(f"- [{doc.name}](./{doc.name})\n")

        f.write("\n---\n\n")
        f.write("## 说明\n\n")
        f.write("这些文档已被归档，因为它们的内容已整合到核心文档中。\n\n")
        f.write("### 核心文档位置\n\n")
        f.write("核心文档保留在项目根目录:\n\n")
        f.write("1. `PERFORMANCE_OPTIMIZATION_FINAL.md` - 最终总结报告\n")
        f.write("2. `PERFORMANCE_OPTIMIZATION.md` - 详细优化指南\n")
        f.write("3. `CDN_SETUP_GUIDE.md` - CDN配置指南\n")
        f.write("4. `PERFORMANCE_QUICK_GUIDE.md` - 快速参考指南\n")
        f.write("5. `README_PERFORMANCE_OPTIMIZATION.md` - 项目README\n")

    print(f"📝 已创建归档索引: {index_file}")

def show_summary():
    """显示文档整理建议"""
    print()
    print("=" * 80)
    print("💡 文档整理建议")
    print("=" * 80)
    print()
    print("建议的文档结构:")
    print()
    print("根目录 (核心文档):")
    print("  ├── PERFORMANCE_OPTIMIZATION_FINAL.md      # 最终总结报告")
    print("  ├── PERFORMANCE_OPTIMIZATION.md            # 详细优化指南")
    print("  ├── CDN_SETUP_GUIDE.md                     # CDN配置指南")
    print("  ├── PERFORMANCE_QUICK_GUIDE.md             # 快速参考指南")
    print("  └── README_PERFORMANCE_OPTIMIZATION.md     # 项目README")
    print()
    print("归档目录 (历史文档):")
    print("  └── docs/archive/performance-reports/")
    print("      ├── INDEX.md                           # 归档索引")
    print("      └── [其他历史文档...]")
    print()

if __name__ == "__main__":
    try:
        organize_docs()
        show_summary()
    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
