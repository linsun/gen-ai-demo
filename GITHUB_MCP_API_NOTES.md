# GitHub MCP Server API Usage Notes

This document contains important notes about using the GitHub MCP server with the correct API tools and parameters.

## Correct Tool Names

### ✅ Available Tools
- `list_branches` - Lists all branches in a repository
- `create_branch` - Creates a new branch
- `create_file` - Creates or updates a file in the repository

### ❌ Tools That Don't Exist
- `get_branch` - **This tool does not exist!** Use `list_branches` instead

## Parameter Format

The GitHub MCP server expects separate `owner` and `repo` parameters, not a combined format.

### ✅ Correct Format
```json
{
  "owner": "linsun",
  "repo": "gen-ai-demo",
  "branch": "main"
}
```

### ❌ Incorrect Format
```json
{
  "repo": "linsun/gen-ai-demo",
  "branch": "main"
}
```

## Tool Usage Examples

### List Branches
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "list_branches",
    "arguments": {
      "owner": "linsun",
      "repo": "gen-ai-demo"
    }
  }
}
```

**Response Format:**
```json
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "main"
      },
      {
        "type": "text", 
        "text": "feature-branch"
      }
    ]
  }
}
```

### Create Branch
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "create_branch",
    "arguments": {
      "owner": "linsun",
      "repo": "gen-ai-demo",
      "branch": "new-branch-name",
      "from_branch": "main"
    }
  }
}
```

### Create File
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call", 
  "params": {
    "name": "create_file",
    "arguments": {
      "owner": "linsun",
      "repo": "gen-ai-demo",
      "path": "folder/filename.txt",
      "content": "File content here",
      "message": "Commit message",
      "branch": "target-branch"
    }
  }
}
```

For binary files (images):
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "create_or_update_file",
    "arguments": {
      "owner": "linsun",
      "repo": "gen-ai-demo", 
      "path": "images/photo.jpg",
      "content": "base64-encoded-content-here",
      "message": "Add image file",
      "branch": "target-branch",
      "encoding": "base64"
    }
  }
}
```

**Note:** If the `encoding` parameter doesn't work properly (images stored as base64 text), try:
- `"content_encoding": "base64"` instead of `"encoding": "base64"`
- Omit the encoding parameter entirely (some servers auto-detect binary content)

## Environment Variables

When configuring the application:

```bash
# Repository name only (not owner/repo format)
export GITHUB_REPO="gen-ai-demo"

# Owner is hardcoded as "linsun" in the application
# Full repository path becomes: linsun/gen-ai-demo
```

## Branch Existence Checking

Since `get_branch` doesn't exist, use `list_branches` and parse the results:

```python
def check_branch_exists(branch_name):
    result = call_github_mcp_tool("list_branches", {
        "owner": "linsun", 
        "repo": GITHUB_REPO
    })
    
    if result and "content" in result:
        branches_data = result["content"]
        for branch_info in branches_data:
            if isinstance(branch_info, dict) and "text" in branch_info:
                if branch_name == branch_info["text"].strip():
                    return True
    return False
```

## Common Issues

### Issue: "Tool not found: get_branch"
**Solution:** Use `list_branches` instead and parse the response to check if branch exists.

### Issue: "Invalid repository format"
**Solution:** Use separate `owner` and `repo` parameters instead of combined format.

### Issue: "Branch creation timeout"
**Solution:** Use extended timeout (120 seconds) for GitHub operations.

### Issue: "Binary files (images) stored as base64 text instead of proper binary"
**Symptoms:** Image files show base64 content when viewed on GitHub instead of displaying as images  
**Example:** Raw URLs like `https://raw.githubusercontent.com/user/repo/branch/image.jpg` show base64 text starting with `/9j/4AAQ...` instead of binary image data

**Root Cause:** GitHub MCP server fundamental limitation - the `create_or_update_file` tool has NO `encoding` parameter and treats all content as UTF-8 text

**✅ AUTOMATIC SOLUTION IMPLEMENTED:**
The app now automatically converts base64 text to binary images after MCP upload:

1. **Upload via MCP:** Uses GitHub MCP server (works, stores as text)
2. **Auto-Convert:** Uses direct GitHub API to convert to proper binary format
3. **Result:** Images display correctly on GitHub

**Requirements for Auto-Conversion:**
```bash
# Set GitHub Personal Access Token
export GITHUB_TOKEN="ghp_your_token_here"
```

**Implementation:**
```python
# 1. Upload via MCP (stores as base64 text)
mcp_result = call_github_mcp_tool("create_or_update_file", {
    "owner": "owner", "repo": "repo", "path": "image.jpg",
    "content": base64_content, "message": "Upload image", "branch": "main"
})

# 2. Auto-convert to binary (if GITHUB_TOKEN available)
if mcp_result and GITHUB_TOKEN:
    conversion_success = convert_base64_to_binary_image(
        "image.jpg", base64_content, "main", "Convert to binary"
    )
```

**Fallback Behavior:**
- **With GITHUB_TOKEN:** ✅ Automatic binary conversion
- **Without GITHUB_TOKEN:** 📄 Remains as base64 text (manual conversion needed)

**Manual Conversion (if needed):**
```bash
# Download base64 content
curl -s "https://raw.githubusercontent.com/user/repo/branch/image.jpg" | base64 -d > image.jpg
```

## URL Generation

For displaying GitHub links in the UI:

```python
# Environment variable contains just the repo name
GITHUB_REPO = "gen-ai-demo"

# Construct full URLs manually
full_repo_path = f"linsun/{GITHUB_REPO}"
branch_url = f"https://github.com/{full_repo_path}/tree/{branch_name}"
folder_url = f"https://github.com/{full_repo_path}/tree/{branch_name}/folder"
```

## Testing

To test the GitHub MCP server API:

```bash
# List branches
curl -X POST http://your-mcp-server:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "list_branches",
      "arguments": {
        "owner": "linsun",
        "repo": "gen-ai-demo"
      }
    }
  }'
```
