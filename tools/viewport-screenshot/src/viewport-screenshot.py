# Name: viewport_screenshot
# Label: Viewport Screenshot

import hou, os
from datetime import datetime

# ----- 1) Pick a resolution (single choice) -----
options = ["1920x1080", "2560x1440", "3840x2160", "Custom..."]
indices = hou.ui.selectFromList(
    options,
    message="Select Screenshot Resolution",
    exclusive=True
)
if not indices:  # user canceled
    raise hou.Error("Screenshot canceled.")

selection = options[indices[0]]

if selection == "Custom...":
    # Ask for width & height together; 0 == OK, 1 == Cancel
    btn, values = hou.ui.readMultiInput(
        "Custom Resolution",
        ("Width", "Height"),
        initial_contents=("1920", "1080")
    )
    if btn != 0:
        raise hou.Error("Screenshot canceled.")
    try:
        w = int(values[0].strip())
        h = int(values[1].strip())
        if w <= 0 or h <= 0:
            raise ValueError
        resolution = (w, h)
    except ValueError:
        raise hou.Error("Invalid custom resolution. Use positive integers.")
else:
    w, h = map(int, selection.split("x"))
    resolution = (w, h)

# ----- 2) Find the Scene Viewer -----
desktop = hou.ui.curDesktop()
scene_viewer = desktop.paneTabOfType(hou.paneTabType.SceneViewer)
if scene_viewer is None:
    raise hou.Error("No Scene Viewer found.")

# ----- 3) Build the output path (with timestamp) -----
save_dir = hou.expandString("$HIP/screenshots")
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

hip_path = hou.hipFile.path()
base = os.path.splitext(hip_path if hip_path else "untitled.hip")[0]
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
file_path = os.path.join(
    save_dir, f"{os.path.basename(base)}_{timestamp}.jpg"
)

# ----- 4) Configure a single-frame flipbook and shoot -----
settings = scene_viewer.flipbookSettings().stash()
settings.frameRange((hou.frame(), hou.frame()))
settings.output(file_path)
settings.useResolution(True)
settings.resolution(resolution)

scene_viewer.flipbook(scene_viewer.curViewport(), settings)

hou.ui.displayMessage(
    f"Screenshot saved:\n{file_path}\nResolution: {resolution[0]}x{resolution[1]}"
)
