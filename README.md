# Lesson 48 practical application: Bounded Deployment Worker

**Author: Luis Coco Enríquez**

**Course mapping:** LinkedIn Post 49 · source Lesson 48.

**Lesson:** Deploy and Scale Multi-Agent Applications

## Purpose and concepts

Run a request batch with bounded concurrency and produce an explicit local deployment configuration.

This is a standalone student application. Its main teaching code is in [workflow.py](workflow.py), with executable sample input in [data/input.json](data/input.json). The lesson-specific algorithm actually runs in both modes. Only model responses change: offline mode uses clearly labelled deterministic fixtures; live mode invokes the Claude Agent SDK.

The following table relates the application to the original lesson topics. The runnable example concentrates on the core workflow; hosting, external infrastructure and wider production practices remain extensions where indicated.

| Lesson topic | Context from the lesson |
| --- | --- |
| Prepare the Application | Prepare the application before deployment. |
| Configure Environments Safely | Configure development and production through validated server-side settings. |
| Containerize the App | Containerize the complete application with its tested dependencies, code, entry point, and any required SDK runtime. |
| Choose a Hosting Model | Choose a hosting model that fits the workload. |
| Scale and Protect the Workflow | Scale with explicit limits. |
| Maintain and Improve in Production | Operate the deployment with stage-level monitoring, representative evaluation, and a controlled release process. |

## Files

| File | Responsibility |
| --- | --- |
| `app.py` | CLI, configuration, fresh output folders and explicit error exit codes. |
| `workflow.py` | The lesson-specific control flow and domain checks. Start reading here. |
| `runtime.py` | Offline/live adapter, checked structured responses, SDK lifecycle and stage events. |
| `lesson.json` | Application metadata, source topic references and the exercise. |
| `data/input.json` | Editable, fictional teaching data. |
| `requirements.txt` | SDK version pinned to the locally inspected API. |
| `test_app.py` | Offline domain checks and workspace-boundary test. |
| `examples/offline_report.json` | Saved result from a verified offline execution. |
| `outputs/<run>/` | Report, trace and any lesson-specific artifacts from a new run. |

## Configure the application

Use Python 3.10 or newer. Offline mode uses only the standard library and needs no key. Live mode uses `claude-agent-sdk==0.2.175` and configured Anthropic credentials (or supported local Claude authentication).

Open a terminal in this `Practical Application Example` folder.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "your-anthropic-api-key"
.\.venv\Scripts\python.exe app.py --offline
```

macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-anthropic-api-key"
.venv/bin/python app.py --offline
```

You can call the virtual environment's Python directly; activation is optional. Below, `python` means that interpreter. Credentials stay in the environment; the app does not load `.env` files. Supported SDK wheels bundle the Claude executable; consult the official setup documentation if your platform requires a separate CLI installation.

## Run the application

```bash
# Inspect configuration and sample input without running the workflow.
python app.py --dry-run

# Execute the real local algorithm with labelled response fixtures (default).
python app.py --offline

# Display fragments where this lesson includes a streaming stage.
python app.py --offline --stream

# Use the real Claude Agent SDK. This makes paid model calls on your account.
python app.py --live

# Override input, model and operating limits.
python app.py --live --input data/input.json --model YOUR_MODEL_ID --max-turns 8 --budget-usd 1 --timeout 90

# Verify the local teaching behavior, without API calls.
python -m unittest discover -v
```

`--output-dir` must name a new directory, so a failed run cannot overwrite a previous successful report. Input paths passed on the command line are relative to your terminal; bundled data paths resolve relative to the application. Every run writes `trace.json`; successful runs also write `report.json`, and failed runs write `failure.json` and exit with code 1. A completed report can still contain `accepted: false`, abstention or an escalation; completion does not mean a business approval.

`--fail-stage NAME` injects one transient failure at a named stage, allowing recovery exercises without breaking a real service. Use stage names from `workflow.py` or `trace.json`. `--approve` applies only to local approval exercises; it never authorizes external publication, purchases or messages.

Optional container rehearsal (requires Docker and internet access when building):

```bash
docker build -t lesson48-practical .
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,size=128m lesson48-practical python app.py --offline --output-dir /tmp/run
```

The container command runs only the offline exercise. A live model connection needs a separately designed network and credential policy. The generator does not build, start, publish or deploy containers.

## How the application was built

The workflow defines its own data checks and coordination behavior. Functions in this lesson are `run`. The host Python code owns branching, loops, scoring, file writes and acceptance decisions. A model stage receives only the evidence explicitly passed to `agent.ask`.

```python
async def run(agent, data):
    workers = data['workers']
    if type(workers) is not int or not 1 <= workers <= 3:
        raise ValueError('Use one to three workers')
    semaphore = asyncio.Semaphore(workers)
    async def worker(index, job):
        async with semaphore:
            return await agent.ask('job_' + str(index), 'Complete the assigned short summary.', job, 'Completed summary for: ' + job)
    results = await asyncio.gather(*(worker(i, job) for i, job in enumerate(data['jobs'])))
    config = {'workers': workers, 'requests': len(results), 'credentials': 'environment only', 'hosted': False}
    atomic_json(agent.output / 'deployment_config.json', config)
    return {'results': results, 'configuration': config}
```

Read the code in this order:

1. Inspect `data/input.json` and identify the input assumptions and units.
2. Follow `run(agent, data)` and any local helper functions. Conditions and loops determine which stages actually execute.
3. At each `agent.ask(stage, instruction, evidence, example)`, distinguish the instruction from evidence. `example` is the offline response fixture and structured-output shape, not a successful live result.
4. Follow each returned value into the next stage or host check. In live mode nontext responses use an SDK JSON schema and are checked again locally; semantic rules still belong in this workflow.
5. Inspect the returned report and any separately saved artifact. Use the trace to distinguish stage completion from an accepted final deliverable.

In `runtime.py`, live requests open `ClaudeSDKClient` with an asynchronous context manager, call `query`, consume `receive_response` to the end, and require a successful final `ResultMessage`. The adapter records `is_error`, subtype, session ID, turn count and cost when available. Empty or missing final results, invalid shapes and raised SDK exceptions are treated as failures. SDK tools are disabled by default and are enabled only where this workflow supplies explicit options. `cwd` is not an OS sandbox.

The runtime admits up to three concurrent stages and caps the number of calls. Turn limits and per-call timeouts are configurable. Observed costs are accumulated across calls; in-flight work, subagents and provider reporting can make exact spend differ from estimates. Session examples consume each answer before sending the next question. Never mistake a saved ID, UI history or prompt role for persistent storage or an isolation boundary.

## Expected behavior and verification

The saved [offline report](examples/offline_report.json) shows the fixture result, explicitly marked `offline_teaching_fixture`. The trace demonstrates the actual local control flow. Deterministic checks exercise the lesson's domain behavior rather than checking a model's wording.

Live answers can differ. Local tests and SDK option checks do not prove live model quality, provider access, Docker isolation or deployed behavior. Live API calls are not part of the offline test suite. For a live smoke test, inspect final run status, source support, domain gates and saved artifacts together.

## Student exercise

Change the worker limit and inspect stage overlap in trace.json. Build the supplied Docker image without publishing it.

Change one input or fixture at a time, rerun the tests, and explain the changed branch or acceptance decision. Offline responses are fixed fixtures: they are not a model and may intentionally stop matching a changed dataset. Update the fixture deliberately or compare with a live run; do not treat fixture wording as freshly computed evidence.

## Limits and troubleshooting

This is a focused local teaching application, not a deployed production service. The bundled data is fictional, and model output still needs evidence-based review.

- Missing SDK import: install `requirements.txt` using the same interpreter that runs `app.py`.
- Authentication or provider failure: check server-side credentials and connectivity; the failure artifact does not count as a successful answer.
- Invalid sample input: read the domain check in `workflow.py` and keep required fields and types.
- Missing saved session or memory: run the initialization exercise first and use the same workspace, owner and execution mode.
- UI import error: install the optional UI requirements before launching `ui.py`.
- Unavailable tools or CLI: check the pinned SDK version and the official setup requirements.

## Primary documentation

- [Anthropic Python Agent SDK reference](https://code.claude.com/docs/en/agent-sdk/python)
- [Official Python SDK source and examples](https://github.com/anthropics/claude-agent-sdk-python)
- [Custom tools](https://code.claude.com/docs/en/agent-sdk/custom-tools)
- [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions)

The SDK configuration was checked against the installed `0.2.175` types. The lesson topics above come from this lesson's existing storyboard; the application does not modify that storyboard or any videos.
