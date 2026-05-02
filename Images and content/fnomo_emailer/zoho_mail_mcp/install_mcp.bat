@echo off
echo ============================================================
echo   FNOMO -- Zoho Mail MCP Server Installer
echo ============================================================
echo.
echo Installing Python dependencies...
pip install fastmcp requests python-dotenv --break-system-packages
echo.
echo Done. Now restart Claude desktop to load the MCP.
echo.
echo After restart, Claude will have these tools available:
echo   zoho_create_draft  - Save draft to Zoho Drafts folder
echo   zoho_list_drafts   - List drafts in Zoho
echo   zoho_send_draft    - Send an existing draft
echo   zoho_list_folders  - List all Zoho mail folders
echo   zoho_get_token     - Debug: check current auth token
echo.
pause
