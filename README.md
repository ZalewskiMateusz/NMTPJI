# NMTPJI (Magic: The Gathering Commander Overlay & Tracker)

**NMTPJI** is a dark-themed desktop tactical HUD, game-state tracker, and analytical tool tailored for Magic: The Gathering Commander (EDH) games—whether played via webcam or online platforms like Untap.in and Discord.

---

##Key Features

* **Tactical Smart Overlay:** Real-time multi-player game-state dashboard tracking Life, Commander Damage, Commander Tax, Poison counters, and player turn states.
* **Commander Analytics & Winrates:** Tracks match history by specific Commanders (not just deck names) with deep matchup breakdowns and win rate statistics against opponent Commanders.
* **Interactive Deck & Probability Tracker:** Built-in MTG deck management, Moxfield import support, Scryfall metadata integration, and hypergeometric probability calculations for drawn cards.
* **Customizable Room Lobby:** Multi-player game setup featuring custom room configuration options (such as toggling Deck Tracker permissions).
* **Local SQLite Engine:** Offline-first architecture ensuring reliable persistence for match results, commander performance metrics, and local deck storage.
* **Modern Dark UI:** Responsive CustomTkinter interface meticulously designed for second-monitor usage during live matches.
* **Automatic Updates:** Built-in updater service that seamlessly checks GitHub releases to keep your app up to date.

---

##Project Structure

```text
NMTPJI/
├── core/           # Business logic (engine state, hypergeometric math, parsers, Scryfall API)
├── database/       # SQLite database handlers, match history & commander stats persistence
├── gui/            # CustomTkinter interface, modals (EndMatchWindow), views & components
│   ├── components/ # Reusable UI components (PlayerBoard, LifeCounter, StatsWidgets)
│   └── views/      # Application views (RoomView, StatisticsView, DeckTrackerView)
├── network/        # Peer-to-peer room state synchronization & lobby state
├── services/       # External service integrations & background routines
├── utils/          # Helper modules, including the GitHub autoupdater utility
├── assets/         # Icons, images, and fonts (e.g., Kanisah.ttf, app icon)
├── main.py         # Application entry point with background update checks
├── version.txt     # Current local application version tracking
└── NMTPJI.spec     # PyInstaller build specification file
