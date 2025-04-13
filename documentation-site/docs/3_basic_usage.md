---
sidebar_position: 3
---

# Step 2: Usage

In general, any MCP client that supports `stdio` protocol should work with this MCP server. This server was explicitly tested to work with:

- Cursor
- Windsurf
- Cline
- Claude Desktop

Additionally, you can also use smithery.ai to install this server a number of clients, including the ones above.

Follow the guides below to install this MCP server in your client.

## Cursor

Go to Settings -> Features -> MCP Servers and add a new server with this configuration:

```json
{
  "mcpServers": {
    "chatty": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/users/chatty-mcp",
        "run",
        "chatty.py",
        "--kokoro",
        "--speed",
        "1.5",
        "--volume",
        "0.8"
      ]
    }
  }
}
```

If configuration is correct, you should see a green dot indicator and the number of tools exposed by the server.

![How successful Cursor config looks like](https://github.com/user-attachments/assets/45df080a-8199-4aca-b59c-a84dc7fe2c09)


## Cline
Cline also supports MCP servers through a similar JSON configuration. Follow these steps to set up the Supabase MCP server:

1. **Find the full path to the executable** (this step is critical):

   ```bash
   # On macOS/Linux
   which supabase-mcp-server

   # On Windows
   where supabase-mcp-server
   ```
   Copy the full path that is returned (e.g., `/Users/username/.local/bin/supabase-mcp-server`).

2. **Configure the MCP server** in Cline:

   - Open Cline in VS Code
   - Click on the "MCP Servers" tab in the Cline sidebar
   - Click "Configure MCP Servers"
   - This will open the `cline_mcp_settings.json` file
   - Add the following configuration:

   ```json
   {
     "mcpServers": {
       "supabase": {
         "command": "/full/path/to/supabase-mcp-server",  // Replace with the actual path from step 1
         "env": {
           "QUERY_API_KEY": "your-api-key",  // Required - get your API key at thequery.dev
           "SUPABASE_PROJECT_REF": "your-project-ref",
           "SUPABASE_DB_PASSWORD": "your-db-password",
           "SUPABASE_REGION": "us-east-1",  // optional, defaults to us-east-1
           "SUPABASE_ACCESS_TOKEN": "your-access-token",  // optional, for management API
           "SUPABASE_SERVICE_ROLE_KEY": "your-service-role-key"  // optional, for Auth Admin SDK
         }
       }
     }
   }
   ```

If configuration is correct, you should see a green indicator next to the Supabase MCP server in the Cline MCP Servers list, and a message confirming "supabase MCP server connected" at the bottom of the panel.

![How successful configuration in Cline looks like](https://github.com/user-attachments/assets/6c4446ad-7a58-44c6-bf12-6c82222bbe59)


## Windsurf
Go to Cascade -> Click on the hammer icon -> Configure -> Fill in the configuration:
```json
{
    "mcpServers": {
      "supabase": {
        "command": "/Users/username/.local/bin/supabase-mcp-server",  // update path
        "env": {
          "QUERY_API_KEY": "your-api-key",  // Required - get your API key at thequery.dev
          "SUPABASE_PROJECT_REF": "your-project-ref",
          "SUPABASE_DB_PASSWORD": "your-db-password",
          "SUPABASE_REGION": "us-east-1",  // optional, defaults to us-east-1
          "SUPABASE_ACCESS_TOKEN": "your-access-token",  // optional, for management API
          "SUPABASE_SERVICE_ROLE_KEY": "your-service-role-key"  // optional, for Auth Admin SDK
        }
      }
    }
}
```
If configuration is correct, you should see green dot indicator and clickable supabase server in the list of available servers.

![How successful Windsurf config looks like](https://github.com/user-attachments/assets/322b7423-8c71-410b-bcab-aff1b143faa4)

## Claude Desktop

Claude Desktop also supports MCP servers through a JSON configuration. Follow these steps to set up the Supabase MCP server:

1. **Find the full path to the executable** (this step is critical):
   ```bash
   # On macOS/Linux
   which supabase-mcp-server

   # On Windows
   where supabase-mcp-server
   ```
   Copy the full path that is returned (e.g., `/Users/username/.local/bin/supabase-mcp-server`).

2. **Configure the MCP server** in Claude Desktop:
   - Open Claude Desktop
   - Go to Settings → Developer -> Edit Config MCP Servers
   - Add a new configuration with the following JSON:

   ```json
   {
     "mcpServers": {
       "supabase": {
         "command": "/full/path/to/supabase-mcp-server",  // Replace with the actual path from step 1
         "env": {
           "QUERY_API_KEY": "your-api-key",  // Required - get your API key at thequery.dev
           "SUPABASE_PROJECT_REF": "your-project-ref",
           "SUPABASE_DB_PASSWORD": "your-db-password",
           "SUPABASE_REGION": "us-east-1",  // optional, defaults to us-east-1
           "SUPABASE_ACCESS_TOKEN": "your-access-token",  // optional, for management API
           "SUPABASE_SERVICE_ROLE_KEY": "your-service-role-key"  // optional, for Auth Admin SDK
         }
       }
     }
   }
   ```

> ⚠️ **Important**: Unlike Windsurf and Cursor, Claude Desktop requires the **full absolute path** to the executable. Using just the command name (`supabase-mcp-server`) will result in a "spawn ENOENT" error.

If configuration is correct, you should see the Supabase MCP server listed as available in Claude Desktop.

![How successful Windsurf config looks like](https://github.com/user-attachments/assets/500bcd40-6245-40a7-b23b-189827ed2923)
