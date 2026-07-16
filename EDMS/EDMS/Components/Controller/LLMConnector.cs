using EDMS.Components.Extensions;
using EDMS.Components.Models.DTO;
using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Qdrant.Client;
using Qdrant.Client.Grpc;
using System.Text;

namespace EDMS.Components.Controller
{
    [Route("api/[action]")]
    [ApiController]
    public class LLMConnector : ControllerBase
    {
        private static readonly Dictionary<string, ChatHistory> _historyBucket = new();
        private readonly Kernel _kernel;
        private readonly QdrantClient _qdrant;
        private readonly OllamaVLService _ollamaVL;

        public LLMConnector(Kernel kernel, QdrantClient qdrant, OllamaVLService ollamaVL)
        {
            _kernel = kernel;
            _qdrant = qdrant;
            _ollamaVL = ollamaVL;
        }

        [HttpPost]
        public async Task Chat([FromBody] ChatDTO request)
        {
            if (string.IsNullOrEmpty(request.Content))
                return;

            Response.ContentType = "text/plain; charset=utf-8";

            var chatService = _kernel.GetRequiredService<IChatCompletionService>("GeneralChat");
            var embeddingService = _kernel.GetRequiredService<ITextEmbeddingGenerationService>("Embadding");

            try
            {
                Console.WriteLine($"[질문] {request.Content}");

                // 1. 사용자 질문을 벡터로 변환
                var questionEmbedding = await embeddingService.GenerateEmbeddingAsync(request.Content);
                Console.WriteLine($"질문 벡터화 완료: {questionEmbedding.Length} 차원");

                // 2. 전체 책에서 유사한 문서 검색
                var searchResponse = await _qdrant.SearchAsync(
                    collectionName: "DocFileInfo",
                    vector: questionEmbedding.ToArray(),
                    limit: (ulong)10,
                    scoreThreshold: 0.5f,
                    payloadSelector: true
                    );

                Console.WriteLine($"Qdrant 검색 결과: {searchResponse.Count}개");

                var result = new List<SearchResultDTO>();

                foreach(var item in searchResponse)
                {
                    result.Add(new SearchResultDTO
                    {
                        EBookNM = item.Payload.Keys.Contains("Title") ? item.Payload["Title"].StringValue : "알수없는 문서",
                        PageNum = (int)item.Payload["PageNum"].IntegerValue,
                        Text = item.Payload["ChunkText"].StringValue,
                        ChunkIndex = (int)item.Payload["ChunkIndex"].IntegerValue,
                        Score = item.Score.ToString()
                    });

                    Console.WriteLine($"  - 점수: {item.Score}, 페이지: {(int)item.Payload["PageNum"].IntegerValue}");
                }

                if (!result.Any())
                {
                    string notFound = "질문과 관련된 문서를 찾을 수 없습니다. 다른 키워드로 검색해보세요.";
                    await Response.WriteAsync(notFound);
                    return;
                }

                Console.WriteLine($"검색된 문서: {result.Count}개");

                // 3. 검색된 문서들을 컨텍스트로 조합
                string context = string.Join("\n\n", result.Select((r, idx) =>
                    $"[문서 {idx + 1}]\n출처: {r.EBookNM} - 페이지 {r.PageNum}\n유사도: {r.Score:F2}\n내용: {r.Text}"));

                // 4. RAG 프롬프트 구성
                if (!_historyBucket.TryGetValue(request.RoomId, out var history))
                {
                    history = new ChatHistory();
                    history.AddSystemMessage(@"당신은 문서 검색 및 분석 전문가입니다.
                                        사용자가 검색한 내용과 관련된 문서들이 제공됩니다.

                                        [답변 규칙]
                                        1. 제공된 여러 문서를 종합적으로 분석하여 답변하세요.
                                        2. 답변에는 반드시 출처(파일명과 페이지 번호)를 명시하세요.
                                        3. 여러 문서에 걸쳐 있는 내용이라면 모두 언급하세요.
                                        4. 문서에서 직접적인 답을 찾을 수 없다면, 관련성이 있는 내용을 설명하고 '정확한 답변은 문서에 없습니다'라고 안내하세요.
                                        5. 유사도 점수가 낮은 문서는 참고만 하고, 높은 문서 위주로 답변하세요.

                                        [답변 형식]
                                        답변 내용을 먼저 작성하고, 마지막에 참고한 출처를 나열하세요.
                                        예시:
                                        (답변 내용)

                                        **참고 출처:**
                                        - 문서명.pdf 3페이지
                                        - 보고서.pdf 15페이지");
                    _historyBucket[request.RoomId] = history;
                }

                history.AddUserMessage($@"[검색된 관련 문서]
                                        {context}

                                        [사용자 질문]
                                        {request.Content}

                                        위 문서들을 분석하여 질문에 답변해주세요.");

                var executionSettings = new OpenAIPromptExecutionSettings
                {
                    Temperature = 0,
                    ExtensionData = new Dictionary<string, object>
                    {
                        { "strict", false },
                        { "keep_alive", "1m" },
                        { "num_ctx", 16384 }
                    }
                };

                var updates = chatService.GetStreamingChatMessageContentsAsync(history, executionSettings: executionSettings, kernel: _kernel);

                Console.WriteLine("시작 == " + DateTime.Now.ToString("HH:mm:ss"));
                StringBuilder fullContent = new StringBuilder();
                await foreach (var update in updates)
                {

                    if (!string.IsNullOrEmpty(update.Content))
                    {
                        fullContent.Append(update.Content);
                        await Response.WriteAsync(update.Content);
                        await Response.Body.FlushAsync();
                    }
                }
                Console.WriteLine("종료 == " + DateTime.Now.ToString("HH:mm:ss"));
                history.AddAssistantMessage(fullContent.ToString());
            }
            catch (System.ClientModel.ClientResultException ex) when (ex.Message.Contains("500"))
            {
                // 서버(Ollama)가 죽었을 때 사용자에게 알림
                string errorMsg = "로컬 LLM 서버 응답 오류입니다. GPU 메모리가 부족하거나 서버가 재시작 중일 수 있습니다.";
                await Response.WriteAsync(errorMsg);
                Console.WriteLine($"[LLM Error] {ex.Message}");
                return;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Chat Error] {ex.Message}");
                Console.WriteLine($"Stack Trace: {ex.StackTrace}");
                return;
            }

            await Response.CompleteAsync();
        }


        [HttpPost]
        public async Task OCR([FromBody] RequstDataDTO fileData)
        {
            if (fileData == null) return;

            var lowImageService = _kernel.GetRequiredService<IChatCompletionService>("LowImageChat");
            var highImageService = _kernel.GetRequiredService<IChatCompletionService>("HighImageChat");

            var selectedService = fileData.IsHigh ? highImageService : lowImageService;

            try
            {
                byte[] imageBytes = Convert.FromBase64String(fileData.Image);

                var contentItems = new ChatMessageContentItemCollection();
                contentItems.Add(new TextContent("이미지를 분석해 주세요."));

                var history = new ChatHistory();
                history.AddSystemMessage(@"당신은 세계 최고의 AI OCR 및 데이터 추출 전문가입니다. 
                                        제공된 이미지의 모든 내용을 단 한 글자의 누락도 없이 완벽하게 텍스트로 디지털화하는 것이 당신의 임무입니다.

                                        [준수 사항]
                                        1. 모든 텍스트 추출: 이미지에 포함된 아주 작은 글씨, 주석, 페이지 번호까지 한 글자도 빠짐없이 있는 그대로 추출하세요.
                                        2. 표(Table) 처리: 
                                            - 표 형식의 데이터는 반드시 '마크다운(Markdown) 표' 형식으로 변환하세요.
                                            - 셀 병합이 있는 경우, 데이터의 흐름에 맞게 반복 기입하거나 적절한 구분자(-)를 사용하여 구조를 유지하세요.
                                            - 기술적인 필드명 대신 사용자가 이해하기 쉬운 용어를 사용하되, 원본 데이터의 의미를 훼손하지 마세요.
                                        3. 레이아웃 유지: 
                                            - 일반 텍스트 문단과 표 사이에는 한 줄의 공백을 두어 구분하세요.
                                            - 문서의 시각적 순서(위에서 아래, 왼쪽에서 오른쪽)를 엄격히 따르세요.
                                        4. 금지 사항:
                                            - ""이미지를 분석하겠습니다"", ""표를 찾았습니다""와 같은 불필요한 서술은 절대 하지 마세요.
                                            - 데이터 구조나 JSON에 대한 기술적 언급을 하지 마세요.
                                            - 오직 추출된 '정보 내용'만 출력하세요.

                                        [출력 형식]
                                        - 일반 텍스트는 그대로 서술형으로 작성.
                                        - 표는 마크다운 표 형식을 준수하여 작성.");
                //history.AddSystemMessage(@"이미지의 모든 텍스트를 그대로 추출하세요. 
                //                            표가 있으면 표도 추출하세요.");

                contentItems.Add(new ImageContent(imageBytes, "image/png"));
                history.AddUserMessage(contentItems);

                var executionSettings = new OpenAIPromptExecutionSettings
                {
                    Temperature = 0.2,
                    ExtensionData = new Dictionary<string, object>
                    {
                        { "keep_alive", "1m" },
                        { "num_ctx", 16384 },
                        { "num_predict", 8192 }
                    }
                };

                Console.WriteLine($"OCR 처리중...{fileData.PageNum}/{fileData.TotalPage} [{DateTime.Now.ToString("HH:mm:ss")}]");
                var updates = await selectedService.GetChatMessageContentAsync(history, executionSettings: executionSettings, kernel: _kernel);

                string result = updates.Content;

                // 디버깅 로그
                //Console.WriteLine($"[OCR 결과 길이] {result?.Length ?? 0}자");
                //Console.WriteLine($"[OCR 결과 미리보기] {result?.Substring(0, Math.Min(100, result?.Length ?? 0))}...");
                //string result = await _ollamaVL.OCRAsync(imageBytes, fileData.IsHigh);

                //if (string.IsNullOrEmpty(result))
                //{
                //    Console.WriteLine("모델이 응답을 생성하지 못했습니다.");
                //    await Response.WriteAsync(result);
                //}
                //else
                //{
                //    await Response.WriteAsync(result);
                //}

                await Response.WriteAsync(result);
            }
            catch (System.ClientModel.ClientResultException ex) when (ex.Message.Contains("500"))
            {
                string errorMsg = "로컬 LLM 서버 응답 오류입니다. GPU 메모리가 부족하거나 서버가 재시작 중일 수 있습니다.";
                Console.WriteLine($"[LLM Error] {ex.Message}");
                return;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[General Error] {ex.Message}");
                return;
            }
        }

        [HttpPost]
        public async Task GetChatRoomName([FromBody] string message)
        {
            try
            {
                Console.WriteLine("ChatRoomName");
                var chatService = _kernel.GetRequiredService<IChatCompletionService>("GeneralChat");

                var history = new ChatHistory();
                history.AddSystemMessage(@"채팅룸 제목을 지어야 합니다 메세지의 질문 핵심을 20자 이내로 요약해 주세요");

                history.AddUserMessage(message);

                var executionSettings = new OpenAIPromptExecutionSettings
                {
                    Temperature = 0,
                    ExtensionData = new Dictionary<string, object>
                    {
                        { "strict", false },
                        { "keep_alive", "1m" },
                        { "num_ctx", 16384 }
                    }
                };

                Console.WriteLine($"채팅방 제목 생성중... [{DateTime.Now.ToString("HH:mm:ss")}]");
                var updates = await chatService.GetChatMessageContentAsync(history, executionSettings: executionSettings, kernel: _kernel);

                string result = updates.Content;

                await Response.WriteAsync(result);
            }
            catch (System.ClientModel.ClientResultException ex) when (ex.Message.Contains("500"))
            {
                string errorMsg = "로컬 LLM 서버 응답 오류입니다. GPU 메모리가 부족하거나 서버가 재시작 중일 수 있습니다.";
                Console.WriteLine($"[ChatRoomName Error] {ex.Message}");
                return;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ChatRoomName Error] {ex.Message}");
                return;
            }
        }

        [HttpPost]
        public async Task Summary([FromBody] SummaryRequestDTO request)
        {
            try
            {
                Console.WriteLine("Summary");
                var chatService = _kernel.GetRequiredService<IChatCompletionService>("GeneralChat");

                string tagsText = string.Join(", ", request.TagList);

                var history = new ChatHistory();
                history.AddSystemMessage($@"당신은 문서 요약 및 분석 전문가입니다.
                                            [참조 태그]
                                            {tagsText}

                                            ## 지시 사항
                                            1. 목차와 테이블은 제외하고 본문의 핵심 내용만 요약하여 ""Content""에 넣으세요.
                                            2. 위 [참조 태그] 리스트 중에서 본문 내용과 가장 관련이 깊은 태그를 선택하여 ""Tags"" 배열에 넣으세요.
                                            3. [참조 태그]에 적절한 태그가 없다면 본문에서 추출한 핵심 키워드를 사용하세요.
                                            4. 반드시 아래 JSON 형식으로만 답변하고, 그 외의 인사말이나 설명은 절대 생략하세요.

                                            {{
                                                ""Content"": ""요약된 텍스트 내용"",
                                                ""Tags"": ""태그""
                                            }}");

                history.AddUserMessage(request.Message);

                var executionSettings = new OpenAIPromptExecutionSettings
                {
                    Temperature = 0,
                    ResponseFormat = "json_object",
                    ExtensionData = new Dictionary<string, object>
                    {
                        { "strict", false },
                        { "keep_alive", "1m" },
                        { "num_ctx", 16384 }
                    }
                };

                Console.WriteLine($"텍스트 요약중... [{DateTime.Now.ToString("HH:mm:ss")}]");
                var updates = await chatService.GetChatMessageContentAsync(history, executionSettings: executionSettings, kernel: _kernel);

                string rawJson = updates.Content;

                await Response.WriteAsync(rawJson);
            }
            catch (System.ClientModel.ClientResultException ex) when (ex.Message.Contains("500"))
            {
                string errorMsg = "로컬 LLM 서버 응답 오류입니다. GPU 메모리가 부족하거나 서버가 재시작 중일 수 있습니다.";
                Console.WriteLine($"[Summary Error] {ex.Message}");
                return;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Summary Error] {ex.Message}");
                return;
            }
        }

        [HttpPost]
        public async Task<IActionResult> Embedding([FromBody] List<DocChunkDTO> embeddingRequest)
        {
            if (embeddingRequest == null || !embeddingRequest.Any())
                return BadRequest();

            var embaddingService = _kernel.GetRequiredService<ITextEmbeddingGenerationService>("Embadding");

            try
            {
                List<string> textsToEmbed = embeddingRequest.Select(x => x.ChunkText).ToList();
                var embeddings = await embaddingService.GenerateEmbeddingsAsync(textsToEmbed);

                Console.WriteLine($"임베딩 생성 완료: {embeddings.Count}개");

                var collections = await _qdrant.ListCollectionsAsync();
                bool collectionExists = collections.Contains("DocFileInfo");

                if (!collectionExists)
                {
                    Console.WriteLine("컬렉션이 없습니다. 생성 합니다.");

                    await _qdrant.CreateCollectionAsync(collectionName: "DocFileInfo", vectorsConfig: new Qdrant.Client.Grpc.VectorParams
                    {
                        Size = (ulong)embeddings[0].ToArray().Length,
                        Distance = Qdrant.Client.Grpc.Distance.Cosine
                    });

                    Console.WriteLine("컬렉션 생성 완료");
                }

                var pointsToUpsert = new List<PointStruct>();
                for (int i = 0; i < embeddingRequest.Count; i++)
                {
                    var vectorData = embeddings[i].ToArray();

                    if(vectorData.Length == 0)
                    {
                        Console.WriteLine($"Warning: Empty vector for chunk {i}");
                        continue;
                    }

                    Console.WriteLine($"Chunk {i}: Vector 길이={vectorData.Length}");

                    var points = new PointStruct
                    {
                        Id = Guid.NewGuid(),
                        Vectors = vectorData,
                        Payload =
                        {
                            { "UID", embeddingRequest[i].UID },
                            { "Title", embeddingRequest[i].Title },
                            { "PageNum", embeddingRequest[i].PageNum },
                            { "ChunkIndex", embeddingRequest[i].ChunkIndex },
                            { "ChunkText", embeddingRequest[i].ChunkText }
                        }
                    };

                    pointsToUpsert.Add(points);
                }

                // Qdrant에 저장
                if (pointsToUpsert.Any())
                {
                    await _qdrant.UpsertAsync("DocFileInfo", pointsToUpsert);
                    Console.WriteLine($"[성공] {pointsToUpsert.Count}개의 벡터가 Qdrant에 저장되었습니다.");
                }

                return Ok();
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
                return StatusCode(500);
            }
        }
    }
}
