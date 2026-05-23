# 16+8 Intermittent Fasting Tracker (16+8 间歇性禁食闹钟)

A multi-platform 16:8 intermittent fasting tracker and timer. This project provides multiple interfaces for tracking your fasting and eating windows, all sharing a single, unified configuration logic.

## Features

- **Cross-Platform Interfaces**:
  - **Mobile Web (`mobile.html`)**: Optimized for mobile screens, supports PWA (Add to Home Screen), and includes Wake Lock to keep the screen on.
  - **Desktop Web (`index.html`)**: A beautiful, minimalist UI for desktop browsers with visual ring progress.
  - **Desktop GUI (`gui.py`)**: A native desktop application built with Python and Tkinter.
  - **Command Line (`cli.py`)**: A lightweight terminal-based tracker.
- **Unified Configuration**: All versions logic share and sync the same core fasting windows.
- **Notifications & Sounds**: Real-time reminders when your window changes.

## Usage

### Python CLI & GUI

Ensure you have Python 3 installed. No external dependencies are required.

```bash
# Run the Desktop GUI
python3 gui.py

# Run the CLI
python3 cli.py
```

### Web Versions

Simply open the HTML files in your browser. 
For the best mobile experience, host `mobile.html` on a web server or open it directly on your device, and add it to your home screen.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve the UI, add new features (e.g., stats, history tracking), or build interfaces for other platforms.

## License

MIT License
