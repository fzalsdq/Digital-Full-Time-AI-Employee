# AI Employee - Bronze Tier

> **Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

This is the **Bronze Tier** implementation of the Personal AI Employee hackathon project. It provides the foundational layer for an autonomous AI agent that proactively manages personal and business affairs using file-based triggering.

## 📋 What's Included

| Component | Status | Description |
|-----------|--------|-------------|
| **Obsidian Vault** | ✅ | Local Markdown knowledge base with Dashboard, Company Handbook, and Business Goals |
| **Folder Structure** | ✅ | Organized folders for Inbox, Needs_Action, Done, Plans, etc. |
| **Filesystem Watcher** | ✅ | Monitors a drop folder for new files and creates action items |
| **Orchestrator** | ✅ | Processes action files and updates the Dashboard |
| **Base Watcher Class** | ✅ | Abstract class for building additional watchers |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Employee (Bronze Tier)                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌──────────────────────────────────────┐
│   Drop Folder   │────▶│     Filesystem Watcher (Python)      │
│  (Inbox/files)  │     │  - Detects new files                 │
└─────────────────┘     │  - Creates action files              │
                        └──────────────────────────────────────┘
                                          │
                                          ▼
                        ┌──────────────────────────────────────┐
                        │         Obsidian Vault               │
                        │  /Needs_Action/*.md                  │
                        │  /Done/*.md                          │
                        │  Dashboard.md                        │
                        │  Company_Handbook.md                 │
                        │  Business_Goals.md                   │
                        └──────────────────────────────────────┘
                                          │
                                          ▼
                        ┌──────────────────────────────────────┐
                        │        Orchestrator (Python)         │
                        │  - Updates Dashboard                 │
                        │  - Processes approved files          │
                        │  - Generates daily summaries         │
                        └──────────────────────────────────────┘
                                          │
                                          ▼
                        ┌──────────────────────────────────────┐
                        │           Qwen (AI Agent)            │
                        │  - Reads action files                │
                        │  - Creates plans                     │
                        │  - Writes results to Done            │
                        └──────────────────────────────────────┘
```

## 📁 Vault Structure

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time status dashboard
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Objectives and metrics
├── Inbox/                    # Drop folder for new files
├── Needs_Action/             # Action items for Qwen
├── Plans/                    # Generated action plans
├── Done/                     # Completed tasks
├── Pending_Approval/         # Awaiting human approval
├── Approved/                 # Approved for execution
├── Rejected/                 # Rejected items
├── Logs/                     # Audit logs
├── Briefings/                # Daily/weekly summaries
└── Files/                    # Processed files storage
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+** - [Download](https://www.python.org/downloads/)
- **Obsidian** - [Download](https://obsidian.md/download)
- **Qwen** - AI reasoning engine

### Installation

1. **Clone or download this project**

2. **Install Python dependencies**
   ```bash
   cd scripts
   pip install -r requirements.txt
   ```

3. **Open Obsidian**
   - Open Obsidian
   - Click "Open folder as vault"
   - Select the `AI_Employee_Vault` folder

4. **Verify setup**
   ```bash
   python orchestrator.py --once
   ```

### Running the Bronze Tier

#### Option 1: Run in Terminal (Development)

Open two terminal windows:

**Terminal 1 - Start the Filesystem Watcher:**
```bash
cd scripts
python filesystem_watcher.py
```

**Terminal 2 - Start the Orchestrator:**
```bash
cd scripts
python orchestrator.py
```

#### Option 2: Run in Background (Production)

Using PM2 (recommended for always-on operation):

```bash
# Install PM2
npm install -g pm2

# Start Filesystem Watcher
pm2 start scripts/filesystem_watcher.py --name "ai-file-watcher" --interpreter python3

# Start Orchestrator
pm2 start scripts/orchestrator.py --name "ai-orchestrator" --interpreter python3

# Save process list for auto-start on reboot
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

#### Option 3: Windows Task Scheduler

For Windows users who want the watcher to start on login:

1. Open Task Scheduler
2. Create a new task:
   - **Trigger:** At log on
   - **Action:** `python.exe` with arguments `"E:\path\to\scripts\filesystem_watcher.py"`
   - **Settings:** Run whether user is logged on or not

## 📖 Usage

### How It Works

1. **Drop a file** into the `AI_Employee_Vault/Inbox` folder (or your configured watch folder)

2. **Filesystem Watcher detects** the new file and:
   - Copies/moves it to `AI_Employee_Vault/Files/`
   - Creates an action file in `AI_Employee_Vault/Needs_Action/`

3. **Orchestrator updates** the Dashboard.md with the new pending item

4. **Qwen processes** the action file:
   - Reads the file content
   - Creates a plan in `Plans/`
   - Executes the required actions
   - Moves completed items to `Done/`

5. **Dashboard updates** automatically showing completed tasks

### Example: Processing a Document

1. Save a contract PDF to `AI_Employee_Vault/Inbox/contract.pdf`

2. Watcher creates `Needs_Action/FILE_contract_pdf_2026-02-26.md`:
   ```markdown
   ---
   type: file_drop
   original_name: "contract.pdf"
   file_path: "Files/contract.pdf"
   file_size: 245678
   status: pending
   ---

   ## File Information
   - **Original Name:** contract.pdf
   - **Size:** 240.0 KB
   - **Vault Location:** `Files/contract.pdf`

   ## Suggested Actions
   - [ ] Review file content
   - [ ] Categorize file
   - [ ] Take required action
   - [ ] Mark as done
   ```

3. Qwen reads the action file and processes the contract

4. After completion, file moves to `Done/`

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_EMPLOYEE_VAULT` | Path to Obsidian vault | `./AI_Employee_Vault` |
| `AI_EMPLOYEE_WATCH_FOLDER` | Folder to watch for files | `./AI_Employee_Vault/Inbox` |

### Command-Line Options

#### Filesystem Watcher

```bash
python filesystem_watcher.py [OPTIONS]

Options:
  --vault-path PATH     Path to Obsidian vault
  --watch-path PATH     Path to watch folder
  --interval SECONDS    Check interval (default: 30)
  --copy-only           Copy files instead of moving
```

#### Orchestrator

```bash
python orchestrator.py [OPTIONS]

Options:
  --vault-path PATH     Path to Obsidian vault
  --interval SECONDS    Check interval (default: 60)
  --once                Run once and exit (for testing)
```

## 🧪 Testing

### Test the Setup

1. **Run orchestrator in test mode:**
   ```bash
   python orchestrator.py --once
   ```

2. **Drop a test file:**
   ```bash
   echo "Test content" > AI_Employee_Vault/Inbox/test_document.txt
   ```

3. **Start the watcher** (in a separate terminal):
   ```bash
   python filesystem_watcher.py --interval 5
   ```

4. **Check the Needs_Action folder** for a new action file

5. **Check Dashboard.md** for updated stats

### Verify Installation

```bash
# Check Python version
python --version  # Should be 3.13+

# Check dependencies
pip list | grep -E "watchdog|psutil"

# Test watcher import
python -c "from scripts.base_watcher import BaseWatcher; print('OK')"
```

## 📝 Configuration

### Company Handbook

Edit `AI_Employee_Vault/Company_Handbook.md` to customize:
- Approval thresholds
- Priority classifications
- Communication guidelines
- Error handling rules

### Business Goals

Edit `AI_Employee_Vault/Business_Goals.md` to set:
- Revenue targets
- Key metrics
- Active projects
- Weekly targets

### Dashboard

The Dashboard.md auto-updates, but you can customize:
- Additional metrics sections
- Custom alerts
- Project tracking tables

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Watcher doesn't detect files | Check watch folder path, ensure files don't start with `.` |
| Dashboard not updating | Run `orchestrator.py --once` to test |
| Permission errors | Run as administrator or check folder permissions |
| Python import errors | Run `pip install -r requirements.txt` |

## 📊 Logs

Logs are stored in:
- `AI_Employee_Vault/Logs/` - Application logs
- `AI_Employee_Vault/Logs/orchestrator_*.log` - Orchestrator-specific logs

View recent logs:
```bash
tail -f AI_Employee_Vault/Logs/orchestrator_2026-02-26.log
```

## 🎯 Next Steps (Silver Tier)

After mastering Bronze tier, consider adding:
- [ ] Gmail Watcher for email monitoring
- [ ] WhatsApp Watcher for message monitoring
- [ ] MCP servers for external actions
- [ ] Human-in-the-loop approval workflow
- [ ] Scheduled tasks via cron/Task Scheduler

## 📄 License

This project is part of the Personal AI Employee Hackathon 0.

## 🤝 Support

- **Weekly Research Meeting:** Wednesdays 10:00 PM PKT
- **Zoom:** [Join Meeting](https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1)
- **Documentation:** See main hackathon document

---

*AI Employee v0.1 (Bronze Tier) - Built with ❤️ for the Personal AI Employee Hackathon 0*
