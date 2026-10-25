# MindWeave

MindWeave is a local, contract-aware visual orchestrator for reliable multi-agent workflows. It provides deterministic Demo Mode, mandatory human release approval, workflow templates, reusable workflow modules, and a simple virtual-wallet guardrail.

## Windows quick start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Tests: `pytest backend/tests`.

## Demo

Sign in (a local account starts at ₹70), choose a starter workflow, click **Run workflow**, then approve the mandatory Human Approval node. Work is fully local; no keys are needed in Demo Mode.
