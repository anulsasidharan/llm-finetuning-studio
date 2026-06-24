import type { Methodology } from "@/types"

export type RecommendationGoal = "plain_task" | "alignment"
export type VramBudget = "low" | "medium" | "high"

export type RecommendationInput = {
  goal: RecommendationGoal
  vramBudget: VramBudget
  /** Approximate row (or preference-pair) count; 0 means "not provided yet". */
  datasetRows: number
}

export type RecommendationResult = {
  methodology: Methodology
  /** True when datasetRows was provided and falls below the recommended methodology's min sample count. */
  belowMinSamples: boolean
}

// Mirrors CLAUDE.md section 7's "Min Samples" column, as plain numbers for comparison
// (lib/methodology-data.ts keeps the display strings — this is a separate derived concern).
const MIN_SAMPLES: Record<Methodology, number> = {
  sft: 1000,
  lora: 500,
  qlora: 500,
  dpo: 1000,
  orpo: 1000,
  rlhf: 10000,
}

export function recommendMethodology({
  goal,
  vramBudget,
  datasetRows,
}: RecommendationInput): RecommendationResult {
  let methodology: Methodology

  if (goal === "alignment") {
    if (vramBudget === "high" && datasetRows >= MIN_SAMPLES.rlhf) {
      methodology = "rlhf"
    } else if (vramBudget === "low") {
      methodology = "orpo"
    } else {
      methodology = "dpo"
    }
  } else {
    if (vramBudget === "high") {
      methodology = "sft"
    } else if (vramBudget === "medium") {
      methodology = "lora"
    } else {
      methodology = "qlora"
    }
  }

  return {
    methodology,
    belowMinSamples: datasetRows > 0 && datasetRows < MIN_SAMPLES[methodology],
  }
}
