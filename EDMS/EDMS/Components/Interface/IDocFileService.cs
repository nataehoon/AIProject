using EDMS.Components.Models.Entity;

namespace EDMS.Components.Interface
{
    public interface IDocFileService
    {
        Task<List<DocFileInfo>?> GetDocFileList();

        Task<IEnumerable<string>?> GetTagList();
    }
}
