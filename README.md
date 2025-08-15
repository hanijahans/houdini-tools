# Houdini Tools (Monorepo)

A collection of small, focused utilities for Houdini artists and TDs.  
Each tool lives in its own folder under [`tools/`](./tools/) with its own README, version, and source files.

## Tools

### [Finalization Checklist](./tools/finalization-checklist/)
**Type:** Shelf tool  
Make “final” mechanical, not emotional — a scrollable PySide2 checklist with helper actions like viewport screenshots.

### [Viewport Screenshot](./tools/viewport-screenshot/)
**Type:** Shelf tool  
Quickly capture Houdini viewport images to a chosen folder with timestamped filenames.

---

## How to Use
1. Pick a tool from the [`tools/`](./tools/) folder.
2. Follow its README for install instructions.
3. Download packaged releases from the **Releases** page if you just want the ready-to-use files.

## All-in-One Shelf
The root `HJD.shelf` file contains all tools in this repository in a single Houdini shelf set.
You can load it directly in Houdini if you want everything at once.

## Versioning
- Each tool maintains its own `VERSION` file.
- Release tags are namespaced per tool:  
  - `finalization-checklist-vX.Y.Z`

## License
MIT unless stated otherwise in a tool’s folder — see [LICENSE](./LICENSE).

## Support
- **Bugs / feature requests:** open a GitHub Issue in this repo and include the tool name in the title.
