# ducky-game
两个文件夹负责的功能



/src
main.py (游戏入口)
    ↓
game_state.py (状态管理)
    ↓
├── duck.py (主角)
├── battle.py (战斗) → enemy.py (敌人)
├── partner.py (伙伴)
├── npc.py (NPC)
├── weapon.py (武器)
└── utils.py (工具)
    ↓
animation_utils.py (动画)
config.py (配置)
constants.py (常量)

/assets（图片资源）
