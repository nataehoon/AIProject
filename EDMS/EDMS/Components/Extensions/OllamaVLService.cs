namespace EDMS.Components.Extensions
{
    // OllamaVLService.cs
    using System.Text.Json;
    using System.Text.Json.Serialization;

    public class OllamaVLService
    {
        private readonly HttpClient _httpClient;
        private readonly Uri _nativeEndpoint;

        public OllamaVLService(IHttpClientFactory httpClientFactory, IConfiguration configuration)
        {
            _httpClient = httpClientFactory.CreateClient("AIClient");

            var endpoint = configuration["Ollama:NativeEndpoint"];
            if (string.IsNullOrWhiteSpace(endpoint) || !Uri.TryCreate(endpoint, UriKind.Absolute, out var nativeEndpoint))
            {
                throw new InvalidOperationException(
                    "Ollama:NativeEndpoint 설정이 필요합니다. 환경 변수 Ollama__NativeEndpoint를 사용하세요.");
            }

            _nativeEndpoint = nativeEndpoint;
        }

        public async Task<string> OCRAsync(byte[] imageBytes, bool isHigh)
        {
            // Ollama 전용 API 형식 (OpenAI 규격보다 훨씬 단순하고 확실함)
            var requestBody = new
            {
                model = isHigh ? "qwen3-vl:32b-ocr" : "qwen3-vl:8b",
                prompt = "이미지의 모든 텍스트를 마크다운 표 형식으로 추출해줘.",
                stream = false,
                images = new[] { Convert.ToBase64String(imageBytes) }, // 이미지 배열
                options = new { num_ctx = 32768, temperature = 0.2, num_predict = 16384 }
            };

            var requestUri = new Uri(_nativeEndpoint, "api/generate");
            var response = await _httpClient.PostAsJsonAsync(requestUri, requestBody);
            var json = await response.Content.ReadFromJsonAsync<JsonElement>();

            // Ollama의 generate API는 'response' 필드에 결과가 담깁니다.
            return json.GetProperty("response").GetString();
        }
    }

    // 요청/응답 모델
    public class OllamaChatRequest
    {
        [JsonPropertyName("model")] public string Model { get; set; }
        [JsonPropertyName("messages")] public OllamaChatMessage[] Messages { get; set; }
        [JsonPropertyName("options")] public OllamaOptions Options { get; set; }
        [JsonPropertyName("keep_alive")] public string KeepAlive { get; set; }
        [JsonPropertyName("stream")] public bool Stream { get; set; }
    }

    public class OllamaChatMessage
    {
        [JsonPropertyName("role")] public string Role { get; set; }
        [JsonPropertyName("content")] public string Content { get; set; }
        [JsonPropertyName("images")] public string[] Images { get; set; }
    }

    public class OllamaOptions
    {
        [JsonPropertyName("num_ctx")] public int NumCtx { get; set; }
        [JsonPropertyName("num_predict")] public int NumPredict { get; set; }
        [JsonPropertyName("temperature")] public double Temperature { get; set; }
    }

    public class OllamaChatResponse
    {
        [JsonPropertyName("message")] public OllamaChatMessage Message { get; set; }
    }
}
