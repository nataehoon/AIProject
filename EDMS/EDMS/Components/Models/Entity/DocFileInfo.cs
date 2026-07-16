using System.Text.Json.Serialization;

namespace EDMS.Components.Models.Entity
{
    public class DocFileInfo
    {
        [JsonPropertyName("idx")]
        public string IDX { get; set; }
        [JsonPropertyName("uid")]
        public string UID { get; set; }
        [JsonPropertyName("fileName")]
        public string FileName { get; set; }
        [JsonPropertyName("Title")]
        public string Title { get; set; }
        [JsonPropertyName("mainText")]
        public string MainText { get; set; }
        [JsonPropertyName("fileSize")]
        public int FileSize { get; set; }
        [JsonPropertyName("registrant")]
        public string Registrant { get; set; }
        [JsonPropertyName("filePath")]
        public string FilePath { get; set; }
        [JsonPropertyName("tags")]
        public string Tags { get; set; }
        [JsonPropertyName("createAt")]
        public DateTime CreateAt { get; set; }
        [JsonPropertyName("updateAt")]
        public DateTime UpdateAt { get; set; }

        [JsonIgnore]
        public virtual ICollection<DocFilePage> DocFilePage { get; set; } = new List<DocFilePage>();
    }
}
