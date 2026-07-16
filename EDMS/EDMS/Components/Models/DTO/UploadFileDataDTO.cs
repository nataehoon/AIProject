namespace EDMS.Components.Models.DTO
{
    public class UploadFileDataDTO
    {
        public string FileId { get; set; }
        public string FileName { get; set; }
        public List<byte[]> Images { get; set; } = new List<byte[]>();
        public string FileType { get; set; } // "pdf", "image", "excel"
        public string FilePath { get; set; }
        public int FileSize { get; set; }
        public bool IsHigh { get; set; }
        public string UploadPath { get; set; }
        public string Extension { get; set; }
    }
}
