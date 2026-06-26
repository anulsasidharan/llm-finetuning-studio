import type { Methodology } from "@/types"
import { METHODOLOGY_INFO } from "@/lib/methodology-data"

export type LearningCategory = "foundations" | "datasets" | "methodologies" | "concepts"

export type LearningCategoryMeta = {
  id: LearningCategory
  label: string
  description: string
}

export type LearningSection = {
  heading?: string
  body?: string
  bullets?: string[]
  callout?: {
    variant: "tip" | "info" | "warning"
    title?: string
    text: string
  }
}

export type LearningTopic = {
  id: string
  category: LearningCategory
  title: string
  summary: string
  methodology?: Methodology
  relatedLinks?: { label: string; href: string }[]
  sections: LearningSection[]
}

export const LEARNING_CATEGORIES: LearningCategoryMeta[] = [
  {
    id: "foundations",
    label: "Foundations",
    description: "Core ideas before you touch a config",
  },
  {
    id: "datasets",
    label: "Datasets",
    description: "Formats, quality, and preference data",
  },
  {
    id: "methodologies",
    label: "Methodologies",
    description: "How each fine-tuning method works",
  },
  {
    id: "concepts",
    label: "Key concepts",
    description: "VRAM, alignment, loss, and adapters",
  },
]

const METHODOLOGY_EXPLAINERS: Record<
  Methodology,
  { analogy: string; whenToUse: string[]; watchOut: string }
> = {
  sft: {
    analogy:
      "Like re-reading a textbook cover to cover — every weight in the model can change, so it learns deeply but needs the most VRAM.",
    whenToUse: [
      "You have a large GPU budget and want maximum task fidelity",
      "Your dataset is large (1,000+ examples) and domain-specific",
      "You plan to merge weights and deploy without adapter files",
    ],
    watchOut:
      "Full SFT on a 7B+ model typically needs 40–80 GB VRAM. On consumer GPUs, LoRA or QLoRA is almost always more practical.",
  },
  lora: {
    analogy:
      "Like adding small sticky-note overlays on top of a frozen textbook — only the adapter matrices train, so you use far less memory.",
    whenToUse: [
      "You want strong results on a single mid-range GPU",
      "You have 500+ task examples and a clear output format",
      "You may train multiple task-specific adapters on one base model",
    ],
    watchOut:
      "Rank (r) controls adapter capacity — too low underfits, too high overfits small datasets and increases VRAM.",
  },
  qlora: {
    analogy:
      "LoRA plus a compressed 4-bit copy of the base model — the textbook is stored in shorthand, but the sticky notes still teach the new task.",
    whenToUse: [
      "You only have ~10–24 GB VRAM (e.g. RTX 3090, T4, A10)",
      "You are starting your first fine-tune and want the best cost/quality trade-off",
      "You need results close to full SFT without full SFT hardware",
    ],
    watchOut:
      "4-bit quantization adds a small quality gap vs full precision — usually negligible for instruction-following, more noticeable for reasoning-heavy tasks.",
  },
  dpo: {
    analogy:
      "Show the model pairs of good vs bad answers and nudge it toward the good ones — no separate reward model, but you need two full model copies in memory.",
    whenToUse: [
      "You have human preference pairs (chosen/rejected completions)",
      "You want alignment without training a reward model first",
      "Tone, safety, or style correction matters more than raw task accuracy",
    ],
    watchOut:
      "DPO keeps a frozen reference copy of the policy — expect roughly 2× LoRA VRAM. Pairs must be consistent; noisy preferences teach the wrong lesson.",
  },
  orpo: {
    analogy:
      "SFT and preference tuning in one pass — teach the task and the ranking at the same time instead of two separate training runs.",
    whenToUse: [
      "You have preference pairs but limited GPU time",
      "You want alignment on a LoRA-sized VRAM budget",
      "You are comparing against DPO and want a simpler pipeline",
    ],
    watchOut:
      "Still needs 1,000+ quality pairs. Beta controls how aggressively the model departs from its starting point — tune it in the Config Builder.",
  },
  rlhf: {
    analogy:
      "A student (policy) writes answers, a teacher (reward model) grades them, and reinforcement learning updates the student to maximize the grade.",
    whenToUse: [
      "You need gold-standard alignment for a production assistant",
      "You already have (or can train) a reliable reward model",
      "You have 10,000+ preference examples and significant compute",
    ],
    watchOut:
      "The most complex and VRAM-hungry path (~4× base model). Reward hacking is real — a flawed reward model teaches bad behavior confidently.",
  },
}

function methodologyTopics(): LearningTopic[] {
  return METHODOLOGY_INFO.map((info) => {
    const extra = METHODOLOGY_EXPLAINERS[info.methodology]
    return {
      id: info.methodology,
      category: "methodologies" as const,
      title: info.label,
      summary: info.keyDifferentiator,
      methodology: info.methodology,
      relatedLinks: [
        { label: "Methodology Selector", href: "/methodology" },
        { label: "Training Config", href: `/config?methodology=${info.methodology}` },
      ],
      sections: [
        {
          heading: "In one sentence",
          body: info.keyDifferentiator,
        },
        {
          heading: "Mental model",
          body: extra.analogy,
        },
        {
          heading: "Technical snapshot",
          bullets: [
            `Trainer: ${info.trainerClass}`,
            `VRAM: ${info.vramUsage}`,
            `Minimum data: ${info.minSamples}`,
          ],
        },
        {
          heading: "When to choose this",
          bullets: extra.whenToUse,
        },
        {
          callout: {
            variant: "warning",
            title: "Watch out",
            text: extra.watchOut,
          },
        },
      ],
    }
  })
}

export const LEARNING_TOPICS: LearningTopic[] = [
  {
    id: "what-is-fine-tuning",
    category: "foundations",
    title: "What is fine-tuning?",
    summary: "Specialising a pre-trained model on your task with example data.",
    relatedLinks: [
      { label: "Onboarding wizard", href: "/onboarding" },
      { label: "Dataset Studio", href: "/datasets" },
    ],
    sections: [
      {
        heading: "Pre-trained = general knowledge",
        body:
          "Base models (Llama, Mistral, Phi, etc.) are trained on trillions of tokens. They write fluently and know a lot — but they do not know your domain, your brand voice, or your output format.",
      },
      {
        heading: "Fine-tuning = specialisation",
        body:
          "You show the model hundreds or thousands of examples of the exact behaviour you want. Its weights update to reproduce that behaviour reliably — not just when you craft the perfect prompt.",
      },
      {
        heading: "What you get at the end",
        bullets: [
          "A merged full model (SFT) or a small adapter file (LoRA/QLoRA)",
          "Artifacts you can evaluate, version, export to GGUF, or push to HuggingFace Hub",
          "A deployable endpoint that behaves consistently on your task",
        ],
      },
      {
        callout: {
          variant: "tip",
          title: "Rule of thumb",
          text:
            "Fine-tuning pays off when you have a clear, repeatable task and at least a few hundred consistent examples. One-off questions are still better served by prompt engineering.",
        },
      },
    ],
  },
  {
    id: "ft-vs-prompt-vs-rag",
    category: "foundations",
    title: "Fine-tuning vs prompts vs RAG",
    summary: "Three ways to make a model useful — often combined, not competing.",
    sections: [
      {
        heading: "Prompt engineering",
        body:
          "Change the input text (system prompt, few-shot examples, chain-of-thought). Fast to iterate, zero training cost, but behaviour can drift and context windows fill up quickly.",
        bullets: ["Best for: prototyping, one-off tasks, rapid A/B of instructions"],
      },
      {
        heading: "RAG (retrieval-augmented generation)",
        body:
          "Fetch relevant documents at inference time and inject them into the prompt. Keeps answers grounded in your private knowledge without retraining weights.",
        bullets: ["Best for: Q&A over changing document stores, citations, fresh data"],
      },
      {
        heading: "Fine-tuning",
        body:
          "Change the model weights themselves. The behaviour becomes intrinsic — consistent tone, format, and task skill without stuffing examples into every prompt.",
        bullets: ["Best for: stable output style, domain jargon, tool-use formats, high-volume APIs"],
      },
      {
        callout: {
          variant: "info",
          text:
            "Production systems often stack all three: a fine-tuned model for style and skill, RAG for factual grounding, and prompts for session-specific instructions.",
        },
      },
    ],
  },
  {
    id: "training-pipeline",
    category: "foundations",
    title: "The studio pipeline",
    summary: "How modules connect from raw data to a deployed model.",
    relatedLinks: [
      { label: "Onboarding tour", href: "/onboarding" },
      { label: "Deploy & Export", href: "/deploy" },
    ],
    sections: [
      {
        body: "Each module in Fine-Tuning Studio maps to a stage in a typical ML workflow:",
        bullets: [
          "Datasets — upload, detect format (Alpaca / ShareGPT / ChatML), run quality checks",
          "Methodology — pick SFT, LoRA, QLoRA, DPO, ORPO, or RLHF with guided recommendations",
          "Training Config — set hyperparameters with inline tooltips for every field",
          "GPU Selector & Cost Estimator — compare cloud GPUs and forecast spend before launch",
          "Training — launch a job and watch live loss, GPU utilisation, and ETA",
          "Evaluation — benchmark base vs fine-tuned side by side",
          "Deploy — export GGUF, push to HuggingFace Hub, or prepare for vLLM",
        ],
      },
      {
        callout: {
          variant: "tip",
          text: "First time through? Start at Onboarding for a guided walkthrough, then upload a dataset and let the Methodology Selector recommend a starting point.",
        },
      },
    ],
  },
  {
    id: "dataset-formats",
    category: "datasets",
    title: "Dataset formats",
    summary: "Alpaca, ShareGPT, and ChatML — how rows are shaped before training.",
    relatedLinks: [{ label: "Dataset Studio", href: "/datasets/upload" }],
    sections: [
      {
        heading: "Alpaca",
        body: "Single-turn instruction data with optional context.",
        bullets: [
          'Keys: instruction, input (optional), output',
          "Good for: Q&A, classification-style tasks, short completions",
          "Example: instruction = 'Summarise this article', input = <article>, output = <summary>",
        ],
      },
      {
        heading: "ShareGPT",
        body: "Multi-turn chats in a conversations array.",
        bullets: [
          'Each turn: { "from": "human"|"gpt"|"system", "value": "..." }',
          "Good for: dialogue, customer support transcripts, multi-step reasoning",
        ],
      },
      {
        heading: "ChatML",
        body: "Role-based messages — the canonical shape TRL trainers consume internally.",
        bullets: [
          'Each message: { "role": "user"|"assistant"|"system", "content": "..." }',
          "Good for: modern chat models; other formats are auto-converted here during training",
        ],
      },
      {
        callout: {
          variant: "info",
          text: "Upload any supported format — the Dataset Studio detects it automatically and normalises rows to ChatML before training.",
        },
      },
    ],
  },
  {
    id: "dataset-quality",
    category: "datasets",
    title: "Dataset quality",
    summary: "What the quality report checks and why it matters.",
    relatedLinks: [{ label: "Upload a dataset", href: "/datasets/upload" }],
    sections: [
      {
        heading: "What we measure",
        bullets: [
          "Duplicate rows — exact matches after normalising whitespace and case",
          "Word-count stats — min, max, mean, median length per example",
          "Language distribution — per-row language detection (use full sentences for accuracy)",
        ],
      },
      {
        heading: "Practical checklist",
        bullets: [
          "Remove near-duplicate instructions — they inflate metrics without teaching new behaviour",
          "Keep examples consistent in tone and format — the model copies what it sees",
          "Balance languages if you care about multilingual output",
          "Aim for at least 500 rows for LoRA/QLoRA, 1,000+ for SFT, 1,000+ pairs for DPO/ORPO",
        ],
      },
      {
        callout: {
          variant: "warning",
          text: "Garbage in, garbage out — a small, clean dataset almost always beats a large, noisy one.",
        },
      },
    ],
  },
  {
    id: "preference-pairs",
    category: "datasets",
    title: "Preference pairs",
    summary: "The data shape required for DPO, ORPO, and RLHF alignment.",
    relatedLinks: [{ label: "Methodology Selector", href: "/methodology" }],
    sections: [
      {
        body:
          "Alignment methods need triplets: a prompt plus a preferred (chosen) completion and a dispreferred (rejected) one.",
        bullets: [
          'Each row: { "prompt": "...", "chosen": "...", "rejected": "..." }',
          "Chosen should reflect the behaviour you want; rejected should be plausible but clearly worse",
          "Pairs must share the same prompt — you are teaching ranking, not new facts",
        ],
      },
      {
        heading: "Collecting good pairs",
        bullets: [
          "Use real user thumbs-up/down logs when possible",
          "Have annotators agree on a rubric (helpful, harmless, honest)",
          "Avoid pairs where chosen and rejected are nearly identical — the signal is too weak",
        ],
      },
      {
        callout: {
          variant: "tip",
          text: "Start with ORPO if you have pairs but limited VRAM — it combines SFT and preference tuning in one pass.",
        },
      },
    ],
  },
  ...methodologyTopics(),
  {
    id: "lora-mechanics",
    category: "concepts",
    title: "How LoRA works",
    summary: "Low-rank adapters inject trainable matrices into frozen layers.",
    relatedLinks: [{ label: "Config Builder", href: "/config?methodology=lora" }],
    sections: [
      {
        body:
          "Instead of updating every weight in a billion-parameter model, LoRA adds small matrices A and B to selected linear layers. The base weights stay frozen; only A and B train.",
      },
      {
        heading: "Rank (r)",
        body:
          "The inner dimension of A and B. Higher rank = more capacity to learn complex adaptations, but more parameters, more VRAM, and higher overfitting risk on small data. Typical starting point: 8.",
      },
      {
        heading: "Alpha",
        body:
          "Scales the adapter output before it is added to the frozen layer. Often set to 2× rank (e.g. r=8, alpha=16). Too high destabilises training; too low makes the adapter ineffective.",
      },
      {
        callout: {
          variant: "info",
          text: "QLoRA uses the same adapter idea but loads the base model in 4-bit NF4 quantization — that's why it fits on consumer GPUs.",
        },
      },
    ],
  },
  {
    id: "vram-budgeting",
    category: "concepts",
    title: "VRAM & GPU budgeting",
    summary: "What drives memory use and how to pick a GPU.",
    relatedLinks: [
      { label: "GPU Selector", href: "/gpu-selector" },
      { label: "Cost Estimator", href: "/cost-estimator" },
    ],
    sections: [
      {
        heading: "Main VRAM drivers",
        bullets: [
          "Model size — parameter count and precision (fp16 vs 4-bit)",
          "Methodology — SFT loads full weights; QLoRA loads a quantised base + small adapters",
          "Sequence length — doubling max_seq_length roughly doubles activation memory",
          "Batch size — lower batch size first; use gradient accumulation to recover effective batch",
        ],
      },
      {
        heading: "Rough guide for 7B models",
        bullets: [
          "QLoRA: ~10–16 GB (single RTX 3090 / cloud T4)",
          "LoRA: ~20–28 GB (A10, A5000)",
          "Full SFT: 40–80 GB (A100 40/80 GB)",
          "DPO: ~2× LoRA (policy + frozen reference)",
        ],
      },
      {
        callout: {
          variant: "tip",
          text: "Use the GPU Selector to compare vendors and the Cost Estimator to forecast spend before you launch.",
        },
      },
    ],
  },
  {
    id: "loss-and-overfitting",
    category: "concepts",
    title: "Loss curves & overfitting",
    summary: "Reading training metrics on the live dashboard.",
    relatedLinks: [{ label: "Training dashboard", href: "/training" }],
    sections: [
      {
        heading: "Train loss",
        body:
          "Measures how wrong the model is on training examples. It should trend down steadily. Sudden spikes often mean the learning rate is too high or the batch is unstable.",
      },
      {
        heading: "Eval loss",
        body:
          "Measured on held-out data. If train loss keeps falling but eval loss rises, the model is memorising your dataset (overfitting) — try fewer epochs, more data, or lower rank.",
      },
      {
        heading: "Healthy signs",
        bullets: [
          "Train and eval loss both decrease, then eval loss plateaus",
          "GPU utilisation stays high without OOM errors",
          "Generated samples in Evaluation match your desired style",
        ],
      },
      {
        callout: {
          variant: "warning",
          text: "More epochs is not always better — three well-chosen epochs on clean data usually beats ten on noisy data.",
        },
      },
    ],
  },
  {
    id: "alignment-overview",
    category: "concepts",
    title: "Alignment overview",
    summary: "Teaching models what humans prefer, not just what text predicts.",
    relatedLinks: [{ label: "DPO explainer", href: "/learning?topic=dpo" }],
    sections: [
      {
        body:
          "Standard SFT teaches next-token prediction on demonstrations. Alignment methods teach the model to prefer helpful, safe completions over plausible but bad ones.",
      },
      {
        heading: "Method comparison",
        bullets: [
          "DPO — direct preference optimisation; no reward model, but needs a reference copy in memory",
          "ORPO — odds-ratio preference optimisation; single-pass SFT + alignment on LoRA-sized VRAM",
          "RLHF — train a reward model, then optimise with PPO; highest quality ceiling, highest complexity",
        ],
      },
      {
        callout: {
          variant: "info",
          text: "Alignment does not replace task-specific SFT — most production flows SFT first for skill, then align for tone and safety.",
        },
      },
    ],
  },
]

export function getTopicById(id: string): LearningTopic | undefined {
  return LEARNING_TOPICS.find((topic) => topic.id === id)
}

export function getTopicsByCategory(category: LearningCategory): LearningTopic[] {
  return LEARNING_TOPICS.filter((topic) => topic.category === category)
}

export const DEFAULT_LEARNING_TOPIC_ID = LEARNING_TOPICS[0]?.id ?? "what-is-fine-tuning"
