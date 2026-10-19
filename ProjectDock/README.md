# Project Dock

**Part of NorthStar — free tools built to be useful.**

Project Dock is a desktop application for organizing project folders in one place. Its animated Project Orbit visualizes registered projects as planets orbiting NorthStar.

## Features

- **Project Orbit:** View registered projects as orbiting planets.
- **Project registration:** Add existing project folders to Project Dock.
- **Persistent storage:** Registered projects are saved locally and restored when the application starts.
- **Lightweight desktop UI:** Built with Python and Tkinter.

## Requirements

- Python 3
- Tkinter (usually included with standard Python installations)

## Getting Started

1. Clone or download this repository.
2. Open a terminal in the `ProjectDock` directory.
3. Run:

   ```powershell
   python main.py
   ```

## Local Data

Project Dock stores its registered project paths in a local `projects.json` file alongside the application.

This file is generated locally and is excluded from version control because it may contain personal folder paths.

## Roadmap

- [x] Animated Project Orbit
- [x] Add project folders
- [x] Save and restore registered projects
- [ ] Remove projects from Project Dock
- [ ] Further UI and usability improvements

## Built With

- Python
- Tkinter

## About NorthStar

NorthStar is a collection of free tools designed to help people build, organize, and create. Project Dock is one of its desktop tools.
