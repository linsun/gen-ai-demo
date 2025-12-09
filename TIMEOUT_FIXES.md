# GitHub MCP Timeout Issues - Fixes Applied

This document describes the improvements made to handle GitHub MCP server timeout issues and improve reliability.

## Problem

The original issue was:
- GitHub MCP session initialization worked (200 response with session ID)
- Branch creation request timed out after 60 seconds
- Connection error: `Read timed out. (read timeout=60)`

## Solutions Implemented

### 1. Extended Timeouts for GitHub Operations

```python
# Extended timeout for GitHub operations that may take longer
timeout_duration = 120 if tool_name in ['create_branch', 'create_file'] else 60
```

**Why:** GitHub API operations (especially branch creation and file uploads) can take longer than regular API calls.

### 2. Pre-flight Connection Testing

```python
def test_github_mcp_connection():
    """Test if GitHub MCP server is accessible"""
```

**Benefits:**
- Tests connection before attempting operations
- Provides early feedback to users about connectivity issues
- Shows connection status in the UI

### 3. Branch Existence Check

```python
def check_branch_exists(branch_name):
    """Check if a branch exists in the repository"""
```

**Why:** Avoids unnecessary branch creation attempts if branch already exists.

### 4. Branch Creation with Retry Logic

```python
def create_branch_with_retry(branch_name, max_retries=2):
    """Create branch with retry logic"""
```

**Features:**
- Attempts branch creation up to 2 times
- Logs each attempt for debugging
- Graceful fallback to main branch if creation fails

### 5. Enhanced Error Handling for File Uploads

**Improvements:**
- Individual try-catch for each file upload
- Partial success handling (some files uploaded successfully)
- Detailed error reporting
- Continues with remaining uploads even if one fails

### 6. Graceful Fallback Strategy

**Fallback Chain:**
1. Try to create new branch → If fails
2. Use existing branch → If fails  
3. Use main branch → Continue with uploads

### 7. Improved User Feedback

**UI Enhancements:**
- Real-time connection status display
- Progress indicators for each operation
- Partial success notifications
- Detailed error messages
- Direct GitHub links when successful

## Updated Workflow

### Before Analysis
1. **Connection Test:** Verify GitHub MCP server is accessible
2. **Status Display:** Show connection status to user
3. **Configuration:** Display current settings

### During GitHub Storage
1. **Branch Management:**
   - Check if event branch exists
   - Create branch if needed (with retry)
   - Fallback to main branch if creation fails

2. **File Uploads:**
   - Upload analysis report (markdown)
   - Upload first image (base64 encoded)
   - Upload second image (base64 encoded)
   - Track success/failure for each file

3. **Result Reporting:**
   - Show successful uploads
   - Report any failures with details
   - Provide GitHub links for access

## Error Scenarios Handled

### 1. GitHub MCP Server Unreachable
- **Detection:** Pre-flight connection test
- **User Experience:** Clear error message, analysis continues without GitHub storage

### 2. Branch Creation Timeout
- **Handling:** Retry logic with fallback to existing/main branch
- **User Experience:** Warning message, continues with file uploads

### 3. Individual File Upload Failures
- **Handling:** Continue with remaining uploads
- **User Experience:** Partial success notification with details

### 4. Network Intermittency
- **Handling:** Extended timeouts and retry mechanisms
- **User Experience:** Progress indicators and detailed status

## Configuration

### Environment Variables
```bash
EVENT_NAME="apidays-paris-2025"                    # Event name for branch/folder
GITHUB_MCP_SERVER_URL="http://server:3000/mcp"     # MCP server endpoint
GITHUB_REPO="linsun/gen-ai-demo"                   # Target repository
```

### Timeout Settings
- Regular operations: 60 seconds
- GitHub operations (branch/file): 120 seconds
- Connection tests: 10 seconds

## Benefits

1. **Reliability:** Handles timeout and network issues gracefully
2. **User Experience:** Clear feedback and status information
3. **Partial Success:** Saves what it can even if some operations fail
4. **Debugging:** Comprehensive logging for troubleshooting
5. **Flexibility:** Fallback strategies ensure analysis results are preserved

## Monitoring

Watch for these log messages:
- `✅ GitHub MCP: Connected` - Connection successful
- `🕐 Using 120s timeout for create_branch` - Extended timeout in use
- `⚠️ Branch creation failed, will try to use main branch` - Fallback activated
- `✅ Successfully uploaded 2/3 files` - Partial success scenario

## Binary File Upload Issues (Additional Fix)

### Problem
Images were being stored as base64 text content instead of proper binary files in GitHub.

### Root Cause
The GitHub MCP server wasn't properly handling the `encoding: "base64"` parameter.

### Solution Implemented
1. **Multiple Encoding Attempts:** Try different parameter formats
   - `"encoding": "base64"` (standard)
   - `"content_encoding": "base64"` (alternative) 
   - No encoding parameter (auto-detection)

2. **Enhanced Logging:** Added detailed logging for binary uploads
   - File size verification
   - Base64 content preview
   - Upload attempt tracking

3. **Retry Logic:** Automatic retry with different parameter combinations

## Future Improvements

1. **Background Processing:** Move GitHub uploads to background thread
2. **Local Backup:** Save files locally if GitHub upload fails completely
3. **Retry Queue:** Implement persistent retry queue for failed uploads
4. **Health Monitoring:** Regular health checks of GitHub MCP server
5. **Binary Upload Validation:** Verify uploaded images are properly decoded on GitHub
