import logging
import sys

class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._init_logger()
        return cls._instance
    
    def _init_logger(self):
        self.logger = logging.getLogger("BakUI")
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        self.gui_callback = None

    def set_gui_callback(self, callback):
        self.gui_callback = callback

    def info(self, msg):
        self.logger.info(msg)
        if self.gui_callback:
            self.gui_callback(f"[INFO] {msg}")

    def error(self, msg):
        self.logger.error(msg)
        if self.gui_callback:
            self.gui_callback(f"[ERROR] {msg}")

    def warning(self, msg):
        self.logger.warning(msg)
        if self.gui_callback:
            self.gui_callback(f"[WARN] {msg}")

