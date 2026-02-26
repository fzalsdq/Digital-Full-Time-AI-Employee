# Digital Full-Time AI Employee

## Project Overview

This is a **hackathon project** for building an autonomous "Digital FTE" (Full-Time Equivalent) - an AI agent that proactively manages personal and business affairs 24/7. The architecture is **local-first**, **agent-driven**, and implements **human-in-the-loop** safety mechanisms.

### Core Concept

Transform Qwen from a reactive chatbot into a proactive business partner that:
- Monitors Gmail, WhatsApp, and filesystems via "Watcher" scripts
- Uses Obsidian as a local knowledge base and GUI dashboard
- Executes actions through MCP (Model Context Protocol) servers
- Implements the "Ralph Wiggum" persistence pattern for multi-step task completion
- Generates "Monday Morning CEO Briefings" with revenue reports and bottleneck analysis

### Architecture Layers

| Layer | Components | Purpose |
|-------|------------|---------|
| **Perception** | Gmail Watcher, WhatsApp Watcher, Finance Watcher (Python scripts) | Monitor external inputs 24/7 |
| **Memory/GUI** | Obsidian Vault (Markdown files) | Local-first data storage and dashboard |
| **Reasoning** | Qwen | Primary reasoning engine |
| **Action** | MCP Servers (Email, Browser, Calendar, etc.) | Execute external actions |
| **Orchestration** | `orchestrator.py`, `watchdog.py` | Process management and scheduling |

## Directory Structure

```
Digital-Full-Time-AI-Employee/
├── Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md  # Main blueprint
├── skills-lock.json          # Skill dependencies
├── .qwen/skills/             # Agent skills
│   └── browsing-with-playwright/
│       ├── SKILL.md          # Skill documentation
│       ├── references/
│       │   └── playwright-tools.md
│       └── scripts/
│           ├── mcp-client.py
│           ├── start-server.sh
│           ├── stop-server.sh
│           └── verify.py
└── QWEN.md                   # This file
```

## Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| [Qwen](https://qwen.ai/) | Active subscription (only if required) | Reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Knowledge base & dashboard |
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts & orchestration |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers |
| [GitHub Desktop](https://desktop.github.com/download/) | Latest | Version control |

**Hardware:** Minimum 8GB RAM, 4-core CPU, 20GB free disk. Recommended: 16GB RAM, 8-core CPU, SSD.

## Building and Running

### Setup Checklist

```bash
# 1. Check Obsidian installation (install from https://obsidian.md/download if not present)

# 2. Create Obsidian vault structure
mkdir -p AI_Employee_Vault/{Inbox,Needs_Action,Done,Plans,Pending_Approval,Approved,Rejected,Logs,Accounting,Briefings}

# 3. Initialize Python environment (UV recommended)
uv init
uv add playwright google-api-python-client watchdog

# 4. Install Playwright browsers
playwright install

# 5. Start Playwright MCP server (for browser automation)
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh

# 6. Verify server
python3 .qwen/skills/browsing-with-playwright/scripts/verify.py
```

### Obsidian Vault Structure

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time summary (bank balance, pending tasks)
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Q1/Q2 objectives and metrics
├── Inbox/                    # Raw incoming items
├── Needs_Action/             # Items requiring Qwen's attention
├── Plans/                    # Generated action plans
├── Done/                     # Completed tasks
├── Pending_Approval/         # Awaiting human approval
├── Approved/                 # Approved actions (triggers execution)
├── Rejected/                 # Rejected actions
├── Logs/                     # Audit logs (YYYY-MM-DD.json)
├── Accounting/               # Bank transactions, invoices
└── Briefings/                # CEO briefings
```

### Running Watchers

```bash
# Gmail Watcher (monitors for new important emails)
python gmail_watcher.py

# WhatsApp Watcher (monitors for keywords like "urgent", "invoice")
python whatsapp_watcher.py

# Filesystem Watcher (monitors drop folders)
python filesystem_watcher.py

# Use PM2 for production (auto-restart on crash)
npm install -g pm2
pm2 start gmail_watcher.py --interpreter python3
pm2 save
pm2 startup
```

### Ralph Wiggum Loop (Persistence Pattern)

Keep Qwen working until task completion:

```bash
# Start Ralph loop
/ralph-loop "Process all files in /Needs_Action, move to /Done when complete" \
  --completion-promise "TASK_COMPLETE" \
  --max-iterations 10
```

### MCP Server Configuration

Configure MCP servers in your Qwen settings:

```json
{
  "servers": [
    {
      "name": "email",
      "command": "node",
      "args": ["/path/to/email-mcp/index.js"],
      "env": {
        "GMAIL_CREDENTIALS": "/path/to/credentials.json"
      }
    },
    {
      "name": "browser",
      "command": "npx",
      "args": ["@anthropic/browser-mcp"],
      "env": {
        "HEADLESS": "true"
      }
    }
  ]
}
```

## Development Conventions

### Security Principles

1. **Never commit credentials**: Use `.env` files (add to `.gitignore`)
2. **Environment variables**: `export GMAIL_API_KEY="your-key"`
3. **Dry-run mode**: All actions support `--dry-run` flag
4. **Human-in-the-loop**: Sensitive actions require file movement to `/Approved`
5. **Audit logging**: All actions logged to `/Logs/YYYY-MM-DD.json`

### Human-in-the-Loop Pattern

For sensitive actions (payments, emails to new contacts):

1. Qwen creates approval request in `/Pending_Approval/`
2. Human reviews and moves file to `/Approved` or `/Rejected`
3. Orchestrator detects approved file and executes MCP action
4. Result logged and files moved to `/Done`

### Approval Thresholds

| Action | Auto-Approve | Require Approval |
|--------|--------------|------------------|
| Email replies | Known contacts | New contacts, bulk sends |
| Payments | < $50 recurring | New payees, > $100 |
| Social media | Scheduled posts | Replies, DMs |
| File operations | Create, read | Delete, move outside vault |

### Coding Style

- **Watcher scripts**: Inherit from `BaseWatcher` abstract class
- **Retry logic**: Use `@with_retry` decorator for transient errors
- **Logging**: JSON format with timestamp, action_type, actor, result
- **Error handling**: Graceful degradation (queue locally, process when restored)

### Testing Practices

1. **Development mode**: Set `DEV_MODE=true` to prevent real actions
2. **Sandbox accounts**: Use test accounts for Gmail, banking
3. **Rate limiting**: Max 10 emails/hour, 3 payments/hour in dev
4. **Watchdog monitoring**: Auto-restart failed processes

## Key Files

| File | Purpose |
|------|---------|
| `Personal AI Employee Hackathon 0_...md` | Complete architectural blueprint and hackathon guide |
| `skills-lock.json` | Skill dependency tracking |
| `.qwen/skills/browsing-with-playwright/SKILL.md` | Browser automation skill documentation |
| `.qwen/skills/browsing-with-playwright/scripts/mcp-client.py` | MCP client for Playwright |

## Hackathon Tiers

| Tier | Time | Deliverables |
|------|------|--------------|
| **Bronze** | 8-12 hours | Dashboard.md, 1 Watcher, Qwen reading/writing to vault |
| **Silver** | 20-30 hours | 2+ Watchers, Plan.md generation, 1 MCP server, HITL workflow |
| **Gold** | 40+ hours | Full integration, Odoo accounting, multiple MCPs, weekly audit |
| **Platinum** | 60+ hours | Cloud deployment, specialization, A2A upgrade, production-ready |

## Common Commands

```bash
# Start all services
pm2 start orchestrator.py --interpreter python3
pm2 start gmail_watcher.py --interpreter python3
pm2 start whatsapp_watcher.py --interpreter python3

# View logs
pm2 logs orchestrator

# Stop all
pm2 stop all

# Check Playwright server status
pgrep -f "@playwright/mcp"

# Restart Playwright if needed
bash .qwen/skills/browsing-with-playwright/scripts/stop-server.sh
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Watchers stop overnight | Use PM2 or supervisord for process management |
| Gmail API 403 | Enable Gmail API in Google Cloud Console |
| MCP won't connect | Check server process: `ps aux | grep mcp` |
| Element not found (Playwright) | Run `browser_snapshot` first to get current refs |

## Resources

- **Qwen + Obsidian**: [YouTube](https://www.youtube.com/watch?v=sCIS05Qt79Y)
- **MCP Servers**: [GitHub](https://github.com/modelcontextprotocol/servers)
- **Odoo Integration**: [Documentation](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
- **Playwright**: [Docs](https://playwright.dev/python/docs/intro)

## Weekly Research Meeting

**When:** Wednesdays 10:00 PM PKT  
**Zoom:** [Join Meeting](https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1)  
**Meeting ID:** 871 8870 7642 | **Passcode:** 744832
