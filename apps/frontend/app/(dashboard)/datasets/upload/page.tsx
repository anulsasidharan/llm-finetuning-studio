import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { PageContainer } from "@/components/layout/PageContainer"
import { DatasetUploader } from "@/components/dataset/DatasetUploader"

export default function UploadDatasetPage() {
  return (
    <PageContainer>
      <h1 className="text-2xl font-semibold text-foreground">Upload dataset</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Upload a .json or .jsonl file containing your training data.
      </p>
      <Card className="mt-6 max-w-xl">
        <CardHeader>
          <CardTitle>Dataset file</CardTitle>
          <CardDescription>
            You can detect its format and run a quality check after uploading.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DatasetUploader />
        </CardContent>
      </Card>
    </PageContainer>
  )
}
