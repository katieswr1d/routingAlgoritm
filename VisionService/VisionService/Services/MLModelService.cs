using Microsoft.ML;
using VisionService.Models;

namespace VisionService.Services
{
    public class MLModelService
    {
        private readonly MLContext _mlContext;
        private readonly ITransformer _model;
        private readonly PredictionEngine<ImageData, ImagePrediction> _predictionEngine;

        public MLModelService(string modelPath)
        {
            _mlContext = new MLContext(seed: 0);
            _model = _mlContext.Model.Load(modelPath, out var modelSchema);
            _predictionEngine = _mlContext.Model
                .CreatePredictionEngine<ImageData, ImagePrediction>(_model);
        }

        public AssessmentResponse Assess(string imagePath)
        {
            var imageData = new ImageData { ImagePath = imagePath, Label = "" };
            var prediction = _predictionEngine.Predict(imageData);

            float confidence = 0f;
            if (prediction.Score != null)
            {
                foreach (var s in prediction.Score)
                    if (s > confidence) confidence = s;
            }

            float numericScore = prediction.PredictedLabelValue?.ToLower() switch
            {
                "good" => 1.0f,
                "normal" => 0.5f,
                "bad" => 0.1f,
                _ => 0.5f
            };

            return new AssessmentResponse
            {
                Label = prediction.PredictedLabelValue,
                Confidence = confidence,
                Score = numericScore,
                AllScores = prediction.Score
            };
        }
    }
}