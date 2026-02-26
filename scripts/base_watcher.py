"""
Base Watcher Module

Abstract base class for all watcher scripts in the AI Employee system.
All watchers inherit from this class and implement check_for_updates() and create_action_file().
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Any, Optional


class BaseWatcher(ABC):
    """
    Abstract base class for AI Employee watchers.
    
    Watchers monitor external sources (email, files, APIs) and create
    action files in the Needs_Action folder for Qwen to process.
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.logs_dir = self.vault_path / 'Logs'
        self.check_interval = check_interval
        
        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Track processed items to avoid duplicates
        self.processed_ids: set = set()
        
        self.logger.info(f'{self.__class__.__name__} initialized')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {check_interval}s')
    
    def _setup_logging(self):
        """Configure logging for the watcher."""
        log_file = self.logs_dir / f'{datetime.now().strftime("%Y-%m-%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def check_for_updates(self) -> List[Any]:
        """
        Check the external source for new items.
        
        Returns:
            List of new items to process
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item: Any) -> Optional[Path]:
        """
        Create an action file in the Needs_Action folder.
        
        Args:
            item: The item to create an action file for
            
        Returns:
            Path to the created file, or None if failed
        """
        pass
    
    def generate_filename(self, prefix: str, unique_id: str) -> str:
        """
        Generate a standardized filename.
        
        Args:
            prefix: File type prefix (e.g., 'EMAIL', 'FILE', 'TASK')
            unique_id: Unique identifier for the item
            
        Returns:
            Formatted filename with .md extension
        """
        timestamp = datetime.now().strftime('%Y-%m-%d')
        # Sanitize unique_id for filesystem
        safe_id = ''.join(c.lower() if c.isalnum() else '_' for c in unique_id[:50])
        return f'{prefix}_{safe_id}_{timestamp}.md'
    
    def create_frontmatter(self, item_type: str, **kwargs) -> str:
        """
        Create YAML frontmatter for action files.
        
        Args:
            item_type: Type of item (email, file, task, etc.)
            **kwargs: Additional metadata fields
            
        Returns:
            Formatted YAML frontmatter string
        """
        frontmatter = [
            '---',
            f'type: {item_type}',
            f'created: {datetime.now().isoformat()}',
            'status: pending',
        ]
        
        for key, value in kwargs.items():
            frontmatter.append(f'{key}: {value}')
        
        frontmatter.append('---')
        return '\n'.join(frontmatter)
    
    def log_action(self, action_type: str, details: dict):
        """
        Log an action to the audit log.
        
        Args:
            action_type: Type of action performed
            details: Dictionary of action details
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': self.__class__.__name__,
            **details
        }
        
        log_file = self.logs_dir / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        
        # Append to log file (simple implementation - could use proper JSON Lines)
        with open(log_file, 'a') as f:
            f.write(str(log_entry) + '\n')
    
    def run(self):
        """
        Main run loop for the watcher.
        
        Continuously checks for updates and creates action files.
        Runs until interrupted (Ctrl+C).
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info('Press Ctrl+C to stop')
        
        try:
            while True:
                try:
                    # Check for new items
                    items = self.check_for_updates()
                    
                    if items:
                        self.logger.info(f'Found {len(items)} new item(s)')
                        
                        for item in items:
                            filepath = self.create_action_file(item)
                            if filepath:
                                self.logger.info(f'Created action file: {filepath.name}')
                                self.log_action('action_file_created', {
                                    'file': str(filepath),
                                    'item_type': type(item).__name__
                                })
                    else:
                        self.logger.debug('No new items')
                    
                except Exception as e:
                    self.logger.error(f'Error processing items: {e}', exc_info=True)
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}', exc_info=True)
            raise


if __name__ == '__main__':
    # This is an abstract class - cannot be instantiated directly
    print('BaseWatcher is an abstract class. Inherit from it to create specific watchers.')
    print('Example: class FilesystemWatcher(BaseWatcher)')
