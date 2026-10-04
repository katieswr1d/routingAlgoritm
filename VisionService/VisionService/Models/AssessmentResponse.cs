namespace VisionService.Models
{
    public class AssessmentResponse
    {
        public string Label { get; set; }
        public float Confidence { get; set; }
        public float Score { get; set; }
        public float[] AllScores { get; set; }
    }
}