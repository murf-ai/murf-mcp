# Murf MCP Server

![Murf AI Logo](https://murf.ai/public-assets/home/Murf_Logo.png)


## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)

---


## Overview

The Murf MCP Server offers seamless integration with MCP clients like [Claude Desktop](https://claude.ai/download), enabling developers and creators to convert text into lifelike speech effortlessly. With over 130 natural-sounding voices across 13+ languages and 20+ speaking styles, Murf provides unparalleled speech customization for a wide range of applications.

---

## Installation

### Claude Desktop

1. Get your API key from [Murf API Dashboard](https://murf.ai/api/dashboard).
2. Install `uv` (Python package manager), install with:
    **macOS:**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    **Windows:**
    ```bash
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
    Check out their [official guide](https://github.com/astral-sh/uv?tab=readme-ov-file#installation) for more details.

3. There are two ways to proceed with the setup:

   **Option 1: Automated Setup (Recommended)**
   ```bash
   uvx setup-murf-mcp-claude
   ```
   This will automatically configure Claude Desktop with the Murf MCP server.

   **Option 2: Manual Setup**
   
   If you prefer to configure manually, continue with the following steps:


    1. Update Claude Desktop Config to install murf, open the config file: 
        Go to `Claude → Settings → Developer → Edit Config → claude_desktop_config.json` 

        or
        if you have VS Code installed, run:

        **macOS:**
         ```bash
         code ~/Library/Application\ Support/Claude/claude_desktop_config.json
         ```
         **Windows:**
          ```bash
          code $env:AppData\Claude\claude_desktop_config.json
          ```

    
    2.  This will open the config file, add the following lines to the `"mcpServers"` section:

        ```json
        "mcpServers": {
            "Murf":{
                "command": "uvx",
                "args": ["murf-mcp"],
                "env": {
                    "MURF_API_KEY": "YOUR_MURF_API_KEY"
                }
            }
        }
        ```
    3. Install FFmpeg (required for audio processing):

        **macOS:**
        ```bash
        brew install ffmpeg
        ```

        **Windows:**
        Download FFmpeg from [here](https://www.ffmpeg.org/download.html)

        
4. Restart the Claude Desktop app to start the MCP server, you should be able to see a small hammer icon in the chat input box. This indicates that the MCP server is running and tools are available.

**Note:** For Windows users, "Developer Mode" must be enabled in Claude Desktop to utilize the MCP server. To enable it, click the hamburger menu in the top-left corner, select "Help," and then choose "Enable Developer Mode."

---

## Usage

 * Prompt the LLM to create a voiceover:
    For example:  

    * Create a one-minute podcast on Generative AI featuring a conversation between two speakers. Choose suitable voice styles and accents, incorporate natural pauses, and generate a voiceover for it.

    * Create a 15-second introduction for my YouTube channel about indoor plants. Use a friendly and conversational tone to generate a voiceover for it.
    
    These should generate a voiceover and save it to file on your Desktop.

* You can also prompt the LLM to recommend a voice style for a specific use case. For example:

    * What is the best voice style for a YouTube video about indoor plants?
    * What is the best voice style for a podcast about Generative AI?

* The TTS API supports a variety of features such as rate, pitch, speed, and custom pronunciations. You can explore these options [here](https://murf.ai/api/docs/api-reference/text-to-speech/generate#request). You can prompt the LLM to apply these settings to the overall voiceover or tailor them individually for each speaker.


## Contributing

Contributions are welcome! If you’d like to improve the MCP server, follow these steps:

1. Fork the repository and clone it to your machine.

2. Create a new branch for your feature or bugfix.

3. Make your changes and ensure everything runs smoothly.

4. Write clear commit messages and keep the code clean.

5. Open a pull request describing your changes.

Feel free to open an issue if you have questions, feature requests, or need help getting started.


## Troubleshooting
If you encounter any issues, please check the following:

- `spawn uvx ENOENT` error:
If you see a `spawn uvx ENOENT` error, it means the system can't locate the uvx executable. To fix this:
    - Run the following command to get the absolute path of `uvx`:
        ```bash
        which uvx
        ```
    - Update your `claude_desktop_config.json` file with the absolute path in the `command` field. For example:
        ```json
        "command": "/absolute/path/to/uvx"
        ```
    - Restart the Claude Desktop app.

- Check the logs for any other error messages or warnings here:
  - **macOS:** `~/Library/Logs/Claude/mcp-server-Murf.log`
  - **Windows:** `%APPDATA%\Claude\logs\mcp-server-Murf.log`

