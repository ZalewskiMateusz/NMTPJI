# NMTPJI (Magic: The Gathering Commander Overlay & Tracker)

NMTPJI is a desktop tactical HUD and card probability tracker tailored for Magic: The Gathering Commander (EDH) webcam games (e.g., via Discord).

## Key Features
- **Hypergeometric Probability Calculator:** Real-time odds calculation of opponents holding specific cards in hand.
- **Moxfield / Text Decklist Parser:** Fast import of decklists directly from text or Moxfield exports.
- **Scryfall Integration:** Automatic caching and display of card art and metadata.
- **Tactical Smart Overlay:** Multi-player game-state dashboard tracking Life, Commander Damage, and Commander Tax.
- **Local SQLite Storage:** Offline-first architecture for local deck saving and game statistics.

## Project Structure
```text
NMTPJI/
├── core/         # Business logic (math, parsers, Scryfall API)
├── database/     # SQLite database handlers
├── gui/          # CustomTkinter interface views and components
├── network/      # Peer-to-peer room state synchronization
└── main.py       # Application entry point