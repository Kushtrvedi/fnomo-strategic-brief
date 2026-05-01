# Zoho Mail MCP

Repo-local fallback plugin for Zoho Mail when no hosted connector or integration is available.

## What it does

- gives this repo a versioned local plugin scaffold
- defines an MCP-style server entry in `.mcp.json`
- adds a plugin skill so future Codex sessions can recognize the fallback path

## What still needs to be done

1. add real Zoho OAuth app credentials
2. store a valid `ZOHO_REFRESH_TOKEN`
3. implement the local server logic in `scripts/zoho-mail-local-server.mjs`
4. install or expose this plugin through the desired Codex plugin loading path

## Current limitation

This plugin is scaffolded but not yet a working mail integration.

It exists so the Fnomo repo has a GitHub-backed MCP fallback path instead of relying only on a hosted connector.
