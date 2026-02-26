"""
AI Employee - Bronze Tier Runner

Runs both the Filesystem Watcher and Orchestrator together.
Updates dashboard automatically when new files are detected.

Usage:
    python run_bronze_tier.py [--vault-path PATH] [--watch-path PATH]
"""

import os
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from filesystem_watcher import FilesystemWatcher
from orchestrator import Orchestrator


class BronzeTierRunner:
    """Runs the complete Bronze Tier system."""
    
    def __init__(self, vault_path: str, watch_path: str, check_interval: int = 5):
        self.vault_path = Path(vault_path)
        self.watch_path = Path(watch_path)
        self.check_interval = check_interval
        
        # Initialize watcher and orchestrator
        self.watcher = FilesystemWatcher(
            vault_path=vault_path,
            watch_path=watch_path,
            check_interval=check_interval
        )
        
        self.orchestrator = Orchestrator(
            vault_path=vault_path,
            check_interval=check_interval
        )
        
        print(f"=" * 70)
        print("AI Employee - Bronze Tier")
        print(f"=" * 70)
        print(f"Vault Path:       {vault_path}")
        print(f"Watch Path:       {watch_path}")
        print(f"Check Interval:   {check_interval}s")
        print(f"=" * 70)
        print("Starting AI Employee system...")
        print("- Filesystem Watcher: Monitoring for new files")
        print("- Orchestrator: Updating dashboard")
        print(f"=" * 70)
        print("Press Ctrl+C to stop")
        print(f"=" * 70)
    
    def run(self):
        """Main run loop."""
        last_orchestrator_update = 0
        
        try:
            while True:
                current_time = time.time()
                
                # Check for new files
                items = self.watcher.check_for_updates()
                
                if items:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Found {len(items)} new file(s)")
                    for item in items:
                        filepath = self.watcher.create_action_file(item)
                        if filepath:
                            print(f"  ✓ Created: {filepath.name}")
                    
                    # Update dashboard immediately after new files
                    self.orchestrator.update_dashboard()
                
                # Update dashboard periodically (every 30 seconds)
                if current_time - last_orchestrator_update > 30:
                    self.orchestrator.update_dashboard()
                    last_orchestrator_update = current_time
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping AI Employee system...")
            self.watcher.logger.info('Stopped by user')


def main():
    parser = argparse.ArgumentParser(
        description='AI Employee - Bronze Tier Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    default_vault = os.environ.get(
        'AI_EMPLOYEE_VAULT',
        str(Path(__file__).parent.parent / 'AI_Employee_Vault')
    )
    
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
        default=5,
        help='Check interval in seconds (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Validate paths
    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        print(f'Error: Vault path does not exist: {vault_path}')
        sys.exit(1)
    
    watch_path = Path(args.watch_path)
    watch_path.mkdir(parents=True, exist_ok=True)
    
    runner = BronzeTierRunner(
        vault_path=str(vault_path),
        watch_path=str(watch_path),
        check_interval=args.interval
    )
    
    runner.run()


if __name__ == '__main__':
    main()
