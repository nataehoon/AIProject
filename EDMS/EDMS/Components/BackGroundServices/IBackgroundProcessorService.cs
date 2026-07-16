namespace EDMS.Components.BackGroundServices
{
    public interface IBackgroundProcessorService
    {
        Task ProcessAsync(BackgroundTask task);
    }
}
