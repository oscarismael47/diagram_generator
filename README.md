# Diagram Generator

A Streamlit-based web app for generating and visualizing architecture diagrams (e.g., AWS) using Python code.

![Example AWS Diagram](./static/recording.gif)

## Features

- **Chat-driven diagram generation**: Describe your desired architecture in chat, and the app generates a diagram.
- **Python code preview**: View the Python code used to generate the diagram.
- **Download diagrams**: Download generated diagrams as images.
- **Agent graph visualization**: See the agent workflow as a flowchart.

## Usage

1. **Install dependencies**  
   ```
   pip install -r requirements.txt
   ```

2. **Run the app**  
   ```
   streamlit run app.py
   ```

3. **Interact**  
   - Use the chat sidebar to request diagrams (e.g., "add a random aws diagram").
   - View and download diagrams in the main area.
   - Switch tabs to see Python code or the agent graph.

## Project Structure

```
diagram_generator/
├── agent/
│   ├── agent.py
│   └── utils/
│       └── diagram_handler.py
├── app.py
├── README.md
└── ...
```

## Requirements

- Python 3.12+
- [Streamlit](https://streamlit.io/)
- [diagrams](https://diagrams.mingrammer.com/)

---

*This project is for generating and visualizing architecture diagrams