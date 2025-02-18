import logging

def setup_logger(name: str) -> logging.Logger:
    """设置并返回一个命名的日志记录器"""
    logger = logging.getLogger(name)
    
    # 如果logger已经有处理器，不再添加新的
    if logger.handlers:
        return logger
        
    # 设置日志级别
    logger.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)
    
    return logger 