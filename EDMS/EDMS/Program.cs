using DocumentFormat.OpenXml.Office2016.Drawing.ChartDrawing;
using EDMS.Components;
using EDMS.Components.BackGroundServices;
using EDMS.Components.Database;
using EDMS.Components.Extensions;
using EDMS.Components.Hubs;
using EDMS.Components.Interface;
using EDMS.Components.Service;
using Microsoft.EntityFrameworkCore;
using Qdrant.Client;

var builder = WebApplication.CreateBuilder(args);

var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
if (string.IsNullOrWhiteSpace(connectionString))
{
    throw new InvalidOperationException(
        "ConnectionStrings:DefaultConnection 설정이 필요합니다. 환경 변수 ConnectionStrings__DefaultConnection을 사용하세요.");
}

var serverVersion = ServerVersion.AutoDetect(connectionString);

// 3. DbContextFactory 등록 (Blazor Server 권장 방식)
builder.Services.AddDbContextFactory<MyDbContext>(options =>
    options.UseMySql(connectionString, serverVersion)
           // 개발 중 상세한 에러 확인을 위한 옵션 (선택)
           .EnableSensitiveDataLogging()
           .EnableDetailedErrors());

builder.Services.AddTelerikBlazor();
builder.Services.AddControllers();

builder.Services.AddHttpClient("AIClient", client =>
{
    client.Timeout = TimeSpan.FromMinutes(500); // 10분으로 설정
});
builder.Services.AddScoped<OllamaVLService>();
builder.Services.AddScoped<IDapperConnector, DapperConnector>();
builder.Services.AddScoped<IDocFileService, DocFileService>();
builder.Services.AddScoped<IChatService, ChatService>();

//백그라운드 서비스
builder.Services.AddSingleton<BackgroundQueue>();
builder.Services.AddScoped<IBackgroundProcessorService, BackgroundProcessorService>();
builder.Services.AddHostedService<QueuedBackgroundService>();

builder.Services.AddSingleton(sp =>
{
    var configuration = sp.GetRequiredService<IConfiguration>();
    var host = configuration["Qdrant:Host"];
    var grpcPort = configuration.GetValue<int?>("Qdrant:GrpcPort");

    if (string.IsNullOrWhiteSpace(host) || grpcPort is null)
    {
        throw new InvalidOperationException(
            "Qdrant:Host 및 Qdrant:GrpcPort 설정이 필요합니다. 환경 변수 Qdrant__Host와 Qdrant__GrpcPort를 사용하세요.");
    }

    return new QdrantClient(host, grpcPort.Value);
});

builder.Services.AddSignalR();

builder.Services.AddServerSideBlazor(options =>
    {
        options.DisconnectedCircuitMaxRetained = 100;
        options.DisconnectedCircuitRetentionPeriod = TimeSpan.FromMinutes(3);
        options.JSInteropDefaultCallTimeout = TimeSpan.FromMinutes(1);
        options.MaxBufferedUnacknowledgedRenderBatches = 10;
    }).AddHubOptions(options =>
    {
        options.MaximumReceiveMessageSize = 300 * 1024 * 1024; // 10MB
        options.EnableDetailedErrors = true;
    });

builder.Services.AddSemanticKernelServices(builder.Configuration);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();

app.UseStaticFiles();
app.UseAntiforgery();

app.MapHub<FileProgressingHub>("/fileProcessingHub");

app.MapControllers();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
