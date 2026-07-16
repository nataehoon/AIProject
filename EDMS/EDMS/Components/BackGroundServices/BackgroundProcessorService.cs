using EDMS.Components.Database;
using EDMS.Components.Hubs;
using EDMS.Components.Models.DTO;
using EDMS.Components.Models.Entity;
using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;
using Qdrant.Client;
using System.Collections.Concurrent;
using System.Net.Http.Headers;
using System.Text.Json;
using Telerik.Documents.Fixed.FormatProviders.Image.Skia;
using Telerik.Windows.Documents.Fixed.FormatProviders.Pdf;
using Telerik.Windows.Documents.Fixed.Model;

namespace EDMS.Components.BackGroundServices
{
    public class BackgroundProcessorService : IBackgroundProcessorService
    {
        private readonly IHttpClientFactory _httpClient;
        private readonly IDbContextFactory<MyDbContext> _context;
        private readonly IHubContext<FileProgressingHub> _hubContext;
        public static readonly ConcurrentDictionary<string, UploadStatusDTO> _progressData = new ConcurrentDictionary<string, UploadStatusDTO>();

        public BackgroundProcessorService(IHttpClientFactory httpClient, IDbContextFactory<MyDbContext> context, QdrantClient qdrant, IHubContext<FileProgressingHub> hubContext)
        {
            _httpClient = httpClient;
            _context = context;
            _hubContext = hubContext;
        }

        public async Task ProcessAsync(BackgroundTask task)
        {
            try
            {
                Console.WriteLine("ConvertVector 시작");
                await ConvertVector(task.data);
                Console.WriteLine("ConvertVector 끝");
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
            }
        }

        private async Task ConvertVector(Dictionary<string, object> data)
        {
            var file = (byte[])data["fileData"];
            var fileName = (string)data["fileName"];
            var contentType = (string)data["contentType"];
            var baseUrl = (string)data["baseUrl"];
            var filePath = (string)data["filePath"];
            var fileSize = Convert.ToInt32(data["fileSize"]);
            var IsHigh = (bool)data["isHigh"];
            var uploadPath = (string)data["uploadPath"];
            var fileId = (string)data["fileId"];

            if (file == null)
            {
                Console.WriteLine("파일이 없습니다.");
                return;
            }

            try
            {
                var fileData = new UploadFileDataDTO
                {
                    FileId = fileId,
                    FileName = fileName,
                    FilePath = filePath,
                    FileSize = fileSize,
                    IsHigh = IsHigh,
                    UploadPath = uploadPath,
                    Extension = $".{contentType}"
                };

                bool result = false;
                if (contentType == "pdf")
                {
                    Console.WriteLine("PDF 변환 시작");
                    fileData.FileType = "pdf";
                    fileData.Images = await ConvertPdfToImages(file, fileName, uploadPath, fileSize, fileId);

                    foreach(var item in fileData.Images)
                    {
                        Console.WriteLine($"==========================================");
                        Console.WriteLine($"[이미지 정보]");
                        Console.WriteLine($"원본 크기: {item.Length:N0} bytes");
                        Console.WriteLine($"KB: {item.Length / 1024.0:F2} KB");
                        Console.WriteLine($"MB: {item.Length / 1024.0 / 1024.0:F2} MB");
                        Console.WriteLine($"==========================================");
                    }

                    Console.WriteLine($"PDF 변환 완료: {fileData.Images.Count}개 페이지");
                    result = await AIOCR(fileData, baseUrl);
                }
                else if (contentType == "image")
                {
                    Console.WriteLine("이미지 파일");
                    fileData.FileType = "image";
                    fileData.Images.Add(file);
                    result = await AIOCR(fileData, baseUrl);
                }
                else if (contentType == "excel")
                {
                    Console.WriteLine("Excel 파일");
                    fileData.FileType = "excel";
                    fileData.Images.Add(file);
                }

                if (result)
                {
                    using var content = new MultipartFormDataContent();
                    using var streamContent = new ByteArrayContent(file);
                    streamContent.Headers.ContentType = new MediaTypeHeaderValue(
                        contentType == "pdf" ? "application/pdf" :
                        contentType == "image" ? "image/jpeg" :
                        contentType == "excel" ? "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" :
                        "application/octet-stream"
                    );
                    content.Add(streamContent, "file", fileName);

                    using var client = _httpClient.CreateClient();
                    using var response = await client.PostAsync($"{baseUrl}api/FileSave", content);

                    if (!response.IsSuccessStatusCode)
                    {
                        string error = "파일 저장에 실패하였습니다. 다시 시도해 주세요.";
                        Console.WriteLine(error);
                        UploadStatusDTO uploadStatus = new UploadStatusDTO
                        {
                            Content = error,
                            Path = uploadPath,
                            Size = fileSize,
                            Extension = $".{contentType}",
                            FileId = fileId
                        };
                        _progressData[fileData.FileName] = uploadStatus;
                        await _hubContext.Clients.Group("progressInfo").SendAsync("ProgressInfo", _progressData);
                    }
                    else
                    {
                        UploadStatusDTO uploadStatus = new UploadStatusDTO
                        {
                            Content = $"저장 완료",
                            Path = uploadPath,
                            Size = fileSize,
                            Extension = $".{contentType}",
                            FileId = fileId
                        };
                        _progressData[fileData.FileName] = uploadStatus;
                        await _hubContext.Clients.Group("progressInfo").SendAsync("ProgressInfo", _progressData);
                        _progressData.TryRemove(fileData.FileName, out _);
                    }
                }

                Console.WriteLine("종료");
            }
            catch (InvalidOperationException ex)
            {
                Console.WriteLine("파일 첨부는 한번에 10개 까지만 가능합니다.");
                Console.WriteLine(ex.Message);
            }
            catch (IOException ex)
            {
                Console.WriteLine("파일 크기는 100MB를 초과할 수 없습니다.");
                Console.WriteLine(ex.Message);
            }
            catch (Exception ex)
            {
                // 기타 예외 처리
                Console.WriteLine("파일 첨부 중 오류가 발생했습니다.");
                Console.WriteLine(ex.Message);
            }
        }

        private async Task<bool> AIOCR(UploadFileDataDTO fileData, string baseUrl)
        {
            try
            {
                var semaphore = new SemaphoreSlim(4, 4);

                string UID = Guid.NewGuid().ToString();
                DocFileInfo docfile = new DocFileInfo
                {
                    IDX = Guid.NewGuid().ToString(),
                    UID = UID,
                    FileName = fileData.FileName,
                    Title = fileData.FileName,
                    MainText = "test",
                    FileSize = fileData.FileSize,
                    FilePath = fileData.FilePath,
                    CreateAt = DateTime.Now,
                    UpdateAt = DateTime.Now
                };

                List<DocFilePage> docPageList = new();
                List<DocChunkDTO> docChunks = new();

                Console.WriteLine($"Images Count : {fileData.Images.Count()}");
                var tasks = fileData.Images.Select(async (image, index) =>
                {
                    await semaphore.WaitAsync();
                    try
                    {
                        using var client = _httpClient.CreateClient("AIClient");
                        client.BaseAddress = new Uri(baseUrl);

                        var fileBytes = new RequstDataDTO
                        {
                            Image = Convert.ToBase64String(image),
                            PageNum = (index+1).ToString(),
                            TotalPage = fileData.Images.Count.ToString(),
                            IsHigh = fileData.IsHigh
                        };

                        UploadStatusDTO uploadStatus = new UploadStatusDTO
                        {
                            Content = $"텍스트 읽는중...({index + 1}/{fileData.Images.Count})",
                            Path = fileData.UploadPath,
                            Size = fileData.FileSize,
                            Extension = fileData.Extension,
                            FileId = fileData.FileId
                        };
                        _progressData[fileData.FileName] = uploadStatus;
                        await _hubContext.Clients.Group("progressInfo").SendAsync("ProgressInfo", _progressData);

                        using var response = await client.PostAsJsonAsync("api/OCR", fileBytes);
                        Console.WriteLine($"[OCR API 호출 결과] 상태 코드: {response.StatusCode}");
                        
                        var result = await response.Content.ReadAsStringAsync();
                        if (!response.IsSuccessStatusCode && string.IsNullOrEmpty(result))
                        {
                            string error = string.IsNullOrEmpty(result) ? "내용 없음" : result;

                            uploadStatus = new UploadStatusDTO
                            {
                                Content = $"실패 하였습니다. 다시 시도해 주세요. [오류 내용]: {error}",
                                Path = fileData.UploadPath,
                                Size = fileData.FileSize,
                                Extension = fileData.Extension,
                                FileId = fileData.FileId
                            };
                            _progressData[fileData.FileName] = uploadStatus;
                            await _hubContext.Clients.Group("progressInfo").SendAsync("ProgressInfo", _progressData);

                            Console.WriteLine($"[오류 내용]: {error}");
                            return null;
                        }
                        else
                        {
                            if (string.IsNullOrEmpty(result))
                            {
                                Console.WriteLine($"내용이 없습니다.");
                                return null;
                            }

                            Console.WriteLine($"[결과 내용]: {result}");
                            string pageUID = Guid.NewGuid().ToString();
                            DocFilePage docfilepage = new DocFilePage
                            {
                                IDX = Guid.NewGuid().ToString(),
                                UID = pageUID,
                                PageNum = index+1,
                                Content = result,
                                Link_Doc = UID,
                                CreateAt = DateTime.Now,
                                UpdateAt = DateTime.Now
                            };

                            docPageList.Add(docfilepage);

                            var pageChunks = SplitIntoChunks(result, maxChunkSize: 800, overlap: 100);

                            for(int i = 0; i < pageChunks.Count; i++)
                            {
                                var chunk = new DocChunkDTO
                                {
                                    UID = pageUID,
                                    PageNum = index + 1,
                                    Title = fileData.FileName,
                                    ChunkIndex = i,
                                    ChunkText = pageChunks[i]
                                };

                                docChunks.Add(chunk);
                            }
                            return result;
                        }
                    }
                    catch(Exception ex)
                    {
                        UploadStatusDTO uploadStatus = new UploadStatusDTO
                        {
                            Content = $"실패 하였습니다. 다시 시도해 주세요. [오류 내용]: {ex.Message}",
                            Path = fileData.UploadPath,
                            Size = fileData.FileSize,
                            Extension = fileData.Extension,
                            FileId = fileData.FileId
                        };
                        _progressData[fileData.FileName] = uploadStatus;
                        await _hubContext.Clients.Group("progressInfo").SendAsync("ProgressInfo", _progressData);

                        Console.WriteLine($"[오류 내용]: {ex.Message}");
                        return null;
                    }
                    finally
                    {
                        semaphore.Release();
                    }
                });

                var results = await Task.WhenAll(tasks);

                if (!tasks.Any())
                {
                    return false;
                }
                else
                {
                    using var client = _httpClient.CreateClient("AIClient");
                    client.BaseAddress = new Uri(baseUrl);

                    var tagResponse = await client.PostAsync("api/GetTagList", null);

                    IEnumerable<string> tagList = Enumerable.Empty<string>();
                    if (tagResponse.IsSuccessStatusCode)
                    {
                        tagList = await tagResponse.Content.ReadFromJsonAsync<IEnumerable<string>>() ?? Enumerable.Empty<string>();
                    }

                    Console.WriteLine($"results : {JsonSerializer.Serialize(results)}");

                    string text = string.Join(" ", results);

                    SummaryRequestDTO requestData = new SummaryRequestDTO
                    {
                        Message = text,
                        TagList = tagList
                    };

                    var summaryResponse = await client.PostAsJsonAsync("api/Summary", requestData);

                    if (summaryResponse.IsSuccessStatusCode)
                    {
                        string summaryResult = await summaryResponse.Content.ReadAsStringAsync();

                        Console.WriteLine($"summaryResult : {summaryResult}");

                        var resultObject = JsonSerializer.Deserialize<SummaryResponseDTO>(summaryResult, new JsonSerializerOptions
                        {
                            PropertyNameCaseInsensitive = true
                        });

                        docfile.MainText = resultObject.Content;
                        docfile.Tags = string.Join(", ", resultObject.Tags);

                        Console.WriteLine(summaryResult);
                    }

                }

                if (docChunks.Any())
                {
                    using var context = _context.CreateDbContext();

                    context.DocFileInfo.Add(docfile);
                    context.DocFilePage.AddRange(docPageList);
                    await context.SaveChangesAsync();

                    Console.WriteLine("RDB 저장 성공 벡터화 후 Qdrant");

                    using var client = _httpClient.CreateClient("AIClient");
                    client.BaseAddress = new Uri(baseUrl);

                    using var response = await client.PostAsJsonAsync("api/Embedding", docChunks);
                    Console.WriteLine($"[API 호출 결과] 상태 코드: {response.StatusCode}");

                    if (!response.IsSuccessStatusCode)
                    {
                        var result = await response.Content.ReadAsStringAsync();
                        Console.WriteLine($"[오류 내용]: {result}");
                    }

                    UploadStatusDTO uploadStatus = new UploadStatusDTO
                    {
                        Content = $"변환 완료",
                        Path = fileData.UploadPath,
                        Size = fileData.FileSize,
                        Extension = fileData.Extension,
                        FileId = fileData.FileId
                    };
                    _progressData[fileData.FileName] = uploadStatus;
                    await _hubContext.Clients.Group("progressInfo").SendAsync("ProgressInfo", _progressData);

                    return true;
                }
                return false;
            }
            catch(Exception ex)
            {
                Console.WriteLine($"error: {ex.Message}, {ex.StackTrace}");
                return false;
            }
        }

        private List<string> SplitIntoChunks(string text, int maxChunkSize = 800, int overlap = 100)
        {
            if (string.IsNullOrWhiteSpace(text))
                return new List<string>();

            var chunks = new List<string>();
            int position = 0;

            while (position < text.Length)
            {
                // 청크 크기 결정
                int remainingLength = text.Length - position;
                int chunkLength = Math.Min(maxChunkSize, remainingLength);

                // 문장 경계에서 자르기
                if (chunkLength == maxChunkSize && position + chunkLength < text.Length)
                {
                    int lastBreak = text.LastIndexOfAny(new[] { '.', '\n', '!', '?' },
                        position + chunkLength,
                        Math.Min(chunkLength / 2, chunkLength));

                    if (lastBreak > position)
                    {
                        chunkLength = lastBreak - position + 1;
                    }
                }

                // 청크 추출
                string chunk = text.Substring(position, chunkLength).Trim();

                if (!string.IsNullOrWhiteSpace(chunk))
                {
                    chunks.Add(chunk);
                }

                // 다음 위치 (오버랩 적용)
                position += chunkLength - overlap;

                // 무한 루프 방지
                if (chunkLength <= overlap)
                {
                    position = text.Length;
                }
            }

            return chunks;
        }

        private async Task<List<byte[]>> ConvertPdfToImages(byte[] pdfBytes, string fileName, string uploadPath, int fileSize, string fileId)
        {
            var convertedImages = new List<byte[]>();

            try
            {
                var pdfProvider = new PdfFormatProvider();
                RadFixedDocument document = pdfProvider.Import(pdfBytes);

                Console.WriteLine($"PDF 페이지 수: {document.Pages.Count}");

                // ImagePropertiesResolver 설정
                Telerik.Windows.Documents.Extensibility.FixedExtensibilityManager.ImagePropertiesResolver =
                    new Telerik.Documents.ImageUtils.ImagePropertiesResolver();

                // 각 페이지를 이미지로 변환
                for (int i =0; i < document.Pages.Count; i++)
                {
                    try
                    {
                        // SkiaImageFormatProvider의 정확한 전체 경로
                        var imageProvider = new Telerik.Documents.Fixed.FormatProviders.Image.Skia.SkiaImageFormatProvider();
                        SkiaImageExportSettings settings = new SkiaImageExportSettings
                        {
                            ScaleFactor = 2.0,
                            ImageFormat = SkiaImageFormat.Png,
                            Quality = 80
                        };
                        imageProvider.ExportSettings = settings;

                        using (var stream = new MemoryStream())
                        {
                            imageProvider.Export(document.Pages[i], stream);
                            convertedImages.Add(stream.ToArray());
                        }
                        Console.WriteLine($"이미지로 변환중...({i + 1}/{document.Pages.Count})");

                        UploadStatusDTO uploadStatus = new UploadStatusDTO
                        {
                            Content = $"이미지로 변환중...({i + 1}/{document.Pages.Count})",
                            Path = uploadPath,
                            Size = fileSize,
                            Extension = ".pdf",
                            FileId = fileId
                        };
                        _progressData[fileName] = uploadStatus;
                        await _hubContext.Clients.Group("progressInfo").SendAsync("ProgressInfo", _progressData);
                    }
                    catch (Exception pageEx)
                    {
                        Console.WriteLine($"페이지 변환 오류: {pageEx.Message}");
                    }
                }

                Console.WriteLine($"PDF 변환 완료: {convertedImages.Count}개 이미지");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"PDF 변환 오류: {ex.Message}");
                throw;
            }

            return convertedImages;
        }
    }
}
