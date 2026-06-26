import { Suspense } from "react"

import { LearningCenterView } from "./LearningCenterView"

export default function LearningPage() {
  return (
    <Suspense fallback={null}>
      <LearningCenterView />
    </Suspense>
  )
}
