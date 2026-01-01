# Hunt Map Overlay by sKhaled

A lightweight, real time Windows overlay for Hunt: Showdown that displays map POIs directly on screen.  
Designed to be click through, configurable, and persistent, with all data stored locally and no game file modification.

---

## Disclaimer

This project is not affiliated with or endorsed by Crytek.

Use at your own risk.  
No guarantees are provided.  
This overlay does not modify game files or memory.  
Intended for informational and accessibility purposes.

Always comply with the game’s terms of service.

## Special Thanks

- Kamille (https://github.com/waibcam), and his amazing discord community for providing the POI data.


---
## Showcase

This youtube video showcases all of the features as of right now:

https://youtu.be/uo_AdHLiIgo


## Features

- Real time on screen map overlay
- Supports all Hunt: Showdown maps
- Configurable POI categories
- Per category enable or disable toggle
- Per category color picker
- Global POI size scaling
- Click through overlay that does not block input
- Hotkey driven interaction
- Persistent configuration saved locally
- Soft hide POIs per category
- Fully portable single exe build

## How It Works

The overlay loads map POI data from JSON files and projects them onto a configurable screen rectangle.  
Coordinates are converted from Hunt’s 4096x4096 map grid into normalized screen space and rendered as simple shapes for clarity and performance.

The overlay does not modify game files, inject into the game, or hook any game process.  
It runs as a separate window layered above the game.


## File Storage

On first launch, the application creates the following directory:

%LOCALAPPDATA%\HuntOverlay\

This folder contains:

- data.json  
  Map POI coordinate data

- poiData.json  
  POI style definitions such as radius and default colors

- config.json  
  User settings including enabled categories, colors, map selection, hidden POIs, and size scale

All edits made to these files persist across restarts and updates.


## Controls

Overlay Controls

Backtick (`)  
Toggle master enable or disable

Tab  
Show or hide overlay

H  
Hide overlay

1 2 3 4  
Switch maps if enabled in the control panel

Ctrl + Alt + Shift + Delete  
Hide the POI currently under the mouse

This is a soft hide.  
It only hides the POI for the category it was hidden from.  
It does not delete data from JSON files.  
Hidden state is saved in configuration.


## Control Panel

The control panel allows you to:

- Enable or disable POI categories
- Change category colors
- Switch maps manually
- Enable numeric map switching
- Adjust global POI size scale
- View hotkey instructions

The panel stays on top and does not interfere with gameplay.

## Global POI Scaling

A global size scale lets you increase or decrease all POI sizes without editing JSON files.

- Smaller and Bigger buttons adjust incrementally
- Numeric scale box allows precise control
- Scale applies to all POI categories
- Value is saved in configuration

---

## Installation

Option 1: Prebuilt Executable

1. Download HuntOverlay.exe  
2. Run the executable  
3. On first launch, required files are created automatically  
4. Launch Hunt: Showdown and toggle the overlay  

Option 2: Run from Source

Requirements:

- Python 3.10 or newer
- PySide6

Install dependencies:

pip install pyside6

Run:

python HuntOverlay.py

---

## Building the Executable

To build a single file Windows executable:

py -m PyInstaller --noconfirm --onefile --windowed --name HuntOverlay --icon myicon.ico --add-data "data.json;." --add-data "poiData.json;." --add-data "myicon.ico;." HuntOverlay.py

The output will be located in:

dist\HuntOverlay.exe

You only need to use this file.


## Windows SmartScreen Warning

Because this application is unsigned, Windows may show a SmartScreen warning on first run.

This is expected behavior for unsigned executables.

Click:

More info -> Run anyway

To remove this warning permanently, the executable must be code signed with a trusted certificate. Which I am not gonna do sorry.


## License

This project is licensed under the MIT License.

You are free to:

- Use
- Modify
- Redistribute
- Include in other projects

As long as:

- Credit is preserved
- The license remains included

See the LICENSE file for full details.

---


## Author

sKhaled

If you improve this project, contributions and forks are welcome.
