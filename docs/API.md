# BYOVD Library API 文档

⚠️ **安全警告**：本库仅供授权的安全测试、渗透测试和教育工作使用。

---

## 快速开始

### 安装依赖

```bash
pip install pywin32 psutil
```

### 导入库

```python
from byovd_lib import BYOVD

with BYOVD() as byovd:
    # 你的代码
```

---

## API 接口

### 驱动管理

| 方法 | 描述 | 返回值 |
|------|------|--------|
| `load_driver()` | 加载驱动 | `bool` |
| `unload_driver()` | 卸载驱动 | `bool` |
| `is_driver_loaded()` | 检查驱动状态 | `bool` |

### 进程管理

| 方法 | 描述 | 参数 | 返回值 |
|------|------|------|--------|
| `kill(pid)` | 终止进程 | `pid: int` | `(bool, str)` |
| `kill_by_name(name, exact_match)` | 按名终止 | `name: str, exact_match: bool` | `list[(int, bool, str)]` |
| `list_processes()` | 列出进程 | 无 | `list[(int, str)]` |
| `get_process_by_name(name, exact_match)` | 查找进程 | `name: str, exact_match: bool` | `list[(int, str)]` |

### 杀毒软件检测

| 方法 | 描述 | 参数 | 返回值 |
|------|------|------|--------|
| `detect_av()` | 检测杀毒软件 | 无 | `list[(int, str, str)]` |
| `has_av(name)` | 检查特定杀软 | `name: str` | `bool` |

---

## 使用示例

### 基本用法

```python
from byovd_lib import BYOVD

with BYOVD() as byovd:
    # 终止 PID 1234
    success, msg = byovd.kill(1234)
    
    # 列出进程
    for pid, name in byovd.list_processes():
        print(f"{pid}: {name}")
    
    # 检测杀毒软件
    for pid, name, av in byovd.detect_av():
        print(f"{av}: {name}")
```

### 按名称终止

```python
from byovd_lib import BYOVD

with BYOVD() as byovd:
    # 终止所有记事本
    results = byovd.kill_by_name("notepad.exe")
    for pid, success, msg in results:
        print(f"PID {pid}: {'成功' if success else '失败'}")
```

### 检查杀毒软件

```python
from byovd_lib import BYOVD

with BYOVD() as byovd:
    # 检查是否有火绒
    if byovd.has_av("火绒"):
        print("检测到火绒")
    
    # 获取所有杀毒软件
    for pid, name, av in byovd.detect_av():
        print(f"{av}: {name} (PID: {pid})")
```

---

## 支持的杀毒软件

- Windows Defender
- Kaspersky (卡巴斯基)
- ESET NOD32
- Avast
- AVG
- BitDefender
- McAfee
- 火绒 Huorong
- 百度杀毒
- 360 安全卫士
- 腾讯电脑管家

---

## 注意事项

1. 需要管理员权限
2. 确保 `BdApiUtil64.sys` 存在于库目录或当前目录
3. 使用 `with` 语句自动管理资源

---

## 免责声明

本库仅供安全研究和教育目的使用。