# Google Slides Integration

Simple integration with an external Google Slides MCP server for voice-activated presentation creation.

## Prerequisites

- A running Google Slides MCP server (accessible via HTTP)
- MCP server configured with Google API credentials

## Setup

### 1. Install Dependencies

```bash
cd demo/
pip install -r requirements.txt
```

### 2. Configure MCP Server URL

```bash
export MCP_SERVER_URL="http://agentgw.mcp.svc.cluster.local:3000/mcp"
```

Or set to your MCP server endpoint.

## Usage

Once configured, you can use voice or text commands in the Voice with Llama app to create Google Slides:

- "Create slides for Paris"
- "Make a presentation about Tokyo" 
- "Generate slides for New York"
- "Slides for London"

The app will automatically:
1. Detect your intent to create slides for a place
2. Generate relevant content using Llama
3. Create a Google Slides presentation
4. Return a direct link to the presentation

## Test Connection

```bash
cd demo/
python test_mcp_connection.py
```

## Run the App

```bash
cd demo/
streamlit run pages/2_Voice_With_Llama.py
```

Then use voice or text commands like "Create slides for Tokyo".

## View Logs for Debugging

The app includes comprehensive logging to help debug slide creation:

```bash
cd demo/
python view_logs.py  # Shows logging information and tips
```

**Log messages include:**
- 🔍 Intent detection for slide creation requests
- 🌐 MCP server communication (requests/responses)  
- 📊 Presentation creation steps
- 🤖 Content generation with Llama
- ✅ Success messages with presentation IDs
- ❌ Detailed error messages

**To see logs in real-time:**
Run the Streamlit app in one terminal, and the logs will appear in that terminal output with timestamps and emojis for easy identification.
