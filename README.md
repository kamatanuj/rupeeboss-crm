# Rupeeboss CRM

Lead management system for Rupeeboss voice agent.

## Features
- Lead extraction from D-insights API
- Auto-updates every hour via cron
- Static site deployment to Cloudflare Pages
- Local dashboard at localhost:3002

## Setup

1. Copy `.env.example` to `.env`
2. Add your credentials
3. Run `python3 extract-leads.py` to extract leads

## Live URLs
- **Live CRM:** https://rupeeboss-crm.pages.dev
- **Local Dashboard:** http://localhost:3002

## Auto-Update
Add to crontab: `0 * * * * /path/to/rupeeboss/auto-update.sh`
