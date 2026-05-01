---
name: zoho-mail-mcp
description: Use when Zoho Mail access is needed but no managed connector or integration is available, and Codex should use the local MCP-style Zoho Mail fallback plugin scaffold in this repo.
---

# Zoho Mail MCP

## Purpose

This plugin is a local fallback path for Zoho Mail work when the hosted connector is missing, under-scoped, or unavailable.

## Use Cases

1. Read drafts from `kush@mail.fnomo.com`
2. Create Zoho Mail drafts for Fnomo outreach
3. Search inbox replies from leads
4. Support a local MCP server path inside this repo

## Current State

This plugin is now wired to a real local Python server:

`./scripts/zoho_mail_local_server.py`

## Required Environment

The MCP config expects:

1. `ZOHO_MAIL_ADDRESS`
2. `ZOHO_CLIENT_ID`
3. `ZOHO_CLIENT_SECRET`
4. `ZOHO_REFRESH_TOKEN`
5. `ZOHO_ACCOUNT_ID`
6. `ZOHO_REGION`

By default, the plugin reads them from the Fnomo emailer env file referenced by `ZOHO_ENV_PATH`.

## Operator Rule

If the hosted Zoho connector works, prefer it.

If the hosted connector is unavailable or insufficiently scoped, use this plugin as the local fallback path.

If Zoho auth fails, refresh the token first with:

`D:\Antigravity\eigent\Downloads\fnomo\Images and content\fnomo_emailer\zoho_reauth.py`
