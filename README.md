# NiumaParty 牛馬派對

> A Hong Kong-themed GameFi party game — AI-assisted 3D pipeline meets Web3 game design.

## Overview

NiumaParty is a multiplayer party game set in Hong Kong, featuring iconic cultural elements: red minibuses (紅VAN), pineapple buns (菠蘿包), and the "niuma" (牛馬/work-horse) spirit of Hong Kong workers.

**Tech Stack**: Godot 4.6 + Blender 5.1 + Meshy AI + Python

## Features

- **AI-Assisted 3D Pipeline**: Text-to-3D generation via Meshy AI → topology refinement in Blender → game integration in Godot
- **Hong Kong Cultural Assets**: Red minibus, Sham Shui Po buildings, pineapple buns, cow & horse characters
- **Meshy AI Plugin**: Custom Godot addon for direct Meshy AI model import
- **GameFi Ready**: Designed for Web3 token economy integration

## 3D Assets

| Asset | Source | Pipeline |
|-------|--------|----------|
| PineappleBun (菠蘿包) | Meshy AI → Blender | Text-to-3D → manual topology → glTF export |
| Red Minibus (紅VAN) | Meshy AI → Blender | Text-to-3D → UV refinement → Godot import |
| Cow & Horse Characters | Meshy AI → Blender | AI generation → rigging → animation |
| Sham Shui Po Scene (深水埗) | Blender | Manual modeling with photo reference |

## Project Structure

```
├── project.godot          # Godot 4.6 project config
├── addons/meshy/          # Meshy AI import plugin for Godot
├── models/                # Imported game-ready .glb models
├── assets/                # Source 3D files and Blender projects
│   ├── *.glb              # Individual 3D assets
│   ├── *.blend            # Blender source files
│   └── meshy_to_blender.py # Meshy AI → Blender import script
└── README.md
```

## How It Works

```
Meshy AI (text prompt) → .glb model → Blender (topology/UV/material) → .glb export → Godot (game scene)
```

## Related Repositories

- [web3-ux-contracts](https://github.com/naturejx-source/web3-ux-contracts) — Smart contracts for GameFi token economy
- [niuma-nlp-research](https://github.com/naturejx-source/niuma-nlp-research) — UX research with 1,012 multilingual game reviews
- [ollama-ux-personas](https://github.com/naturejx-source/ollama-ux-personas) — AI persona agents for user testing

## Author

**WU, JINXIA (Rucia Woo)** — BSc Software Engineering | UX Researcher | Web3 Builder
