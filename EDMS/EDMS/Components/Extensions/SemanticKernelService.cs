using EDMS.Components.Plugins;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Ollama;

namespace EDMS.Components.Extensions
{
    public static class SemanticKernelService
    {
        public static async Task<IServiceCollection> AddSemanticKernelServices(this IServiceCollection services, IConfiguration configuration)
        {
            var endpoint = configuration["Ollama:OpenAIEndpoint"];
            if (string.IsNullOrWhiteSpace(endpoint) || !Uri.TryCreate(endpoint, UriKind.Absolute, out var uri))
            {
                throw new InvalidOperationException(
                    "Ollama:OpenAIEndpoint 설정이 필요합니다. 환경 변수 Ollama__OpenAIEndpoint를 사용하세요.");
            }

            // Kernel을 Singleton으로 등록 (중요!)
            services.AddSingleton<Kernel>(sp =>
            {
                var excelPlugin = new ExcelPlugin();

                // 매번 새로운 빌더 생성
                var kernelBuilder = Kernel.CreateBuilder();

                kernelBuilder.AddOpenAIChatCompletion(
                    modelId: "qwen3-coder:30b",
                    apiKey: "none",
                    endpoint: uri,
                    serviceId: "CoderChat",
                    httpClient: new HttpClient { Timeout = TimeSpan.FromMinutes(500) }
                );

                kernelBuilder.AddOpenAIChatCompletion(
                    modelId: "gpt-oss:20b",
                    apiKey: "none",
                    endpoint: uri,
                    serviceId: "GeneralChat",
                    httpClient: new HttpClient { Timeout = TimeSpan.FromMinutes(500) }
                );

                kernelBuilder.AddOpenAIChatCompletion(
                    modelId: "qwen3-vl:8b",
                    apiKey: "none",
                    endpoint: uri,
                    serviceId: "LowImageChat",
                    httpClient: new HttpClient { Timeout = TimeSpan.FromMinutes(500) }
                );

                //kernelBuilder.AddOllamaChatCompletion(
                //    modelId: "qwen3-vl:32b",
                //    endpoint: new Uri(uri),
                //    serviceId: "HighImageChat"
                //);

                kernelBuilder.AddOpenAIChatCompletion(
                    modelId: "qwen3-vl:32b-ocr2",
                    apiKey: "none",
                    endpoint: uri,
                    serviceId: "HighImageChat",
                    httpClient: new HttpClient { Timeout = TimeSpan.FromMinutes(500) }
                );

                kernelBuilder.AddOllamaTextEmbeddingGeneration(
                    modelId: "qwen3-embedding:0.6b",
                    endpoint: uri,
                    serviceId: "Embadding"
                );

                // 플러그인 추가
                kernelBuilder.Plugins.AddFromObject(excelPlugin, "ExcelTools");

                // Build는 단 한 번만 호출
                return kernelBuilder.Build();
            });

            return services;
        }
    }
}
