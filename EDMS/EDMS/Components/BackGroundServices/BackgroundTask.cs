namespace EDMS.Components.BackGroundServices
{
    public class BackgroundTask
    {
        public string TaskId { get; set; }
        public string Type { get; set; }
        public DateTime CreatedAt { get; set; } = DateTime.Now;
        public Dictionary<string, object> data { get; set; }
    }
}
