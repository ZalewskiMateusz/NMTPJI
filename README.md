# NMTPJI (Magic: The Gathering Commander Overlay & Tracker)

NMTPJI is a dark-themed desktop tactical HUD, game-state tracker, and analytical tool tailored for Magic: The Gathering Commander (EDH) games (webcam & online platforms like Untap.in / Discord).

## Key Features

- **Tactical Smart Overlay:** Multi-player game-state dashboard tracking Life, Commander Damage, Commander Tax, Poison, and player turn states in real time.
- **Commander Analytics & Winrates:** Tracks match history by Commander (not just deck names) with deep matchup breakdown (Win Rate vs. specific opponent Commanders).
- **Interactive Deck & Probability Tracker:** Built-in MTG deck management, Moxfield import, Scryfall metadata integration, and hypergeometric probability calculations for drawn cards.
- **Customizable Room Lobby:** Multi-player game setup with room configuration options (e.g. toggle Deck Tracker permission).
- **Local SQLite Engine:** Offline-first architecture for match results logging, commander performance analytics, and local deck storage.
- **Modern Dark UI:** Responsive CustomTkinter interface designed for secondary monitor usage during live matches.

## Project Structure

```text
NMTPJI/
├── core/         # Business logic (engine state, hypergeometric math, parsers, Scryfall API)
├── database/     # SQLite database handlers, match history & commander stats persistence
├── gui/          # CustomTkinter interface, modals (EndMatchWindow), views & components
│   ├── components/ # Reusable UI components (PlayerBoard, LifeCounter, StatsWidgets)
│   └── views/      # Application views (RoomView, StatisticsView, DeckTrackerView)
├── network/      # Peer-to-peer room state synchronization & lobby state
└── main.py       # Application entry point