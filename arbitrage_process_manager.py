"""
Process management module for the arbitrage engine.

This module provides functionality for starting, stopping, and monitoring
the arbitrage engine subprocess with comprehensive logging and status tracking.
"""

import logging
import os
import signal
import subprocess
import threading
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any


class ProcessStatus(Enum):
    """Enumeration of possible process states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    CRASHED = "crashed"


class ArbitrageProcessManager:
    """
    Manages the lifecycle of the arbitrage engine subprocess.
    
    Provides functionality for:
    - Starting and stopping the arbitrage engine
    - Monitoring process health and status
    - Logging process events and output
    - Graceful shutdown with timeout handling
    """
    
    def __init__(
        self,
        script_path: str = "arbitrage_engine.py",
        log_file: Optional[str] = None,
        log_level: int = logging.INFO,
        monitor_interval: float = 1.0,
        shutdown_timeout: float = 30.0
    ):
        """
        Initialize the arbitrage process manager.
        
        Args:
            script_path: Path to the arbitrage engine script to run
            log_file: Path to log file (if None, uses default path)
            log_level: Logging level for the manager logger
            monitor_interval: Interval (seconds) for checking process health
            shutdown_timeout: Maximum time to wait for graceful shutdown (seconds)
        """
        self.script_path = script_path
        self.monitor_interval = monitor_interval
        self.shutdown_timeout = shutdown_timeout
        
        # Process management
        self.process: Optional[subprocess.Popen] = None
        self.status = ProcessStatus.STOPPED
        self._status_lock = threading.Lock()
        
        # Monitoring
        self.monitor_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Statistics
        self.start_time: Optional[datetime] = None
        self.stop_time: Optional[datetime] = None
        self.restart_count = 0
        self.crash_count = 0
        
        # Setup logging
        self.logger = self._setup_logging(log_file, log_level)
    
    def _setup_logging(
        self,
        log_file: Optional[str],
        log_level: int
    ) -> logging.Logger:
        """
        Setup logging for the process manager.
        
        Args:
            log_file: Path to log file
            log_level: Logging level
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)
        
        # Create logs directory if needed
        if log_file is None:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_file = str(log_dir / "arbitrage_process.log")
        
        # File handler
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def _set_status(self, status: ProcessStatus) -> None:
        """
        Safely update process status.
        
        Args:
            status: New process status
        """
        with self._status_lock:
            old_status = self.status
            self.status = status
            if old_status != status:
                self.logger.info(
                    f"Process status changed: {old_status.value} -> {status.value}"
                )
    
    def get_status(self) -> ProcessStatus:
        """
        Get current process status.
        
        Returns:
            Current ProcessStatus
        """
        with self._status_lock:
            return self.status
    
    def is_running(self) -> bool:
        """
        Check if the process is currently running.
        
        Returns:
            True if process is running, False otherwise
        """
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def start(self, *args: str, **kwargs: Any) -> bool:
        """
        Start the arbitrage engine subprocess.
        
        Args:
            *args: Additional command-line arguments for the engine
            **kwargs: Additional keyword arguments for subprocess.Popen
            
        Returns:
            True if process started successfully, False otherwise
        """
        if self.is_running():
            self.logger.warning("Process is already running")
            return False
        
        self._set_status(ProcessStatus.STARTING)
        
        try:
            # Prepare command
            cmd = [
                "python",
                self.script_path,
                *args
            ]
            
            self.logger.info(f"Starting arbitrage engine: {' '.join(cmd)}")
            
            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                **kwargs
            )
            
            self.start_time = datetime.utcnow()
            self.restart_count += 1
            
            self.logger.info(
                f"Arbitrage engine process started (PID: {self.process.pid})"
            )
            
            # Start monitoring thread
            self._start_monitoring()
            
            self._set_status(ProcessStatus.RUNNING)
            return True
            
        except FileNotFoundError:
            self.logger.error(f"Script not found: {self.script_path}")
            self._set_status(ProcessStatus.FAILED)
            return False
        except Exception as e:
            self.logger.error(f"Failed to start process: {e}", exc_info=True)
            self._set_status(ProcessStatus.FAILED)
            return False
    
    def stop(self, timeout: Optional[float] = None) -> bool:
        """
        Stop the arbitrage engine subprocess gracefully.
        
        Args:
            timeout: Override default shutdown timeout (seconds)
            
        Returns:
            True if process stopped successfully, False otherwise
        """
        if not self.is_running():
            self.logger.warning("Process is not running")
            return True
        
        self._set_status(ProcessStatus.STOPPING)
        timeout = timeout or self.shutdown_timeout
        
        try:
            self.logger.info(
                f"Stopping arbitrage engine process (PID: {self.process.pid})"
            )
            
            # Attempt graceful shutdown with SIGTERM
            self.process.terminate()
            
            try:
                self.process.wait(timeout=timeout)
                self.logger.info("Process terminated gracefully")
            except subprocess.TimeoutExpired:
                self.logger.warning(
                    f"Process did not terminate within {timeout}s, forcing kill"
                )
                self.process.kill()
                self.process.wait()
                self.logger.info("Process killed forcefully")
            
            self.stop_time = datetime.utcnow()
            self._set_status(ProcessStatus.STOPPED)
            self._running = False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping process: {e}", exc_info=True)
            return False
    
    def restart(self, delay: float = 1.0, *args: str, **kwargs: Any) -> bool:
        """
        Restart the arbitrage engine process.
        
        Args:
            delay: Delay (seconds) between stop and start
            *args: Additional arguments for start()
            **kwargs: Additional keyword arguments for start()
            
        Returns:
            True if restart successful, False otherwise
        """
        self.logger.info("Restarting arbitrage engine process")
        
        if not self.stop():
            return False
        
        if delay > 0:
            time.sleep(delay)
        
        return self.start(*args, **kwargs)
    
    def _start_monitoring(self) -> None:
        """Start the process monitoring thread."""
        if self.monitor_thread is not None and self.monitor_thread.is_alive():
            return
        
        self._running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_process,
            daemon=True,
            name="ArbitrageProcessMonitor"
        )
        self.monitor_thread.start()
        self.logger.debug("Process monitoring thread started")
    
    def _monitor_process(self) -> None:
        """Monitor the process and detect crashes."""
        while self._running and self.is_running():
            time.sleep(self.monitor_interval)
        
        # Process has exited
        if self._running and self.process is not None:
            exit_code = self.process.returncode
            self.logger.warning(
                f"Process exited unexpectedly (exit code: {exit_code})"
            )
            self._set_status(ProcessStatus.CRASHED)
            self.crash_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get process statistics.
        
        Returns:
            Dictionary containing process statistics
        """
        uptime = None
        if self.start_time:
            if self.status == ProcessStatus.RUNNING:
                uptime = (datetime.utcnow() - self.start_time).total_seconds()
            elif self.stop_time:
                uptime = (self.stop_time - self.start_time).total_seconds()
        
        return {
            "status": self.status.value,
            "pid": self.process.pid if self.process else None,
            "running": self.is_running(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stop_time": self.stop_time.isoformat() if self.stop_time else None,
            "uptime_seconds": uptime,
            "restart_count": self.restart_count,
            "crash_count": self.crash_count,
        }
    
    def log_status(self) -> None:
        """Log current process status and statistics."""
        stats = self.get_stats()
        self.logger.info(f"Process Status: {stats}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


def main():
    """Example usage of ArbitrageProcessManager."""
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create manager instance
    manager = ArbitrageProcessManager(
        script_path="arbitrage_engine.py",
        log_file="logs/arbitrage_process.log",
        monitor_interval=2.0,
        shutdown_timeout=30.0
    )
    
    # Example: Start and monitor the process
    try:
        manager.start()
        
        # Keep monitoring for 60 seconds
        for _ in range(30):
            if manager.is_running():
                manager.log_status()
                time.sleep(2)
            else:
                manager.logger.warning("Process is not running!")
                break
        
    except KeyboardInterrupt:
        manager.logger.info("Interrupted by user")
    finally:
        manager.stop()
        manager.log_status()


if __name__ == "__main__":
    main()
