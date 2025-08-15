# Name: finalization_checklist
# Label: Finalization Checklist

# Houdini Shelf Tool: Finalization Checklist (Qt) + Screenshot + Persistent State (no modal popup)
import os, time, json
import hou
from PySide2 import QtWidgets, QtCore, QtGui

CHECK_ITEMS = [
    "No error flags (red) or critical warnings anywhere in the network.",
    "All external file paths are relative ($HIP, $JOB) — no absolute C:/ or /Users/ paths.",
    "Parameters behave as intended; key sliders/ramps don’t break the graph.",
    "Procedural chains still work after changing inputs (robustness sanity check).",
    "Remove or bypass unused test geometry/nodes (scene hygiene).",
    "Node names are clear and grouped; network annotated with sticky notes/colors.",
    "Remove or bypass temporary debugging/visualization nodes.",
    "Basic lighting rig in place (no default headlight in final shots).",
    "Shot camera(s) framed, locked, and protected (avoid accidental nudges).",
    "Shaders finalized or clean procedural placeholders — no default gray giveaways.",
    "No UV or texture stretching; verify texture paths are valid and UDIMs resolve correctly."
    "Heavy sims/meshes cached to disk; downstream reads from caches.",
    "Clear history & caches where safe (reduce file size, speed up load times).",
    "Display flags / viewport LODs optimized for smooth playback.",
    "All dependencies gathered into project folder (textures, caches, alembic, etc.).",
    "Final .hip saved with `_final` suffix (versioned and traceable).",
    "Required exports (EXR/MP4/ABC/FBX/etc.) completed per delivery specs.",
    "Scene opens cleanly on another machine (no missing plugins/paths).",
    "Final renders/playblast checked for artifacts, missing frames, or flicker."
]

# -------- Persistence helpers (userData on /obj) --------
STATE_KEY = "finalization_checklist_state_v1"

def _state_node():
    return hou.node("/obj")

def _load_state():
    n = _state_node()
    if not n: return {}
    raw = n.userData(STATE_KEY)
    if not raw: return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}

def _save_state(checked_indices):
    n = _state_node()
    if not n: return
    n.setUserData(STATE_KEY, json.dumps({"checked": checked_indices, "time": time.time()}))

# -------- Screenshot helpers --------
def _hip_dir():
    try:
        return hou.expandString("$HIP")
    except Exception:
        return os.path.dirname(hou.hipFile.path() or os.getcwd())

def _screens_dir():
    d = os.path.join(_hip_dir(), "screenshots")
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    return d

def _timestamp():
    return time.strftime("%Y%m%d_%H%M%S")

def _active_view_label():
    sv = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
    if not sv: return "noview"
    vp = sv.curViewport()
    cam = vp.camera()
    return cam.name() if cam else vp.name()

def _frame_str():
    try:
        return f"f{int(round(hou.frame())):04d}"
    except Exception:
        return "f0000"

def _screenshot_viewport(custom_suffix=""):
    """Single-frame flipbook as a JPG (viewport). Returns path or None."""
    sv = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
    if not sv:
        return None
    vp = sv.curViewport()

    base = os.path.splitext(hou.hipFile.path() or "untitled.hip")[0]
    label = _active_view_label()
    fname = f"{os.path.basename(base)}_{label}_{_frame_str()}_{_timestamp()}"
    if custom_suffix: fname += f"_{custom_suffix}"
    img_path = os.path.join(_screens_dir(), fname + ".jpg")

    settings = sv.flipbookSettings().stash()
    settings.frameRange((hou.frame(), hou.frame()))
    settings.output(img_path)
    settings.useResolution(True)
    settings.resolution((1920, 1080))
    settings.cropOutMaskOverlay(True)

    try:
        sv.flipbook(vp, settings)
        return img_path
    except Exception:
        return None

# -------- Path check & save-as-final --------
def _has_absolute_paths():
    bad = []
    for r in ["/obj", "/stage", "/mat", "/img"]:
        n = hou.node(r)
        if not n: continue
        for node in n.allSubChildren():
            for parm in node.parms():
                pt = parm.parmTemplate()
                if pt.type() != hou.parmTemplateType.String: continue
                try:
                    val = parm.evalAsString()
                except Exception:
                    continue
                if not val: continue
                is_abs = (":/" in val or val.startswith("/") or (len(val) > 2 and val[1:3] == ":\\"))  # win/unix
                if is_abs and "$HIP" not in val and "$JOB" not in val:
                    bad.append(f"{node.path()} : {parm.name()} = {val}")
                    if len(bad) > 50:
                        bad.append("… (truncated)")
                        return bad
    return bad

def _save_as_final():
    cur = hou.hipFile.path()
    if not cur or cur == "untitled.hip":
        hou.ui.displayMessage("Save your scene first.", severity=hou.severityType.Warning)
        return None
    if cur.lower().endswith("_final.hip"):
        return cur
    base, ext = os.path.splitext(cur)
    final_path = base + "_final" + ext
    hou.hipFile.save(file_name=final_path)
    return final_path

# -------- Dialog --------
class FinalizationDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(FinalizationDialog, self).__init__(parent)
        self.setWindowTitle("Finalization Checklist")
        self.setMinimumSize(720, 640)

        title = QtWidgets.QLabel("Tick every box, take screenshots anytime, then click “Save & Mark as Final”.")
        title.setWordWrap(True)
        title.setStyleSheet("font-weight:600; margin:4px 0 10px 0;")

        self.list = QtWidgets.QListWidget()
        self.list.setWordWrap(True)
        self.list.setAlternatingRowColors(True)
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.list.setUniformItemSizes(False)
        self.list.setSpacing(4)

        for text in CHECK_ITEMS:
            item = QtWidgets.QListWidgetItem(text)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            item.setToolTip(text)
            self.list.addItem(item)

        # Load saved state
        saved = _load_state()
        checked_set = set(saved.get("checked", []))
        for i in range(self.list.count()):
            if i in checked_set:
                self.list.item(i).setCheckState(QtCore.Qt.Checked)

        # Persist on change
        self.list.itemChanged.connect(self._persist_now)

        # Buttons
        btn_check_all = QtWidgets.QPushButton("Check All")
        btn_clear = QtWidgets.QPushButton("Clear")
        btn_shot = QtWidgets.QPushButton("Screenshot")
        btn_finalize = QtWidgets.QPushButton("Save & Mark as Final")
        btn_cancel = QtWidgets.QPushButton("Cancel")

        # Non-modal status line
        self.status = QtWidgets.QLabel("")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color:#a0a0a0; font-size:11px;")
        self._status_timer = QtCore.QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(lambda: self.status.setText(""))

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(btn_check_all)
        btn_row.addWidget(btn_clear)
        btn_row.addWidget(btn_shot)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_finalize)
        btn_row.addWidget(btn_cancel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.list, 1)
        layout.addWidget(self.status)          # <<< inline status instead of popup
        layout.addLayout(btn_row)

        btn_check_all.clicked.connect(self._check_all)
        btn_clear.clicked.connect(self._clear_all)
        btn_cancel.clicked.connect(self.reject)
        btn_shot.clicked.connect(self._on_screenshot)
        btn_finalize.clicked.connect(self._on_finalize)

    # ----- small helpers -----
    def _notify(self, msg):
        """Update inline status + Houdini status bar, no modal dialog."""
        self.status.setText(msg)
        self._status_timer.start(4500)
        try:
            hou.ui.setStatusMessage(msg, severity=hou.severityType.Message)
        except Exception:
            pass

    # ----- persistence -----
    def _collect_checked_indices(self):
        return [i for i in range(self.list.count())
                if self.list.item(i).checkState() == QtCore.Qt.Checked]

    def _persist_now(self, *args):
        _save_state(self._collect_checked_indices())

    # ----- UI actions -----
    def _check_all(self):
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(QtCore.Qt.Checked)
        self._persist_now()
        self._notify("All items checked.")

    def _clear_all(self):
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(QtCore.Qt.Unchecked)
        self._persist_now()
        self._notify("All items cleared.")

    def _all_checked(self):
        return all(self.list.item(i).checkState() == QtCore.Qt.Checked
                   for i in range(self.list.count()))

    def _on_screenshot(self):
        path = _screenshot_viewport("checkpoint")
        if path:
            self._notify(f"Screenshot saved: {path}")
        else:
            self._notify("Screenshot failed (no Scene Viewer or flipbook error).")

    def _on_finalize(self):
        if not self._all_checked():
            ans = hou.ui.displayMessage(
                "Not all items are checked. Still proceed?",
                buttons=("Go Back", "Proceed"),
                default_choice=0, close_choice=0, severity=hou.severityType.Warning
            )
            if ans == 0:
                return

        bad_paths = _has_absolute_paths()
        if bad_paths:
            sample = "\n".join(bad_paths[:3])
            ans = hou.ui.displayMessage(
                f"Found {len(bad_paths)} absolute paths!\n\n{sample}\n\nProceed anyway?",
                buttons=("Fix First", "Proceed"),
                default_choice=0, close_choice=0,
                severity=hou.severityType.Warning
            )
            if ans == 0:
                return

        self._persist_now()
        final_path = _save_as_final()
        if final_path:
            shot = _screenshot_viewport("final")
            msg = f"Saved as: {final_path}"
            if shot: msg += f"  |  Final screenshot: {shot}"
            self._notify(msg)
        self.accept()

def show_finalization_dialog():
    try:
        main = hou.ui.mainQtWindow()
    except Exception:
        main = None
    dlg = FinalizationDialog(parent=main)
    dlg.exec_()

# Run
show_finalization_dialog()

