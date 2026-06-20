"use client"

import { Info } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverHeader,
  PopoverTitle,
  PopoverTrigger,
} from "@/components/ui/popover"

export type ParameterInfo = {
  label: string
  description: string
  typicalDefault: string
  whyItMatters: string
}

export const PARAMETER_INFO: Record<string, ParameterInfo> = {
  learning_rate: {
    label: "Learning rate",
    description: "How large a step the optimizer takes when updating weights after each batch.",
    typicalDefault: "2e-4 (LoRA/QLoRA), 2e-5 (full SFT)",
    whyItMatters:
      "Too high causes loss to diverge or spike; too low wastes compute and may underfit within the epoch budget.",
  },
  num_epochs: {
    label: "Number of epochs",
    description: "How many full passes the trainer makes over the dataset.",
    typicalDefault: "3",
    whyItMatters:
      "Too few epochs underfits; too many overfits a small dataset and increases cost with no quality gain.",
  },
  batch_size: {
    label: "Batch size",
    description: "Number of examples processed together in one forward/backward pass.",
    typicalDefault: "4 (per-device, with gradient accumulation to reach an effective batch of 16-32)",
    whyItMatters:
      "Larger batches give more stable gradients but use more VRAM; on a fixed GPU, batch size is usually the first thing you have to shrink.",
  },
  warmup_ratio: {
    label: "Warmup ratio",
    description:
      "Fraction of total training steps spent ramping the learning rate up from 0 to its target value.",
    typicalDefault: "0.03 (3% of steps)",
    whyItMatters:
      "Skipping warmup can cause unstable, high-variance loss in the first steps, especially at higher learning rates.",
  },
  weight_decay: {
    label: "Weight decay",
    description: "L2 regularization strength applied to weights during optimization.",
    typicalDefault: "0",
    whyItMatters:
      "Helps prevent overfitting on small datasets, but too much can slow or block convergence — most LoRA/QLoRA runs leave it at 0.",
  },
  max_seq_length: {
    label: "Max sequence length",
    description: "The maximum number of tokens per training example; longer examples are truncated.",
    typicalDefault: "2048",
    whyItMatters:
      "Directly drives VRAM usage — doubling sequence length roughly doubles activation memory, so it's a primary lever for fitting on smaller GPUs.",
  },
  gradient_accumulation_steps: {
    label: "Gradient accumulation steps",
    description:
      "Number of forward/backward passes accumulated before an optimizer step, simulating a larger batch size.",
    typicalDefault: "1 (raise if batch size must be lowered to fit VRAM)",
    whyItMatters:
      "Lets you reach a larger effective batch size on limited VRAM at the cost of more wall-clock time per optimizer step.",
  },
  lora_r: {
    label: "LoRA rank (r)",
    description: "The rank of the low-rank adapter matrices injected into each target layer.",
    typicalDefault: "8",
    whyItMatters:
      "Higher rank gives the adapter more capacity to learn task-specific behavior, but increases trainable parameters, VRAM, and overfitting risk on small datasets.",
  },
  lora_alpha: {
    label: "LoRA alpha",
    description: "A scaling factor applied to the LoRA update before it's added to the frozen base weights.",
    typicalDefault: "16 (commonly 2x the rank)",
    whyItMatters:
      "Controls how strongly the adapter's output influences the model — too high can destabilize training, too low makes the adapter barely change behavior.",
  },
  beta: {
    label: "Beta",
    description:
      "Controls how strongly the policy is constrained to stay close to the reference model during preference optimization.",
    typicalDefault: "0.1",
    whyItMatters:
      "Lower beta allows bigger departures from the reference model (more aggressive alignment, higher risk of degeneration); higher beta keeps outputs closer to the original model.",
  },
  reward_model_id: {
    label: "Reward model ID",
    description: "The model used to score generated responses during PPO-based reinforcement learning.",
    typicalDefault: "No default — must be a model already trained to score this task",
    whyItMatters:
      "RLHF quality is bounded by the reward model's accuracy; a poorly calibrated reward model will actively teach the policy the wrong behavior.",
  },
}

export function ParameterTooltip({ label, description, typicalDefault, whyItMatters }: ParameterInfo) {
  return (
    <Popover>
      <PopoverTrigger
        render={
          <Button
            type="button"
            variant="ghost"
            size="icon-xs"
            aria-label={`What is ${label}?`}
          />
        }
      >
        <Info className="size-3.5 text-muted-foreground" />
      </PopoverTrigger>
      <PopoverContent>
        <PopoverHeader>
          <PopoverTitle>{label}</PopoverTitle>
        </PopoverHeader>
        <p>{description}</p>
        <p>
          <span className="font-medium text-foreground">Typical default:</span> {typicalDefault}
        </p>
        <p>
          <span className="font-medium text-foreground">Why it matters:</span> {whyItMatters}
        </p>
      </PopoverContent>
    </Popover>
  )
}
