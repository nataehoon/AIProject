using System.Text.Json.Serialization;
using Telerik.SvgIcons;

namespace EDMS.Components.Models.Entity
{
    public class ChatRoom
    {
        [JsonPropertyName("idx")]
        public string IDX { get; set; } = Guid.NewGuid().ToString();
        [JsonPropertyName("uid")]
        public string UID { get; set; }
        [JsonPropertyName("userid")]
        public string UserId { get; set; }
        [JsonPropertyName("title")]
        public string Title { get; set; }

        [JsonIgnore]
        public virtual ICollection<Chatting> Chatting { get; set; } = new List<Chatting>();
    }
}
