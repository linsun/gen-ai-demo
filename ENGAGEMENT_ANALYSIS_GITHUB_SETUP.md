# Engagement Analysis GitHub Integration Setup

This guide explains how to configure the Engagement Analysis app to automatically store analysis results and images to GitHub using the GitHub MCP server.

## Prerequisites

- GitHub MCP server running and accessible via HTTP
- GitHub MCP server configured with access to your target repository
- Repository permissions to create branches and files

## Environment Variables

Set these environment variables before running the Engagement Analysis app:

### Required Variables

```bash
# Event name - will be used as branch name and folder name
export EVENT_NAME="apidays-paris-2025"

# GitHub MCP server URL
export GITHUB_MCP_SERVER_URL="http://your-github-mcp-server:port/mcp"

# Target GitHub repository name only (default: gen-ai-demo)
export GITHUB_REPO="gen-ai-demo"
```

### Optional Variables

```bash
# LLaVa model server URL (for image analysis)
export LLAVA_BASE_URL="http://localhost:11434"

# GitHub Personal Access Token (for automatic binary image conversion)
export GITHUB_TOKEN="ghp_your_token_here"
```

### GitHub Token Setup (Recommended for Binary Images)

The GitHub MCP server stores all content as text by default. To automatically convert images from base64 text to proper binary format, set up a GitHub Personal Access Token:

1. **Generate Token:**
   - Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
   - Click "Generate new token (classic)"
   - Select scopes: `repo` (full repository access)
   - Set appropriate expiration date
   - Copy the generated token

2. **Set Environment Variable:**
   ```bash
   export GITHUB_TOKEN="ghp_your_token_here"
   ```

**🔄 With GITHUB_TOKEN:** Images are automatically converted to proper binary format after upload
**📄 Without GITHUB_TOKEN:** Images remain as base64 text files (manual conversion needed)

## How It Works

When you complete an engagement analysis using the camera inputs:

1. **Analysis Process:**
   - Takes two camera images
   - Analyzes engagement levels using LLaVa
   - Compares the engagement levels
   - Generates a summary

2. **GitHub Storage Process:**
   - Creates a new branch named after your event (e.g., `apidays-paris-2025`)
   - Creates folder structure: `events/{EVENT_NAME}/`
   - Stores three files:
     - `analysis_report_{timestamp}.md` - Complete analysis report
     - `image1_{timestamp}.jpg` - First engagement image  
     - `image2_{timestamp}.jpg` - Second engagement image

## Example Usage

### For APIdays Paris 2025 Event

```bash
# Set environment variables
export EVENT_NAME="apidays-paris-2025"
export GITHUB_MCP_SERVER_URL="http://github-mcp.example.com:3001/mcp"
export GITHUB_REPO="gen-ai-demo"

# Run the Streamlit app
cd demo/
streamlit run pages/4_Analyze_Engagement.py
```

### Result Structure

After analysis, files will be stored in:
```
Branch: apidays-paris-2025
Folder: events/apidays-paris-2025/
Files:
  - analysis_report_20250908_143025.md
  - image1_20250908_143025.jpg
  - image2_20250908_143025.jpg
```

## GitHub Links

After successful storage, the app provides direct links to:
- 🌿 **Branch view:** `https://github.com/{REPO}/tree/{BRANCH}`
- 📁 **Event folder:** `https://github.com/{REPO}/tree/{BRANCH}/events/{EVENT_NAME}`

## Analysis Report Format

The generated markdown report includes:

```markdown
# Engagement Analysis Report - {EVENT_NAME}

**Generated:** 2025-09-08 14:30:25

## Analysis Results

### First Image Analysis
[LLaVa analysis of first image]

### Second Image Analysis  
[LLaVa analysis of second image]

### Comparison Analysis
[Comparison between both images]

### Summary
[Brief summary with winner]

## Files
- Image 1: `image1_20250908_143025.jpg`
- Image 2: `image2_20250908_143025.jpg`
```

## Troubleshooting

### Common Issues

1. **GitHub MCP Connection Failed**
   - Check if `GITHUB_MCP_SERVER_URL` is correct
   - Verify GitHub MCP server is running
   - Ensure network connectivity

2. **Branch Creation Failed**
   - Verify GitHub MCP server has repository permissions
   - Check if branch already exists (will continue with existing branch)

3. **File Upload Failed**
   - Check repository permissions for the GitHub MCP server
   - Verify file sizes are within GitHub limits
   - Check network connectivity

4. **Images Stored as Base64 Text Instead of Binary**
   - **Symptoms:** Raw GitHub URLs show base64 text (e.g., `/9j/4AAQ...`) instead of displaying images
   - **Root Cause:** GitHub MCP server limitation - treats all content as text (no encoding parameter)
   - **Automatic Solution:** App now automatically converts base64 text to binary images using GitHub API
   - **Requirement:** Set `GITHUB_TOKEN` environment variable for automatic conversion
   - **Without Token:** Images remain as base64 text (manual conversion needed)

### Debug Mode

The app includes detailed logging. Check the console output for:
- `🔧` MCP session initialization messages
- `🌐` GitHub API call logs  
- `📁` File upload progress
- `📸` JPEG validation and base64 encoding details
- `✅` Success confirmations
- `❌` Error details

### Binary Upload Testing

If images are not displaying correctly on GitHub:

1. **Run the test script:**
   ```bash
   cd demo/
   python test_github_binary_upload.py
   ```

2. **Check the test results** - the script will try 4 different upload methods and report which ones work

3. **Verify image display** - the script tests if uploaded images display correctly or still show as base64 text

4. **Use working method** - the app will automatically use the first successful method found

## Features

- **Automatic Branch Creation:** Creates event-specific branches
- **Structured Storage:** Organized folder structure for each event
- **Timestamped Files:** Unique filenames prevent conflicts
- **Complete Documentation:** Markdown reports with full analysis
- **Direct Links:** Easy access to stored results
- **Error Handling:** Graceful handling of failures
- **Real-time Feedback:** Progress indicators and status updates

## Security Notes

- Ensure GitHub MCP server has minimal required permissions
- Use environment variables for sensitive configuration
- Review repository access logs regularly
- Consider using branch protection rules for important branches
