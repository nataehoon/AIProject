using DocumentFormat.OpenXml.InkML;
using EDMS.Components.BackGroundServices;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Telerik.SvgIcons;

namespace EDMS.Components.Controller
{
    [Route("api/[action]")]
    [ApiController]
    public class FileUploadController : ControllerBase
    {
        private readonly IWebHostEnvironment _env;
        private readonly BackgroundQueue _queue;

        public FileUploadController(IWebHostEnvironment env, BackgroundQueue queue)
        {
            _env = env;
            _queue = queue;
        }

        [HttpPost]
        [DisableRequestSizeLimit] // 용량 제한 해제
        [RequestFormLimits(MultipartBodyLengthLimit = 300 * 1024 * 1024)]
        public async Task<IActionResult> FileUpload( List<IFormFile> files, [FromForm] string isHigh, [FromForm] string uploadPath, [FromForm] string fileId)
        {
            try
            {
                if (files == null || files.Count == 0)
                {
                    return BadRequest("업로드된 파일이 없습니다.");
                }

                if (!Directory.Exists(uploadPath)) Directory.CreateDirectory(uploadPath);

                foreach (var file in files)
                {
                    var fileName = Path.GetFileName(file.FileName);
                    var filePath = Path.Combine(uploadPath, fileName);

                    //using (var stream = new FileStream(filePath, FileMode.Create))
                    //{
                    //    await file.CopyToAsync(stream);
                    //}

                    byte[] fileBytes;
                    using (var ms = new MemoryStream())
                    {
                        await file.OpenReadStream().CopyToAsync(ms);
                        fileBytes = ms.ToArray();
                    }

                    string contentType = string.Empty;
                    if (file.FileName.EndsWith(".pdf", StringComparison.OrdinalIgnoreCase))
                    {
                        contentType = "pdf";
                    }
                    else if (IsImageFile(file.FileName))
                    {
                        contentType = "image";
                    }
                    else if (file.FileName.EndsWith(".xlsx", StringComparison.OrdinalIgnoreCase))
                    {
                        contentType = "excel";
                    }

                    var request = HttpContext.Request;
                    string baseUrl = $"{request.Scheme}://{request.Host}/";

                    bool isHighValue = bool.TryParse(isHigh, out var result) && result;

                    var FileProc = new BackgroundTask
                    {
                        TaskId = file.FileName,
                        Type = file.ContentType,
                        data = new Dictionary<string, object>
                        {
                            {"fileData", fileBytes},
                            {"fileName", file.FileName},
                            {"contentType",  contentType},
                            { "baseUrl", baseUrl},
                            {"filePath", filePath },
                            { "fileSize" , file.Length},
                            { "isHigh", isHighValue},
                            { "uploadPath", uploadPath},
                            { "fileId", fileId}
                        }
                    };

                    _queue.Enqueue(FileProc);
                }

                return Ok(new { count = files.Count, message = "파일 변환 완료" });
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                return StatusCode(500);
            }
        }

        [HttpPost]
        [DisableRequestSizeLimit] // 용량 제한 해제
        [RequestFormLimits(MultipartBodyLengthLimit = 300 * 1024 * 1024)]
        public async Task<IActionResult> FileSave(IFormFile file)
        {
            try
            {
                if (file == null)
                {
                    return BadRequest("업로드된 파일이 없습니다.");
                }

                string uploadPath = Path.Combine(_env.WebRootPath, "uploads");
                if (!Directory.Exists(uploadPath)) Directory.CreateDirectory(uploadPath);

                var fileName = Path.GetFileName(file.FileName);
                var filePath = Path.Combine(uploadPath, fileName);

                using (var stream = new FileStream(filePath, FileMode.Create))
                {
                    await file.CopyToAsync(stream);
                }

                Console.WriteLine("파일 저장 완료");

                return Ok(new { message = "파일 저장 완료" });
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                return StatusCode(500);
            }
        }

        private bool IsImageFile(string fileName)
        {
            var extension = Path.GetExtension(fileName).ToLower();
            return extension == ".png" || extension == ".jpg" || extension == ".jpeg";
        }

    }
}
