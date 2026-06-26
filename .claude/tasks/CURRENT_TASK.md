# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE3-009
## TASK NAME: training_engine/export/push_hf.py
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 3, Week 9
## BRANCH: feat/PHASE3-009-push-hf

## NEXT TASK
PHASE3-010 (training_engine/export/export_gguf.py) — depends on PHASE3-008 (done).

## SUMMARY (this session, 2026-06-25)
Implemented `training_engine/export/push_hf.py` — standalone module that uploads
any local model directory (merged model, LoRA adapter, SFT checkpoint, etc.) to
the HuggingFace Hub using `huggingface_hub.HfApi`.

**Design decisions:**
- `push_to_hub(model_dir, repo_id, *, hf_token=None, private=False, commit_message=None, trust_remote_code=False)`
  is the single public entry point — same flat-function style as `merge_lora.py`
- Uses `HfApi.create_repo(exist_ok=True)` + `HfApi.upload_folder()` rather than
  loading the model into memory — works for any file format (safetensors, GGUF, etc.)
- `HfApi(token=hf_token)` sets the token at the instance level so it isn't
  repeated on every method call; `None` defers to HuggingFace's standard env var
  (`HUGGING_FACE_HUB_TOKEN`) / cli-login cache
- `repo_url` constructed as `f"https://huggingface.co/{repo_id}"`;
  `commit_url` taken from `CommitInfo.commit_url` returned by `upload_folder`
- `trust_remote_code` accepted for API symmetry with `merge_lora` but not used
  (file upload path has no model loading)
- `PushHFError(ValueError)` — consistent with `MergeLoRAError`, `TrainerError`, etc.
- Lazy import via `_get_hf_api_cls()` — same testability pattern as all trainers;
  `huggingface_hub` is installed in the real env but mocked entirely in tests

**Verification:**
- 7 unit tests in `tests/test_push_hf.py`:
  - 3 error paths: missing model_dir, empty repo_id, whitespace-only repo_id
  - 4 happy paths: full success flow (verifies create_repo + upload_folder kwargs +
    return dict), private=True propagation, custom commit message, default message
- Full suite: 148/148 passing (was 141 + 7 new)
- `ruff check` and `ruff format --check` both clean on new files
- Pre-commit hook passed (ruff lint + format stages)

## GOTCHAS LOGGED
- None new.
