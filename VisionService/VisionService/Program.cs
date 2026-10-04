using VisionService.Services;

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.UseUrls("http://0.0.0.0:5001");

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var modelPath = Path.Combine(builder.Environment.ContentRootPath, "ml_assets", "landscape_model.zip");

if (!File.Exists(modelPath))
    throw new FileNotFoundException($"Модель не найдена: {modelPath}");

builder.Services.AddSingleton<MLModelService>(sp => new MLModelService(modelPath));

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseAuthorization();
app.MapControllers();
app.Run();