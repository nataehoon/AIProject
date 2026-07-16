namespace EDMS.Components.Models.DTO
{
    public class SearchResultDTO
    {
        public string EBookNM { get; set; }
        public int PageNum { get; set; }
        public string Text { get; set; }
        public int ChunkIndex { get; set; }
        public string Score { get; set; }
    }
}
