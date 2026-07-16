using System.Collections.Concurrent;

namespace EDMS.Components.BackGroundServices
{
    public class BackgroundQueue
    {
        private readonly ConcurrentQueue<BackgroundTask> _queue = new();

        public int Count => _queue.Count;
        public bool IsEmpty => _queue.IsEmpty;

        public void Enqueue(BackgroundTask task)
        {
            try
            {
                if(!HasPendingTask(task.Type, task.TaskId))
                {
                    _queue.Enqueue(task);
                    Console.WriteLine($"Enqueued task: {task.Type} for {task.TaskId} (Queue size: {Count})");
                }
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
            }
        }

        public bool TryDequeue(out BackgroundTask task) // 큐에서 꺼내기
        {
            return _queue.TryDequeue(out task);
        }

        public bool HasPendingTask(string type, string taskId)
        {
            try
            {
                return _queue.Any(t => t.Type == type && t.TaskId == taskId);
            }
            catch(Exception ex)
            {
                Console.WriteLine($"{ex.Message}");
                throw;
            }
        }
    }
}
