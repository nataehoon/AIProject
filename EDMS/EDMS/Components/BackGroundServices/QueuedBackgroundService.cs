namespace EDMS.Components.BackGroundServices
{
    public class QueuedBackgroundService : BackgroundService
    {
        private readonly BackgroundQueue _queue;
        private readonly IServiceProvider _serviceProvider;

        public QueuedBackgroundService(BackgroundQueue queue, IServiceProvider serviceProvider)
        {
            _queue = queue;
            _serviceProvider = serviceProvider;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            try
            {
                while (!stoppingToken.IsCancellationRequested)
                {
                    try
                    {
                        await ProcessPendingTasks(stoppingToken);

                        if(_queue.Count == 0)
                        {
                            await Task.Delay(1000, stoppingToken);
                        }
                    }
                    catch(Exception ex)
                    {
                        Console.WriteLine(ex.Message);
                        await Task.Delay(2000, stoppingToken);
                    }
                }
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
            }
        }

        private async Task ProcessPendingTasks(CancellationToken stoppingToken)
        {
            try
            {
                int processedCount = 0;
                const int maxBatchSize = 10;

                while(_queue.TryDequeue(out var task) && processedCount < maxBatchSize && !stoppingToken.IsCancellationRequested)
                {
                    await ProcessSingleTask(task);
                }
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
            }
        }

        private async Task ProcessSingleTask(BackgroundTask task)
        {
            try
            {
                using var scope = _serviceProvider.CreateScope();
                var processor = scope.ServiceProvider.GetRequiredService<IBackgroundProcessorService>();

                await processor.ProcessAsync(task);

                Console.WriteLine($"작업 완료: {task.Type}");
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
            }
        }

        public override async Task StopAsync(CancellationToken stoppingToken)
        {
            try
            {
                var remainingTasks = _queue.Count;

                if(remainingTasks > 0)
                {
                    Console.WriteLine($"중지된 백그라운드 서비스 {remainingTasks}건");

                    var timeout = TimeSpan.FromSeconds(30);

                    using var timeoutCts = new CancellationTokenSource(timeout);
                    using var combinedCts = CancellationTokenSource.CreateLinkedTokenSource(stoppingToken, timeoutCts.Token);

                    try
                    {
                        await ProcessPendingTasks(combinedCts.Token);
                    }
                    catch(Exception ex)
                    {
                        Console.WriteLine("백그라운드 서비스를 중지합니다.");
                    }
                }
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
            }
        }
    }
}
