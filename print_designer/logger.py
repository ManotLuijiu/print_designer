import logging
import os
from logging.handlers import RotatingFileHandler

import frappe

def get_logger(name="print_designer"):
    """Creates and returns a logger for the Print Designer app."""
    
    log_dir = os.path.join(frappe.utils.get_bench_path(), "logs", "print_designer")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, "print_designer.log")
    
    # Create a logger
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if logger is already configured
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Create a rotating file handler
    handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024 * 5,  # 5 MB
        backupCount=5
    )
    
    # Create a formatter and set it for the handler
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(handler)
    
    return logger
