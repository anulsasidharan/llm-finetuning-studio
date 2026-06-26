# YouTube Demo Script — LLM Fine-Tuning Studio
# OrionVexa | github.com/anulsasidharan/llm-finetuning-studio

**Target length:** 14–16 minutes  
**Format:** Screen recording + voiceover (OBS / Loom / Descript)  
**Demo scenario:** Fine-tuning Llama 3.1 8B with QLoRA for a customer-support chatbot, then deploying to HuggingFace Hub  
**Recording resolution:** 1920×1080, browser zoom 90%, font size bumped in IDE if showing code  

---

## Pre-Recording Checklist

- [ ] `make dev` running — all containers healthy (`make ps`)
- [ ] Browser open at http://localhost:3000 — logged in as demo user
- [ ] Seed data loaded (`make seed`) — model catalog + GPU pricing populated
- [ ] Sample dataset ready: `docs/demo-assets/customer_support_alpaca.jsonl` (100 rows, Alpaca format)
- [ ] Browser tabs open: dashboard, API docs (http://localhost:8000/docs), GitHub repo
- [ ] Close notifications, Slack, email — full-screen mode
- [ ] Mic check complete, background noise eliminated

---

## Demo Assets

Create these files before recording:

### `docs/demo-assets/customer_support_alpaca.jsonl`
A small 100-row JSONL in Alpaca format. Each line:
```json
{"instruction": "How do I reset my password?", "input": "", "output": "To reset your password, click 'Forgot Password' on the login page, enter your email address, and follow the instructions sent to your inbox. The reset link expires in 30 minutes."}
```

Mix in ~5 near-duplicate rows so the quality checker has something to flag.

---

## Scene-by-Scene Script

---

### SCENE 1 — Hook (0:00–0:30)

**[Screen: Terminal — `make dev` output scrolling, then `make ps` showing all containers green]**

> "Fine-tuning a large language model sounds complicated — new infrastructure, GPU wrangling, alignment techniques, evaluation — it usually takes weeks to set up from scratch."
>
> "This is LLM Fine-Tuning Studio. An end-to-end platform that takes you from zero to a deployed fine-tuned model, entirely from a web browser."
>
> "Let me walk through the full journey right now."

**[Cut to browser — http://localhost:3000 dashboard]**

---

### SCENE 2 — Platform Overview (0:30–1:30)

**[Screen: Dashboard home page — sidebar visible, all module icons rendered]**

> "The platform is organized into ten modules that mirror the actual fine-tuning workflow."
>
> "On the left: Onboarding, Dataset Studio, Methodology Selector, Config Builder, GPU Selector, Cost Estimator — that's your setup phase."
>
> "On the right: Live Training Dashboard, Evaluation Playground, Experiment Tracker, Deploy & Export — that's your run-and-ship phase."
>
> "There's also a Learning Center for anyone who wants to understand the theory behind what they're clicking."

**[Hover sidebar items one by one — 2 seconds each]**

> "The full stack: Next.js 14 on the frontend, FastAPI backend, PostgreSQL, Redis, MinIO for storage, Celery for async tasks, and the training engine is built on HuggingFace PEFT and TRL."
>
> "Everything runs in Docker. One `make dev` and the whole platform is live."

---

### SCENE 3 — Onboarding Wizard (1:30–3:30)

**[Screen: Navigate to /onboarding]**

> "Let's say you're brand new to fine-tuning. You hit Onboarding."

**[Click 'I'm new to fine-tuning']**

> "The wizard asks what you want to achieve — in plain language."

**[Select: 'Improve responses for a specific domain or task']**

> "Based on your answers it routes you to the right methodology. Under the hood it's scoring your requirements against VRAM budget, dataset size, alignment needs, and complexity tolerance."

**[Advance through wizard screens — show the animated LoRA diagram]**

> "Each step has visual explainers. This one walks through how LoRA inserts low-rank adapter matrices instead of updating the full weight matrix — the frozen layers in blue, the adapter in orange."

**[Reach the recommendation screen — QLoRA is recommended]**

> "The recommendation: QLoRA. 4-bit quantized base model with LoRA adapters. It fits a 7B model on a single 24GB GPU and still gets you 90% of the fine-tuning quality of full-precision SFT."
>
> "If you already know what you're doing, you can skip the wizard entirely and jump straight to any module."

---

### SCENE 4 — Dataset Studio (3:30–6:30)

**[Screen: Navigate to /datasets]**

> "Every fine-tuning job starts with data. Dataset Studio handles upload, format conversion, and quality checking."

**[Click 'Upload Dataset']**

> "I'm uploading a customer support Q&A dataset — 100 rows, Alpaca format."

**[Drag and drop `customer_support_alpaca.jsonl`]**

> "The uploader validates MIME type and file size on the way in. Files land in MinIO — the S3-compatible object store running locally."

**[Upload completes — dataset card appears]**

> "Now let's run the format checker."

**[Click 'Format' → select 'Alpaca']**

> "The formatter confirms the dataset is already in Alpaca format. It can convert from ShareGPT or ChatML if needed — useful when you're pulling data from existing chat logs."

**[Click 'Run Quality Check']**

> "Quality check runs three passes: deduplication, statistics, and language detection."

**[Quality report renders — show duplicate rows flagged, token length histogram, language breakdown]**

> "Five near-duplicate rows detected. The quality report shows which rows they are, the similarity score, and a recommendation to remove them before training."
>
> "Token length histogram: mostly under 300 tokens, one outlier at 900. That outlier might cause issues if the model's context window is tight — worth checking."
>
> "Language: 100% English. Good."

**[Click 'Preview' — show the first 5 rows rendered as instruction/output pairs]**

> "The preview renders each record as it will appear to the trainer — the instruction, optional input, and output. No surprises at training time."

---

### SCENE 5 — Methodology Selector (6:30–8:00)

**[Screen: Navigate to /methodology]**

> "Now we choose how we fine-tune. Methodology Selector lays out all six methods side by side."

**[Show the comparison table — SFT, LoRA, QLoRA, DPO, ORPO, RLHF]**

> "SFT: simplest, updates every weight, needs the most VRAM. Full fine-tuning a 7B model requires about 80GB — that's multiple A100s."
>
> "LoRA: injects low-rank adapter matrices, freezes the base. Drops VRAM to about 40% of full. Great for most tasks."
>
> "QLoRA: LoRA on top of a 4-bit quantized base. Drops to 15% of full VRAM. This is the one I'd use for most production fine-tuning today."
>
> "DPO, ORPO: alignment methods — you supply preferred/rejected response pairs, and the model learns to prefer the good ones. No separate reward model needed."
>
> "RLHF: the gold standard for alignment — PPO with a reward model. Most complex, most expensive, most data. Used by OpenAI, Anthropic for their RLHF stages."

**[Click 'QLoRA' — select it]**

> "We're going with QLoRA. The card shows the expected VRAM usage, minimum sample size, and the TRL/PEFT trainer classes it maps to."

---

### SCENE 6 — Training Config Builder (8:00–10:00)

**[Screen: Navigate to /config]**

> "Config Builder is where you set every hyperparameter. The design principle here: every parameter has an inline tooltip that explains what it does and a typical range — no documentation tab-switching."

**[Hover over 'Learning Rate' field — tooltip appears]**

> "Learning rate: 2e-4 is the typical starting point for QLoRA. Tooltip explains the cosine vs linear schedule tradeoff."

**[Walk through key sections]**

> "Model: we're using `meta-llama/Llama-3.1-8B-Instruct`."
>
> "LoRA config: rank 16, alpha 32, dropout 0.05. Target modules: q_proj and v_proj — the query and value projection layers."
>
> "Quantization: 4-bit NF4 with double quantization. Double quantization adds a second level of quantization to the quantization constants themselves — saves another 0.37 bits per parameter."
>
> "Training: 3 epochs, batch size 4, gradient accumulation 4, warmup ratio 0.03."

**[Show the 'Validate Config' button — click it]**

> "Validation runs the config through a Pydantic schema before it ever hits the queue. Catch mismatches between methodology and config here — like trying to set DPO parameters on an SFT trainer."

**[Config passes — green checkmark]**

---

### SCENE 7 — GPU Selector + Cost Estimator (10:00–11:30)

**[Screen: Navigate to /gpu-selector]**

> "GPU Selector pulls live pricing from RunPod and Lambda Labs. The data is cached in Redis with a 15-minute TTL so the page loads instantly on repeat visits."

**[Show GPU cards — A100 40GB, A100 80GB, H100, RTX 4090]**

> "Each card shows the GPU model, VRAM, hourly rate, provider, and an estimated time to complete our specific job based on the config we just built."

**[Filter by provider: RunPod]**

> "For QLoRA on an 8B model, the A100 40GB is the sweet spot — enough VRAM with room to spare."

**[Click 'Estimate Cost']**

> "Cost Estimator does a pre-flight calculation. It takes the model size, dataset size, epoch count, batch configuration, and GPU throughput to project a total training cost before we commit a single dollar."

**[Cost breakdown appears]**

> "Estimated compute: $4.20. Storage for artifacts: $0.12. Total: $4.32 for this training run."
>
> "This is a real number, not a rough estimate — it's derived from the token throughput benchmarks for that specific GPU model."

---

### SCENE 8 — Launching + Live Training Dashboard (11:30–13:30)

**[Screen: Navigate back to config → click 'Launch Job']**

> "Launch. This creates a job record in PostgreSQL, pushes a Celery task to the Redis broker, and the training engine picks it up."

**[Navigate to /training — job card appears with 'queued' status]**

**[Click into the job → Live Training Dashboard]**

> "The dashboard connects to a WebSocket. The training engine publishes metrics to a Redis channel every N steps; the backend subscribes and forwards to all connected browser clients in real time."

**[Show live charts — loss curves, GPU utilization, VRAM usage, tokens/sec]**

> "Loss curves: training loss in blue, eval loss in orange. We're watching for the gap between them — a widening gap means overfitting."
>
> "GPU utilization at 94% — that's good. Below 80% often means the data loader is the bottleneck, not compute."
>
> "VRAM: 18GB of 40GB used. Headroom to push batch size if needed on a re-run."
>
> "ETA updates every 30 seconds based on the current throughput. We're projecting 12 minutes remaining."

**[Show 'Pause' and 'Cancel' controls]**

> "Training controls: pause checkpoints the model state to MinIO mid-run. Cancel terminates the Celery task and saves the last checkpoint. You're never losing training progress."

---

### SCENE 9 — Evaluation Playground (13:30–15:00)

**[Screen: Navigate to /evaluation — job shows 'completed']**

> "Training complete. Now we evaluate."

**[Click into Evaluation Playground — side-by-side comparison view]**

> "Left column: the base model — `Llama-3.1-8B-Instruct` with no fine-tuning. Right column: our fine-tuned adapter applied on top."

**[Type a prompt: 'How do I escalate a billing dispute?']**

**[Both columns generate responses — show side by side]**

> "The base model gives a generic answer. The fine-tuned version uses the exact tone and structure from the training data — mentions the billing portal, specific timelines, the escalation path."

**[Click 'Run Benchmark' — show MMLU / HellaSwag / ARC scores]**

> "Benchmark suite: MMLU, HellaSwag, ARC. These are standard academic benchmarks that test general reasoning — we run them to make sure fine-tuning on our domain data didn't cause catastrophic forgetting on general tasks."
>
> "Numbers look stable. We haven't lost general capability."

**[Show the Experiment Tracker link]**

> "Every evaluation run is logged to the Experiment Tracker automatically — config, metrics, artifacts, all versioned."

---

### SCENE 10 — Experiment Tracker (15:00–15:45)

**[Screen: Navigate to /experiments]**

> "Experiment Tracker is where all your runs live. Each card shows the job ID, methodology, dataset version, final loss, eval benchmark scores, and training cost."

**[Click 'Compare' — select two experiment runs]**

> "The comparison view diffs the configs side by side and overlays the loss curves. This is how you iterate — change one hyperparameter, re-run, compare."

**[Show version columns — rank 8 vs rank 16 LoRA]**

> "Here: rank-8 adapter vs rank-16. Rank 16 got lower eval loss but cost 20% more and trained 15% slower. Depending on the use case, rank 8 might be the right trade."

---

### SCENE 11 — Deploy & Export Manager (15:45–17:00)

**[Screen: Navigate to /deploy]**

> "The fine-tuned model is stored in MinIO as a LoRA adapter checkpoint. Deploy & Export Manager gives you three paths out."

**[Show three export options: HuggingFace Hub Push, GGUF Export, vLLM Deploy]**

> "HuggingFace Hub: merges the LoRA adapter into the base model weights using PEFT's `merge_and_unload`, then pushes the full model to your HuggingFace repo. One click."

**[Click 'Push to HuggingFace' — fill in repo name and token, click Push]**

> "This calls the `push_hf.py` export script — it handles the merge, creates a model card with the config and benchmark scores, and pushes."

**[Show GGUF Export option]**

> "GGUF export runs `llama.cpp` quantization on the merged model. Q4_K_M is the default — 4-bit quantization with K-means clustering. The output is a single `.gguf` file you can run on a MacBook with Ollama or llama.cpp."

**[Show vLLM Deploy option]**

> "vLLM deploy spins up a container running vLLM with the merged model, exposes a REST endpoint compatible with the OpenAI API spec. You get curl-able inference in 30 seconds."

---

### SCENE 12 — Learning Center (17:00–17:45)

**[Screen: Navigate to /learning-center]**

> "Learning Center is for anyone who wants to understand what's happening under the hood — not just click through it."

**[Show topic cards: LoRA, QLoRA, DPO, ORPO, RLHF, Tokenization, Loss Functions, VRAM Math]**

**[Click 'QLoRA' article]**

> "Each article covers the concept, the key equations, and the practical implications for your config choices. The QLoRA article walks through NF4 quantization, double quantization, and paged optimizer memory — with diagrams."

**[Scroll through article — show the NF4 distribution diagram and the VRAM comparison table]**

> "The VRAM math table is the one I refer to most: given a model size, it shows you exactly how much VRAM you need for full fine-tuning, LoRA, and QLoRA. No more guessing whether your GPU is big enough."

---

### SCENE 13 — Production Stack (17:45–18:30)

**[Screen: Switch to VS Code — briefly show docker-compose.prod.yml]**

> "The platform ships production-ready. `docker-compose.prod.yml` builds optimized Docker images — Next.js is compiled to a standalone bundle, FastAPI runs under Gunicorn with 4 Uvicorn workers."

**[Switch to GitHub — show the Actions tab, CI/CD workflows]**

> "GitHub Actions CI runs on every PR: lint, type-check, unit tests for backend and training engine, frontend build. Four jobs in parallel."
>
> "CD on push to main: builds and pushes production images to GitHub Container Registry, then SSH-deploys to the production server."

**[Show Security workflow — Trivy scans]**

> "Security: Trivy scans both images and the repository filesystem for CRITICAL and HIGH CVEs weekly, with SARIF reports uploaded to GitHub's Security tab."

**[Show Dependabot config]**

> "Dependabot auto-opens PRs for stale GitHub Actions, npm packages, and Python deps. The npm updates group Radix UI and TanStack separately so they don't all land in one massive PR."

---

### SCENE 14 — Outro + CTA (18:30–19:00)

**[Screen: Dashboard — all modules visible]**

> "That's the full platform: onboarding to deployment, covered end-to-end."
>
> "The repo is open source at github.com/anulsasidharan/llm-finetuning-studio. Everything you saw today — training engine, backend, frontend — is in there."
>
> "If you're building something with fine-tuning and want to talk: Anu Sasidharan, OrionVexa — links in the description."
>
> "Like and subscribe if you want to see what comes next."

**[End card with: GitHub repo link, OrionVexa logo]**

---

## Shot List Summary

| # | Scene | Duration | Key Screen |
|---|-------|----------|------------|
| 1 | Hook — `make dev` + `make ps` | 0:30 | Terminal |
| 2 | Platform overview — dashboard + sidebar | 1:00 | Browser: / |
| 3 | Onboarding wizard | 2:00 | Browser: /onboarding |
| 4 | Dataset Studio — upload, format, QC | 3:00 | Browser: /datasets |
| 5 | Methodology Selector — QLoRA | 1:30 | Browser: /methodology |
| 6 | Training Config Builder | 2:00 | Browser: /config |
| 7 | GPU Selector + Cost Estimator | 1:30 | Browser: /gpu-selector |
| 8 | Launch + Live Training Dashboard | 2:00 | Browser: /training/[id] |
| 9 | Evaluation Playground | 1:30 | Browser: /evaluation |
| 10 | Experiment Tracker | 0:45 | Browser: /experiments |
| 11 | Deploy & Export Manager | 1:15 | Browser: /deploy |
| 12 | Learning Center | 0:45 | Browser: /learning-center |
| 13 | Production stack — Docker + CI/CD | 0:45 | VS Code + GitHub |
| 14 | Outro + CTA | 0:30 | Browser: / |
| **Total** | | **~19:00** | |

---

## Recording Tips

- **Cursor:** Use a cursor-highlighting tool (e.g., [Cursor Highlighter](https://github.com/nicowillis/cursor-highlight)) — viewers lose the cursor on screen shares.
- **Pacing:** Aim for 3–4 sentences per visible action. Don't hover on loading states — cut with jump-cut editing.
- **Mistakes:** Keep rolling. Edit out flubs in post. Don't re-record entire scenes for minor stumbles.
- **B-roll:** After the main recording, capture 10-second clips of each module's key screen for use as intro overlays.
- **Thumbnail:** Dashboard view with all charts live, loss curves visible, OrionVexa logo top-right.

## Editing Notes

- Add chapter markers matching the scene numbers above — YouTube autogenerates the chapter list from timestamps in the description.
- Intro/outro music: royalty-free, keep at -18dB under voice.
- Add lower thirds for new sections (e.g., "DATASET STUDIO" text overlay).
- Zoom-in on small UI text (tooltip content, config field values) using screen zoom / video zoom in editing.

---

## YouTube Description Template

```
LLM Fine-Tuning Studio — full platform demo.

In this video I walk through every module of LLM Fine-Tuning Studio, an open-source end-to-end platform for fine-tuning large language models. We go from raw dataset to a deployed QLoRA fine-tuned Llama 3.1 8B model, step by step.

⏱ Chapters:
0:00 Intro — why this exists
0:30 Platform overview
1:30 Onboarding wizard
3:30 Dataset Studio
6:30 Methodology Selector
8:00 Training Config Builder
10:00 GPU Selector + Cost Estimator
11:30 Launching + Live Training Dashboard
13:30 Evaluation Playground
15:00 Experiment Tracker
15:45 Deploy & Export Manager
17:00 Learning Center
17:45 Production stack (Docker + CI/CD)
18:30 Outro

🔗 Links:
GitHub: https://github.com/anulsasidharan/llm-finetuning-studio
OrionVexa: https://orionvexa.ca

🛠 Stack: Next.js 14 · FastAPI · PostgreSQL · Redis · MinIO · Celery · HuggingFace PEFT/TRL · Docker · GitHub Actions

#LLM #FineTuning #LoRA #QLoRA #MachineLearning #OpenSource #FastAPI #NextJS
```
