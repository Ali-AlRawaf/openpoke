# OpenPoke 🌴

OpenPoke is a simplified, open-source take on [Interaction Company’s](https://interaction.co/about) [Poke](https://poke.com/) assistant—built to show how a multi-agent orchestration stack can feel genuinely useful. It keeps the handful of things Poke is great at (email triage, reminders, and persistent agents) while staying easy to spin up locally.

- Multi-agent FastAPI backend that mirrors Poke's interaction/execution split, powered by [OpenRouter](https://openrouter.ai/).
- Gmail tooling via [Composio](https://composio.dev/) for drafting/replying/forwarding without leaving chat.
- Trigger scheduler and background watchers for reminders and "important email" alerts.
- Next.js web UI that proxies everything through the shared `.env`, so plugging in API keys is the only setup.

## Requirements
- Python 3.10+
- Node.js 18+
- npm 9+

## Quickstart
1. **Clone and enter the repo.**
   ```bash
   git clone https://github.com/shlokkhemani/OpenPoke
   cd OpenPoke
   ```
2. **Create a shared env file.** Copy the template and open it in your editor:
   ```bash
   cp .env.example .env
   ```
3. **Get your API keys and add them to `.env`:**
   
   **OpenRouter (Required)**
   - Create an account at [openrouter.ai](https://openrouter.ai/)
   - Generate an API key
   - Replace `your_openrouter_api_key_here` with your actual key in `.env`
   
   **Composio (Required for Gmail)**
   - Sign in at [composio.dev](https://composio.dev/)
   - Create an API key
   - Set up Gmail integration and get your auth config ID
   - Replace `your_composio_api_key_here` and `your_gmail_auth_config_id_here` in `.env`
4. **(Required) Create and activate a Python 3.10+ virtualenv:**
   ```bash
   # Ensure you're using Python 3.10+
   python3.10 -m venv .venv
   source .venv/bin/activate
   
   # Verify Python version (should show 3.10+)
   python --version
   ```
   On Windows (PowerShell):
   ```powershell
   # Use Python 3.10+ (adjust path as needed)
   python3.10 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   
   # Verify Python version
   python --version
   ```

5. **Install backend dependencies:**
   ```bash
   pip install -r server/requirements.txt
   ```
6. **Install frontend dependencies:**
   ```bash
   npm install --prefix web
   ```
7. **Start the FastAPI server:**
   ```bash
   python -m server.server --reload
   ```
8. **Start the Next.js app (new terminal):**
   ```bash
   npm run dev --prefix web
   ```
9. **Connect Gmail for email workflows.** With both services running, open [http://localhost:3000](http://localhost:3000), head to *Settings → Gmail*, and complete the Composio OAuth flow. This step is required for email drafting, replies, and the important-email monitor.

The web app proxies API calls to the Python server using the values in `.env`, so keeping both processes running is required for end-to-end flows.

## Project Layout
- `server/` – FastAPI application and agents
- `web/` – Next.js app
- `server/data/` – runtime data (ignored by git)

## Known Issues
- **Concurrent tasks on one agent share a log.** The execution batch manager doesn't queue tasks per agent, so two tasks sent to the same agent run at once and interleave in its log (and in the log slice its card update reads). Card updates for one agent are serialized, but the executions aren't. Fix: a per-agent queue in `ExecutionBatchManager`.
- **Overlapping agent searches can lose a cached vector.** `EmbeddingStore.save()` (`server/services/execution/agent_search.py`) prunes the in-memory cache to the roster it just saw. If another search is still ranking an older version of the roster (a card changed in between), its texts can disappear mid-search; that search raises and `search_agents` falls back to the names-only roster for that one call. Rare (needs two concurrent IA turns plus a card update). Fix: prune only the file on disk, at the cost of keeping stale vectors in memory until restart.

- **Trigger fires never update the agent's card.** Only `send_message_to_agent` writes an `agent_request` log line; the trigger scheduler calls `ExecutionBatchManager.execute_agent()` directly, so a fire leaves no request line. The card updater finds its task by matching the request text, finds none, and skips the update, so what a fire did never reaches the card (the next IA task's update starts at its own request, after the fire's lines). The execution agent's own history also shows each fire's actions but not what it was asked. Fix: move the `record_request` call from `send_message_to_agent` into `ExecutionBatchManager.execute_agent()` so every task logs its request. (The routing-eval fixtures model today's behaviour, so their cards would need regenerating to reflect the fix.)

## License
MIT — see [LICENSE](LICENSE).
