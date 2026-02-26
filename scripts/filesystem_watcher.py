"""
Filesystem Watcher Module

Monitors a drop folder for new files and creates action files in the Needs_Action folder.
This is the Bronze tier watcher - simple file-based triggering for the AI Employee.

Usage:
    python filesystem_watcher.py [--vault-path PATH] [--watch-path PATH] [--interval SECONDS]

Example:
    python filesystem_watcher.py --vault-path "C:/Users/Name/AI_Employee_Vault" --watch-path "C:/Users/Name/DropFolder"
"""

import os
import sys
import shutil
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher


class FileDropItem:
    """Represents a file dropped into the watch folder."""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.name = filepath.name
        self.size = filepath.stat().st_size
        self.created = datetime.fromtimestamp(filepath.stat().st_ctime)
        self.modified = datetime.fromtimestamp(filepath.stat().st_mtime)
        self.content_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute MD5 hash of file content."""
        try:
            with open(self.filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return 'unknown'
    
    def get_content_preview(self, max_lines: int = 20) -> str:
        """Get a preview of the file content."""
        try:
            # Try to read as text
            with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[:max_lines]
                content = ''.join(lines)
                
                # Truncate if too long
                if len(content) > 5000:
                    content = content[:5000] + '\n\n... [content truncated]'
                
                return content
        except Exception as e:
            return f'[Could not read file content: {e}]'


class FilesystemWatcher(BaseWatcher):
    """
    Watches a folder for new files and creates action files.
    
    Files dropped into the watch folder are copied to the vault
    and an action file is created in Needs_Action.
    """
    
    def __init__(
        self,
        vault_path: str,
        watch_path: str,
        check_interval: int = 30,
        move_to_vault: bool = True
    ):
        """
        Initialize the filesystem watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            watch_path: Path to the folder to watch for new files
            check_interval: Seconds between checks (default: 30)
            move_to_vault: If True, move files to vault; if False, copy
        """
        super().__init__(vault_path, check_interval)
        
        self.watch_path = Path(watch_path)
        self.move_to_vault = move_to_vault
        self.processed_files: Dict[str, str] = {}  # filename -> hash
        
        # Create watch folder if it doesn't exist
        self.watch_path.mkdir(parents=True, exist_ok=True)
        
        # Create Files subfolder in vault for dropped files
        self.files_dir = self.vault_path / 'Files'
        self.files_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f'Watch path: {self.watch_path}')
        self.logger.info(f'Move to vault: {self.move_to_vault}')
        
        # Load already processed files on startup
        self._load_processed_files()
    
    def _load_processed_files(self):
        """Load hashes of already processed files to avoid reprocessing."""
        state_file = self.vault_path / '.filesystem_watcher_state.json'
        if state_file.exists():
            try:
                import json
                with open(state_file, 'r') as f:
                    self.processed_files = json.load(f)
                self.logger.info(f'Loaded {len(self.processed_files)} previously processed files')
            except Exception as e:
                self.logger.warning(f'Could not load state file: {e}')
    
    def _save_state(self):
        """Save processed files state."""
        state_file = self.vault_path / '.filesystem_watcher_state.json'
        try:
            import json
            with open(state_file, 'w') as f:
                json.dump(self.processed_files, f, indent=2)
        except Exception as e:
            self.logger.warning(f'Could not save state file: {e}')
    
    def check_for_updates(self) -> List[FileDropItem]:
        """
        Check the watch folder for new files.
        
        Returns:
            List of new FileDropItem objects
        """
        new_items = []
        
        if not self.watch_path.exists():
            self.logger.warning(f'Watch path does not exist: {self.watch_path}')
            return []
        
        # Get all files in watch folder (not subdirectories)
        for filepath in self.watch_path.iterdir():
            if filepath.is_file() and not filepath.name.startswith('.'):
                item = FileDropItem(filepath)
                
                # Check if already processed
                if item.name in self.processed_files:
                    if self.processed_files[item.name] == item.content_hash:
                        self.logger.debug(f'Skipping already processed: {item.name}')
                        continue
                
                new_items.append(item)
                self.logger.info(f'New file detected: {item.name} ({item.size} bytes)')
        
        return new_items
    
    def create_action_file(self, item: FileDropItem) -> Optional[Path]:
        """
        Create an action file for the dropped file.
        
        Args:
            item: The FileDropItem to create an action file for
            
        Returns:
            Path to the created action file
        """
        try:
            # Get content preview BEFORE moving the file
            content_preview = item.get_content_preview()
            
            # Copy or move file to vault
            if self.move_to_vault:
                dest_path = self.files_dir / item.name
                shutil.move(str(item.filepath), str(dest_path))
                self.logger.info(f'Moved file to vault: {dest_path}')
            else:
                dest_path = self.files_dir / item.name
                shutil.copy2(str(item.filepath), str(dest_path))
                self.logger.info(f'Copied file to vault: {dest_path}')
            
            # Determine file type based on extension
            file_type = self._get_file_type(item.name)
            
            # Create action file
            filename = self.generate_filename('FILE', item.name)
            filepath = self.needs_action / filename
            
            frontmatter = self.create_frontmatter(
                item_type='file_drop',
                original_name=f'"{item.name}"',
                file_path=f'"{str(dest_path)}"',
                file_size=item.size,
                file_hash=f'"{item.content_hash}"',
                file_type=f'"{file_type}"'
            )
            
            content = f'''{frontmatter}

## File Information

- **Original Name:** {item.name}
- **Size:** {self._format_size(item.size)}
- **Created:** {item.created.strftime("%Y-%m-%d %H:%M:%S")}
- **Modified:** {item.modified.strftime("%Y-%m-%d %H:%M:%S")}
- **Vault Location:** `{dest_path}`

## Content Preview

```
{content_preview}
```

## Suggested Actions

- [ ] Review file content
- [ ] Categorize file
- [ ] Take required action
- [ ] Move to appropriate folder
- [ ] Mark as done

## Notes

*Add any notes about processing this file here.*
'''
            
            filepath.write_text(content, encoding='utf-8')
            
            # Update processed files tracking
            self.processed_files[item.name] = item.content_hash
            self._save_state()
            
            # Log the action
            self.log_action('file_processed', {
                'original_file': item.name,
                'vault_file': str(dest_path),
                'action_file': str(filepath),
                'size': item.size
            })
            
            return filepath
            
        except Exception as e:
            self.logger.error(f'Error creating action file for {item.name}: {e}', exc_info=True)
            return None
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type based on extension."""
        ext = Path(filename).suffix.lower()
        
        type_map = {
            '.pdf': 'PDF Document',
            '.doc': 'Word Document',
            '.docx': 'Word Document',
            '.xls': 'Excel Spreadsheet',
            '.xlsx': 'Excel Spreadsheet',
            '.csv': 'CSV Data',
            '.txt': 'Text File',
            '.md': 'Markdown',
            '.jpg': 'Image',
            '.jpeg': 'Image',
            '.png': 'Image',
            '.gif': 'Image',
            '.zip': 'Archive',
            '.rar': 'Archive',
            '.7z': 'Archive',
        }
        
        return type_map.get(ext, 'Unknown')
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} TB'


def main():
    """Main entry point for the filesystem watcher."""
    parser = argparse.ArgumentParser(
        description='Filesystem Watcher for AI Employee - Bronze Tier',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python filesystem_watcher.py
  python filesystem_watcher.py --vault-path "C:/Vault" --watch-path "C:/DropFolder"
  python filesystem_watcher.py --interval 60
        '''
    )
    
    # Get vault path from environment or use default
    default_vault = os.environ.get(
        'AI_EMPLOYEE_VAULT',
        str(Path(__file__).parent.parent / 'AI_Employee_Vault')
    )
    
    # Get watch path from environment or use default
    default_watch = os.environ.get(
        'AI_EMPLOYEE_WATCH_FOLDER',
        str(Path(__file__).parent.parent / 'AI_Employee_Vault' / 'Inbox')
    )
    
    parser.add_argument(
        '--vault-path',
        default=default_vault,
        help=f'Path to Obsidian vault (default: {default_vault})'
    )
    parser.add_argument(
        '--watch-path',
        default=default_watch,
        help=f'Path to watch folder (default: {default_watch})'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Check interval in seconds (default: 30)'
    )
    parser.add_argument(
        '--copy-only',
        action='store_true',
        help='Copy files instead of moving them'
    )
    
    args = parser.parse_args()
    
    # Validate paths
    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        print(f'Error: Vault path does not exist: {vault_path}')
        print('Please create the vault directory first.')
        sys.exit(1)
    
    watch_path = Path(args.watch_path)
    watch_path.mkdir(parents=True, exist_ok=True)
    
    print(f'=' * 60)
    print('AI Employee - Filesystem Watcher (Bronze Tier)')
    print(f'=' * 60)
    print(f'Vault Path:    {vault_path}')
    print(f'Watch Path:    {watch_path}')
    print(f'Check Interval: {args.interval}s')
    print(f'Move Files:    {not args.copy_only}')
    print(f'=' * 60)
    print('Watching for new files... Press Ctrl+C to stop.')
    print(f'=' * 60)
    
    # Create and run watcher
    watcher = FilesystemWatcher(
        vault_path=str(vault_path),
        watch_path=str(watch_path),
        check_interval=args.interval,
        move_to_vault=not args.copy_only
    )
    
    watcher.run()


if __name__ == '__main__':
    main()
