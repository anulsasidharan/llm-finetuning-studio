import type { Methodology } from "@/types"

export type MethodologyInfo = {
  methodology: Methodology
  label: string
  trainerClass: string
  vramUsage: string
  minSamples: string
  keyDifferentiator: string
}

// CLAUDE.md section 7 — Fine-Tuning Methodology Reference table.
export const METHODOLOGY_INFO: MethodologyInfo[] = [
  {
    methodology: "sft",
    label: "SFT",
    trainerClass: "trl.SFTTrainer",
    vramUsage: "Full model",
    minSamples: "1,000",
    keyDifferentiator: "Simplest; updates all weights",
  },
  {
    methodology: "lora",
    label: "LoRA",
    trainerClass: "peft.LoraConfig",
    vramUsage: "~40% of full",
    minSamples: "500",
    keyDifferentiator: "Low-rank adapters; frozen base",
  },
  {
    methodology: "qlora",
    label: "QLoRA",
    trainerClass: "LoRA + BitsAndBytesConfig",
    vramUsage: "~15% of full",
    minSamples: "500",
    keyDifferentiator: "4-bit NF4 base; most practical",
  },
  {
    methodology: "dpo",
    label: "DPO",
    trainerClass: "trl.DPOTrainer",
    vramUsage: "2x LoRA",
    minSamples: "1,000 pairs",
    keyDifferentiator: "Alignment without reward model",
  },
  {
    methodology: "orpo",
    label: "ORPO",
    trainerClass: "trl.ORPOTrainer",
    vramUsage: "~LoRA",
    minSamples: "1,000 pairs",
    keyDifferentiator: "Single-pass SFT + alignment",
  },
  {
    methodology: "rlhf",
    label: "RLHF",
    trainerClass: "trl.PPOTrainer + RewardTrainer",
    vramUsage: "4x base",
    minSamples: "10,000 pairs",
    keyDifferentiator: "Gold standard alignment; complex",
  },
]
