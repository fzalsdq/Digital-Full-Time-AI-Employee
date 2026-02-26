"""
Orchestrator Module

Main orchestration script for the AI Employee system.
Processes files in Needs_Action folder and updates the Dashboard.

Usage:
    python orchestrator.py [--vault-path PATH] [--interval SECONDS]

Example:
    python orchestrator.py --vault-path "C:/Users/Name/AI_Employee_Vault"
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import re


class Orchestrator:
    """
    Main orchestrator for the AI Employee system.
    
    Responsibilities:
    - Process files in Needs_Action folder
    - Update Dashboard.md with current status
    - Move completed files to Done folder
    - Generate daily summaries
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the orchestrator.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        
        # Define folders
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.logs = self.vault_path / 'Logs'
        self.briefings = self.vault_path / 'Briefings'
        self.dashboard = self.vault_path / 'Dashboard.md'
        
        # Ensure all folders exist
        for folder in [self.needs_action, self.done, self.plans, 
                       self.pending_approval, self.approved, self.rejected,
                       self.logs, self.briefings]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info(f'Orchestrator initialized')
        self.logger.info(f'Vault path: {self.vault_path}')
    
    def _setup_logging(self):
        """Configure logging."""
        import logging
        
        log_file = self.logs / f'orchestrator_{datetime.now().strftime("%Y-%m-%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Orchestrator')
    
    def get_needs_action_files(self) -> List[Path]:
        """Get all markdown files in Needs_Action folder."""
        if not self.needs_action.exists():
            return []
        
        files = list(self.needs_action.glob('*.md'))
        return sorted(files, key=lambda f: f.stat().st_mtime)
    
    def get_pending_approval_files(self) -> List[Path]:
        """Get all files pending approval."""
        if not self.pending_approval.exists():
            return []
        
        return list(self.pending_approval.glob('*.md'))
    
    def get_approved_files(self) -> List[Path]:
        """Get all approved files ready for action."""
        if not self.approved.exists():
            return []
        
        return list(self.approved.glob('*.md'))
    
    def count_completed_today(self) -> int:
        """Count files completed today."""
        if not self.done.exists():
            return 0
        
        today = datetime.now().strftime('%Y-%m-%d')
        count = 0
        
        for f in self.done.glob('*.md'):
            if today in f.name:
                count += 1
        
        return count
    
    def update_dashboard(self):
        """Update the Dashboard.md with current status."""
        if not self.dashboard.exists():
            self.logger.warning('Dashboard.md not found, creating new one')
            self._create_dashboard()
            return
        
        try:
            # Count items in each folder
            needs_action_count = len(self.get_needs_action_files())
            pending_approval_count = len(self.get_pending_approval_files())
            completed_today = self.count_completed_today()
            
            # Get lists of items
            needs_action_files = self.get_needs_action_files()
            pending_files = self.get_pending_approval_files()
            approved_files = self.get_approved_files()
            
            # Read current dashboard
            content = self.dashboard.read_text(encoding='utf-8')
            
            # Update timestamp
            content = re.sub(
                r'last_updated:.*',
                f'last_updated: {datetime.now().isoformat()}',
                content
            )
            
            # Update Quick Stats
            stats_table = f'''| Metric | Value |
|--------|-------|
| Pending Tasks | {needs_action_count} |
| In Progress | 0 |
| Completed Today | {completed_today} |
| Pending Approval | {pending_approval_count} |'''
            
            content = self._replace_section(
                content, 'Quick Stats', stats_table
            )
            
            # Update Needs Action section
            if needs_action_files:
                needs_action_list = '\n'.join([
                    f'- [ ] `{f.name}`' for f in needs_action_files[-5:]  # Last 5
                ])
                if len(needs_action_files) > 5:
                    needs_action_list += f'\n- *... and {len(needs_action_files) - 5} more*'
            else:
                needs_action_list = '*No items requiring attention*'
            
            content = self._replace_section(
                content, 'Needs Action', needs_action_list
            )
            
            # Update Pending Approval section
            if pending_files:
                pending_list = '\n'.join([
                    f'- [ ] `{f.name}`' for f in pending_files
                ])
            else:
                pending_list = '*No items awaiting approval*'
            
            content = self._replace_section(
                content, 'Pending Approval', pending_list
            )
            
            # Update System Status
            system_status = self._get_system_status()
            content = self._replace_section(
                content, 'System Status', system_status
            )
            
            # Update footer
            content = re.sub(
                r'\*Last generated:.*',
                f'*Last generated: {datetime.now().strftime("%Y-%m-%d")}*',
                content
            )
            
            # Write updated dashboard
            self.dashboard.write_text(content, encoding='utf-8')
            self.logger.info('Dashboard updated')
            
        except Exception as e:
            self.logger.error(f'Error updating dashboard: {e}', exc_info=True)
    
    def _replace_section(self, content: str, section_name: str, new_content: str) -> str:
        """Replace content under a section header."""
        # Find the section (handle both \n and \r\n line endings, and emojis)
        content = content.replace('\r\n', '\n')
        # Pattern matches "## " followed by any characters (including emojis) then the section name
        pattern = rf'(## [^\n]*{re.escape(section_name)}[^\n]*\n\n)(.*?)(\n---|\n## |\Z)'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            # Replace the section content
            start = match.start(2)
            end = match.end(2)
            content = content[:start] + new_content + content[end:]

        return content
    
    def _get_system_status(self) -> str:
        """Get current system status."""
        import psutil
        
        # Check if watcher processes are running
        watcher_running = self._is_process_running('filesystem_watcher')
        
        status_icon = lambda running: '🟢 Running' if running else '⚪ Not Running'
        
        return f'''| Component | Status |
|-----------|--------|
| File Watcher | {status_icon(watcher_running)} |
| Gmail Watcher | ⚪ Not Running |
| WhatsApp Watcher | ⚪ Not Running |
| Orchestrator | 🟢 Running |'''
    
    def _is_process_running(self, process_name: str) -> bool:
        """Check if a process is running."""
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if process_name.lower() in proc.info['name'].lower():
                    return True
        except Exception:
            pass
        return False
    
    def _create_dashboard(self):
        """Create a new Dashboard.md file."""
        content = f'''---
last_updated: {datetime.now().isoformat()}
status: active
---

# 📊 AI Employee Dashboard

## Quick Stats

| Metric | Value |
|--------|-------|
| Pending Tasks | 0 |
| In Progress | 0 |
| Completed Today | 0 |
| Pending Approval | 0 |

---

## 🔴 Needs Action

*No items requiring attention*

---

## 🟡 In Progress

*No active tasks*

---

## 🟢 Completed (Recent)

*No completed tasks yet*

---

## ⏸️ Pending Approval

*No items awaiting approval*

---

## 📈 Business Metrics

### Revenue This Week
- **Target:** $0
- **Actual:** $0

### Key Alerts
- *No alerts*

---

## 📋 Active Projects

| Project | Status | Due Date |
|---------|--------|----------|
| *None* | - | - |

---

## 🕐 System Status

| Component | Status |
|-----------|--------|
| File Watcher | ⚪ Not Running |
| Gmail Watcher | ⚪ Not Running |
| WhatsApp Watcher | ⚪ Not Running |
| Orchestrator | 🟢 Running |

---

*Last generated: {datetime.now().strftime("%Y-%m-%d")}*
*AI Employee v0.1 (Bronze Tier)*
'''
        self.dashboard.write_text(content, encoding='utf-8')
        self.logger.info('Created new Dashboard.md')
    
    def process_approved_files(self):
        """Process files that have been approved."""
        approved_files = self.get_approved_files()
        
        for filepath in approved_files:
            try:
                self.logger.info(f'Processing approved file: {filepath.name}')
                
                # Read the file to understand what action to take
                content = filepath.read_text(encoding='utf-8')
                
                # For Bronze tier, we just move to Done and log
                # Silver/Gold tiers would execute actual actions
                
                # Move to Done
                dest = self.done / filepath.name
                filepath.rename(dest)
                
                # Log the action
                self._log_action('approved_file_processed', {
                    'file': filepath.name,
                    'destination': str(dest)
                })
                
                self.logger.info(f'Moved to Done: {filepath.name}')
                
            except Exception as e:
                self.logger.error(f'Error processing approved file {filepath.name}: {e}', exc_info=True)
    
    def _log_action(self, action_type: str, details: dict):
        """Log an action to the audit log."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': 'orchestrator',
            **details
        }
        
        log_file = self.logs / f'orchestrator_{datetime.now().strftime("%Y-%m-%d")}.log'
        
        with open(log_file, 'a') as f:
            f.write(str(log_entry) + '\n')
    
    def generate_daily_summary(self):
        """Generate a daily summary of activities."""
        today = datetime.now().strftime('%Y-%m-%d')
        summary_file = self.briefings / f'Daily_Summary_{today}.md'
        
        if summary_file.exists():
            self.logger.info(f'Daily summary already exists: {today}')
            return
        
        # Count today's completed items
        completed_count = self.count_completed_today()
        
        content = f'''---
generated: {datetime.now().isoformat()}
date: {today}
type: daily_summary
---

# 📅 Daily Summary - {today}

## Overview

- **Files Processed:** {completed_count}
- **Pending Actions:** {len(self.get_needs_action_files())}
- **Pending Approvals:** {len(self.get_pending_approval_files())}

## Completed Today

'''
        # List completed files
        if self.done.exists():
            for f in self.done.glob(f'*{today}*.md'):
                content += f'- [x] `{f.name}`\n'
        
        content += f'''
## Notes

*Add any observations or notes about today's activities.*

---

*Generated by AI Employee Orchestrator v0.1*
'''
        
        summary_file.write_text(content, encoding='utf-8')
        self.logger.info(f'Generated daily summary: {summary_file}')
    
    def run(self):
        """Main run loop."""
        self.logger.info('Starting Orchestrator')
        self.logger.info('Press Ctrl+C to stop')
        
        last_dashboard_update = 0
        last_summary_check = 0
        
        try:
            while True:
                current_time = datetime.now().timestamp()
                
                # Update dashboard every 30 seconds
                if current_time - last_dashboard_update > 30:
                    self.update_dashboard()
                    last_dashboard_update = current_time
                
                # Process approved files
                self.process_approved_files()
                
                # Generate daily summary at midnight
                if current_time - last_summary_check > 3600:
                    self.generate_daily_summary()
                    last_summary_check = current_time
                
                # Wait before next check
                import time
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info('Orchestrator stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}', exc_info=True)
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI Employee Orchestrator - Bronze Tier',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    default_vault = os.environ.get(
        'AI_EMPLOYEE_VAULT',
        str(Path(__file__).parent.parent / 'AI_Employee_Vault')
    )
    
    parser.add_argument(
        '--vault-path',
        default=default_vault,
        help=f'Path to Obsidian vault (default: {default_vault})'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for testing)'
    )
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        print(f'Error: Vault path does not exist: {vault_path}')
        sys.exit(1)
    
    print(f'=' * 60)
    print('AI Employee - Orchestrator (Bronze Tier)')
    print(f'=' * 60)
    print(f'Vault Path: {vault_path}')
    print(f'Check Interval: {args.interval}s')
    print(f'=' * 60)
    
    orchestrator = Orchestrator(
        vault_path=str(vault_path),
        check_interval=args.interval
    )
    
    if args.once:
        print('Running once (test mode)...')
        orchestrator.update_dashboard()
        orchestrator.process_approved_files()
        print('Done!')
    else:
        print('Starting orchestration loop... Press Ctrl+C to stop.')
        print(f'=' * 60)
        orchestrator.run()


if __name__ == '__main__':
    main()
