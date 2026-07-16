namespace EDMS.Components.Models.DTO
{
    public class ChatDTO
    {
        public string UserId { get; set; }
        public string RoomId { get; set; }
        public string Role { get; set; }
        public string Content { get; set; }
        public bool IsUser { get; set; }
        public DateTime Timestamp { get; set; }
    }
}
