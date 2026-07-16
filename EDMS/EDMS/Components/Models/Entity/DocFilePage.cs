using System.Text.Json.Serialization;

namespace EDMS.Components.Models.Entity
{
    public class DocFilePage
    {
        public string IDX { get; set; }
        public string UID { get; set; }
        public int PageNum { get; set; }
        public string Content { get; set; }
        public string Link_Doc { get; set; }
        public DateTime CreateAt { get; set; }
        public DateTime UpdateAt { get; set; }

        [JsonIgnore]
        public virtual DocFileInfo? Link_Doc_Navigation { get; set; }
    }
}
