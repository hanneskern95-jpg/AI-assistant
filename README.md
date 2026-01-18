# AI Assistant

An AI assistant with custom tools that extend its capabilities.

## Installation

Install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

## Running the GUI

The project includes a Streamlit-based GUI. Start it with:

```bash
streamlit run src/gui_streamlit.py
```

## Adding Custom Tools

The main selling point of this project is how easy it is to extend functionality with custom tools. To add a new tool:

1. Create a Python file in `src/tools/_tools/`
2. Define a class that inherits from the `Tool` class. Add a tool_dict containing the information about the tool and a method run_tool, containing the method that actually runs once the tool gets called.
3. The tool will be automatically loaded and available in the assistant

No additional registration or configuration needed!

## Available Tools

The assistant currently includes the following tools:

- **Recipe Creator** - Search for recipes online
- **Spotify Playlist Creator** - Create and upload playlists to Spotify
- **Wikipedia Fact Checker** - Check facts on Wikipedia
