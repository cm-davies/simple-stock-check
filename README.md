# simple-stock-check

A Python script that monitors product pages across multiple websites and sends email notifications when items are back in stock. It uses **Playwright** with stealth features to simulate human browsing and bypass basic anti-bot protections.

---

## Features

- Supports multiple websites, including Amazon, Cosmic Collectables, and others.  
- Detects CAPTCHAs and pauses for manual solving.  
- Robust detection of in-stock and out-of-stock states, including site-specific logic.  
- Sends email notifications via SMTP when items become available.  
- Uses human-like random pauses, scrolling, and mouse movement to mimic real users.  
- Maintains a persistent browser context for more consistent behavior.

---

## Supported Sites

### Works reliably
- [Amazon UK](https://www.amazon.co.uk)  
- [Bremner TCG](https://www.bremnertcg.co.uk)  
- [Cosmic Collectables](https://cosmiccollectables.co.uk)  
- [Dan Solo TCG](https://dansolotcg.co.uk)  
- [Double Sleeved](https://www.doublesleeved.co.uk)  
- [Endo Collects](https://endocollects.co.uk)  
- [Firestorm Cards](https://www.firestormcards.co.uk)  
- [Romulus Games](https://romulusgames.com)  

### Sometimes works
- [Pokemon Center](https://www.pokemoncenter.com) (may trigger CAPTCHA)

### Known issues / does not work
- [Smyths Toys UK](https://www.smythstoys.com/uk/en-gb) (CAPTCHA & blocks)  
- [The Card Vault](https://thecardvault.co.uk) (loads homepage instead of product page)  
- [Endgame LDN](https://endgameldn.com) (sign-up prompt)  
- [Hills Cards](https://www.hillscards.co.uk) (email system only)  
- [HMV](https://hmv.com) (human verification page)  
- [Magic Madhouse](https://magicmadhouse.co.uk) (false positives for in-stock items)

---

## Installation

1. Clone the repository or copy the script to your local machine.  
2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

