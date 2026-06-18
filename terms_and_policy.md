# Terms of Service for Spectre Music Search Bot

**Effective Date:** June 19, 2026

By adding or using Spectre Music Search Bot ("the Bot") in your Discord server, you agree to the following terms:

### 1. Intended Use
The Bot is designed exclusively to monitor specified channels, parse music links, and maintain a shared community index of track mashups. You agree not to abuse the Bot, attempt to exploit its codebase, or disrupt its hosting infrastructure.

### 2. Limitations of Liability
The Bot is provided "as is" without warranties of any kind. The developers and hosts are not liable for any service interruptions, loss of database records, or unintended behaviors resulting from api updates or network issues.

### 3. Compliance with Discord Terms
Users must adhere to the official Discord Terms of Service and Community Guidelines while interacting with the Bot. Any content shared through the Bot that violates Discord's core guidelines may result in a ban from using the Bot.

### 4. Modifications
These terms may be updated periodically to reflect changes in functionality or platform regulations. Continued use of the Bot constitutes acceptance of updated terms.

---

# Privacy Policy for Spectre Music Search Bot

**Effective Date:** June 19, 2026

This Privacy Policy explains how Spectre Music Search Bot ("the Bot") collects, uses, and stores data within Discord servers.

### 1. Data We Collect
The Bot only processes data necessary for its core functionality (tracking music links and mashups):
* **Message Content:** The Bot monitors text channels designated by the server administrator (`MASHUP_CHANNEL_IDS`). It only scans and processes messages containing valid URLs (e.g., YouTube, streaming platform links). It does not read, log, or store regular text conversations.
* **User Identifiers:** The Bot stores the unique, numerical Discord User ID of the individual who posted the music link, alongside the metadata of the shared link.
* **Guild/Channel IDs:** The Bot stores numerical server and channel IDs to route and associate track data properly.

### 2. How We Use Data
Collected data is used strictly to maintain a persistent ledger of shared music tracks within the server. We do not use this data for tracking across multiple unrelated servers, and we never share, sell, or distribute this data to third parties.

### 3. Data Retention and Deletion
Data is stored securely in a private PostgreSQL database managed entirely by the server host. Users can request the removal of their stored link history at any time by contacting the bot administrator or server host.

### 4. Contact
For privacy inquiries or data removal requests, please contact the repository maintainer via GitHub or open an issue on this repository.
