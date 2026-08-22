"""
日志系统
将日志同时输出到控制台和文件（%APPDATA%/vrc_trans/app.log）
支持日志轮转，单文件最大 2MB，保留 3 个备份
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_log_dir() -> Path:
    """获取日志目录"""
    if os.name == "nt":
        base = os.environ.get("APPDATA", str(Path.home()))
    else:
        base = str(Path.home() / ".config")
    d = Path(base) / "vrc_trans"
    d.mkdir(parents=True, exist_ok=True)
    return d


LOG_FILE = get_log_dir() / "app.log"

# 全局 logger 实例
_logger = None


def setup_logging(level=logging.INFO):
    """
    初始化日志系统
    在程序启动时调用一次
    """
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("vrc_trans")
    logger.setLevel(level)
    logger.propagate = False

    # 日志格式
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 文件 handler（轮转）
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=2 * 1024 * 1024,  # 2MB
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"[Logger] 文件日志初始化失败: {e}")

    # 控制台 handler（仅在有控制台时输出）
    try:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(fmt)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)
    except Exception:
        pass

    _logger = logger
    logger.info("=" * 50)
    logger.info("程序启动，日志系统初始化完成")
    logger.info(f"日志文件: {LOG_FILE}")
    return logger


def get_logger(name: str = "vrc_trans") -> logging.Logger:
    """
    获取 logger 实例
    如果尚未初始化，自动初始化
    """
    global _logger
    if _logger is None:
        setup_logging()
    if name == "vrc_trans":
        return _logger
    return _logger.getChild(name)


# 便捷函数
def debug(msg, *args, **kwargs):
    get_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    get_logger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    get_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    get_logger().error(msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    """记录异常并附堆栈"""
    get_logger().exception(msg, *args, **kwargs)
