# Zoho Mail MCP

Repo-local fallback plugin for Zoho Mail when no hosted connector or integration is available.

## What it does

- gives this repo a versioned local plugin scaffold
- defines an MCP-style server entry in `.mcp.json`
- adds a plugin skill so future Codex sessions can recognize the fallback path
- includes a real Python MCP server in `scripts/zoho_mail_local_server.py`
- supports account lookup, folder listing, draft creation, draft sending, and local draft-cache visibility

## What still needs to be done

1. refresh the local Zoho OAuth token if the current one has expired or been revoked
2. confirm the env source in `ZOHO_ENV_PATH` stays correct
3. install or expose this plugin through the desired Codex plugin loading path

## Current auth note

The plugin is wired to use the Fnomo emailer env file by default:

`D:\Antigravity\eigent\Downloads\fnomo\Images and content\fnomo_emailer\.env`

If Zoho auth fails, refresh the token with:

`D:\Antigravity\eigent\Downloads\fnomo\Images and content\fnomo_emailer\zoho_reauth.py`

## Current limitation

The plugin structure is working, but reliability still depends on a valid Zoho refresh token in the linked env file.
