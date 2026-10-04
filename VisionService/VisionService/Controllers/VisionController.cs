using Microsoft.AspNetCore.Mvc;
using VisionService.Models;
using VisionService.Services;

namespace VisionService.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class VisionController : ControllerBase
    {
        private readonly MLModelService _modelService;
        private readonly IWebHostEnvironment _env;
        private readonly ILogger<VisionController> _logger;

        public VisionController(
            MLModelService modelService,
            IWebHostEnvironment env,
            ILogger<VisionController> logger)
        {
            _modelService = modelService;
            _env = env;
            _logger = logger;
        }

        [HttpGet("health")]
        public IActionResult Health()
        {
            return Ok(new { status = "ok", service = "vision" });
        }

        [HttpPost("assess")]
        public async Task<IActionResult> Assess([FromForm] IFormFile file)
        {
            if (file == null || file.Length == 0)
                return BadRequest(new { error = "Файл не загружен" });

            try
            {
                var tempFolder = Path.Combine(_env.ContentRootPath, "temp");
                Directory.CreateDirectory(tempFolder);

                var fileName = $"{Guid.NewGuid()}{Path.GetExtension(file.FileName)}";
                var filePath = Path.Combine(tempFolder, fileName);

                using (var stream = new FileStream(filePath, FileMode.Create))
                {
                    await file.CopyToAsync(stream);
                }

                var result = _modelService.Assess(filePath);
                System.IO.File.Delete(filePath);

                _logger.LogInformation($"Оценка: {result.Label} ({result.Confidence:F2})");
                return Ok(result);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Ошибка: {ex.Message}");
                return StatusCode(500, new { error = ex.Message });
            }
        }
    }
}