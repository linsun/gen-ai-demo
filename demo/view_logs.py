#!/usr/bin/env python3
"""
Log viewer for the Voice with Llama app with Google Slides integration
Run this in a separate terminal to see real-time logs
"""
import subprocess
import sys
import os

def main():
    print("🔍 Real-time Log Viewer for Voice with Llama")
    print("=" * 50)
    print("This will show logs from the Streamlit app in real-time.")
    print("Make sure to run the Streamlit app in another terminal first.")
    print("=" * 50)
    print()
    
    # Instructions for viewing logs
    print("📋 To view logs, you have several options:")
    print()
    print("1️⃣  Terminal Output (when running streamlit):")
    print("   The logs will appear in the terminal where you run:")
    print("   streamlit run pages/2_Voice_With_Llama.py")
    print()
    print("2️⃣  Check Streamlit logs directory:")
    streamlit_logs = os.path.expanduser("~/.streamlit/logs/")
    if os.path.exists(streamlit_logs):
        print(f"   Streamlit logs: {streamlit_logs}")
        try:
            log_files = [f for f in os.listdir(streamlit_logs) if f.endswith('.log')]
            if log_files:
                latest_log = max(log_files, key=lambda x: os.path.getctime(os.path.join(streamlit_logs, x)))
                print(f"   Latest log file: {latest_log}")
                print(f"   View with: tail -f {os.path.join(streamlit_logs, latest_log)}")
            else:
                print("   No log files found in Streamlit logs directory")
        except Exception as e:
            print(f"   Error checking log files: {e}")
    else:
        print("   Streamlit logs directory not found")
    print()
    print("3️⃣  Python logging output:")
    print("   The app logs will appear in the terminal output with timestamps")
    print("   Look for messages with emojis like 🔍, 📊, 🌐, 🤖, etc.")
    print()
    print("4️⃣  Debug browser console:")
    print("   Open browser dev tools (F12) and check the console for any errors")
    print()
    
    # Sample test messages
    print("🧪 Sample test messages to try:")
    print("   - 'Create slides for Tokyo'")
    print("   - 'Make a presentation about Paris'") 
    print("   - 'Generate slides for New York'")
    print("   - 'Slides for London'")
    print()
    
    print("🔍 What to look for in the logs:")
    print("   🔍 Intent detection messages")
    print("   🌐 MCP server communication")
    print("   📊 Presentation creation steps") 
    print("   🤖 Content generation with Llama")
    print("   ✅ Success messages")
    print("   ❌ Error messages with details")
    print()
    
    print("💡 Troubleshooting tips:")
    print("   - If no logs appear, check if logging is enabled")
    print("   - Look for HTTP errors in MCP communication")
    print("   - Check if presentation IDs are being extracted")
    print("   - Verify Ollama is responding for content generation")
    print()

if __name__ == "__main__":
    main()
