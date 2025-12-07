📦 Google Drive MCP Server

A custom Model Context Protocol (MCP) server that connects Claude Desktop with Google Drive — enabling Drive file listing, folder creation, and more, directly through Claude.

Built by Arpit Saxena — learning Agentic AI, MCP, and tool-building from CampusX + real projects.

🚀 Features

🔗 OAuth2.0 Authentication

📁 List Google Drive files

🗃 Create folders 

❌ Delete files/folders

📁 Download Files also if you give file system access    

⚡ Built with FastMCP + uv

🤖 Fully agentic — usable inside Claude Desktop Tools panel

📂 Project Structure
google-drive-mcp-server/
│
├── main.py                 # Main MCP server code
├── requirements.txt        # Required dependencies
├── credentials_example.json # Example OAuth file (no secrets)
├── .gitignore
└── README.md

🧰 Installation
git clone https://github.com/Arpit-saxena-2004/google-drive-mcp-server.git
cd google-drive-mcp-server

python -m venv .venv
.\.venv\Scripts\activate

pip install -r requirements.txt


Place your real OAuth file:

credentials.json   

⚙️ Run the Server
uv run fastmcp run main.py


Or inside Claude Desktop (via claude_desktop_config):

"google-drive": {
  "command": "your path to uv",
  "args": ["run", "--with", "fastmcp", "fastmcp", "run", "main.py"],
  "cwd": "your path to google_drive_mcp_server",
  "transport": "stdio"
}

🧠 Why This Project Is Special

✔ Real Agentic AI project
✔ Custom MCP server 
✔ OAuth2.0 + API + Authentication
✔ Tool-building — highly in-demand skill
✔ Shows debugging, integration, and advanced AI usage

👨‍💻 Author

Arpit Saxena
Learning Agentic AI, MCP, and Tool Development
Guided by CampusX + self-projects

⭐ If you like this project

Star ⭐ the repo to support!