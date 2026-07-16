using System.Text.Json.Serialization;

namespace EDMS.Components.Models.Entity
{
    public class Chatting
    {
        [JsonPropertyName("idx")]
        public string IDX { get; set; } = Guid.NewGuid().ToString();
        [JsonPropertyName("uid")]
        public string UID { get; set; } = Guid.NewGuid().ToString();
        [JsonPropertyName("isuser")]
        public bool IsUser { get; set; }
        [JsonPropertyName("content")]
        public string Content { get; set; }
        [JsonPropertyName("createat")]
        public DateTime CreateAt { get; set; }
        [JsonPropertyName("link_roomid")]
        public string Link_RoomId { get; set; }

        [JsonIgnore]
        public virtual ChatRoom? Link_RoomId_Navigation { get; set; }
    }
}
