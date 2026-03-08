#!/usr/bin/env python3
"""
3D Modeling Canvas CLI — Copilot runtime implementation.

Usage:
    python3 modeling3d_cli.py render_scene '{"title":"Test","objects":[{"type":"box","width":10,"height":10,"depth":10,"color":"#10b981","position":[0,5,0]}]}'
    python3 modeling3d_cli.py add_object '{"type":"sphere","radius":5,"color":"#3b82f6","position":[15,5,0]}'
    python3 modeling3d_cli.py open
    python3 modeling3d_cli.py export stl
    python3 modeling3d_cli.py wait_for_action 60
    python3 modeling3d_cli.py clear
"""
import json
import sys

sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent.parent / 'claude' / 'implementation'))
from modeling3d import Canvas3D

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: modeling3d_cli.py <action> [args...]", file=sys.stderr)
        sys.exit(1)

    action = args[0]
    c = Canvas3D()

    if action == 'open':
        c.open()
        print(json.dumps({"status": "ok", "url": c._url()}))

    elif action == 'render_scene':
        scene = json.loads(args[1]) if len(args) > 1 else {}
        c.render_scene(scene)
        print(json.dumps({"status": "ok"}))

    elif action == 'add_object':
        obj = json.loads(args[1]) if len(args) > 1 else {}
        c.add_object(obj)
        print(json.dumps({"status": "ok"}))

    elif action == 'transform':
        obj_id   = args[1] if len(args) > 1 else ''
        position = json.loads(args[2]) if len(args) > 2 else None
        rotation = json.loads(args[3]) if len(args) > 3 else None
        scale    = json.loads(args[4]) if len(args) > 4 else None
        c.transform(obj_id, position=position, rotation=rotation, scale=scale)
        print(json.dumps({"status": "ok"}))

    elif action == 'set_camera':
        position = json.loads(args[1]) if len(args) > 1 else [50, 35, 50]
        target   = json.loads(args[2]) if len(args) > 2 else None
        c.set_camera(position, target)
        print(json.dumps({"status": "ok"}))

    elif action == 'set_title':
        title = args[1] if len(args) > 1 else ''
        c.set_title(title)
        print(json.dumps({"status": "ok"}))

    elif action == 'export':
        fmt = args[1] if len(args) > 1 else 'stl'
        c.export(fmt)
        print(json.dumps({"status": "ok", "format": fmt}))

    elif action == 'clear':
        c.clear()
        print(json.dumps({"status": "ok"}))

    elif action == 'wait_for_action':
        timeout = int(args[1]) if len(args) > 1 else 60
        result  = c.wait_for_action(timeout=timeout)
        print(json.dumps(result))

    else:
        print(json.dumps({"status": "error", "error": f"Unknown action: {action}"}))
        sys.exit(1)


if __name__ == '__main__':
    main()
