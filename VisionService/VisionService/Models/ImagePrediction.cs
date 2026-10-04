namespace VisionService.Models
{
    public class ImagePrediction : ImageData
    {
        public float[] Score { get; set; }
        public string PredictedLabelValue { get; set; }
    }
}