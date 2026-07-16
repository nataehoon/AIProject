using Dapper;
using EDMS.Components.Database;
using EDMS.Components.Interface;
using EDMS.Components.Models.Entity;

namespace EDMS.Components.Service
{
    public class DocFileService : IDocFileService
    {
        private readonly IDapperConnector _dapper;

        public DocFileService(IDapperConnector dapper)
        {
            _dapper = dapper;
        }

        public async Task<List<DocFileInfo>?> GetDocFileList()
        {
            try
            {
                using var db = _dapper.CreateConnection();

                string sql = "SELECT * FROM doc_file_info";

                var result = await db.QueryAsync<DocFileInfo>(sql);

                if (!result.Any())
                {
                    return null;
                }

                return result.ToList();
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                throw;
            }
        }

        public async Task<IEnumerable<string>?> GetTagList()
        {
            try
            {
                using var db = _dapper.CreateConnection();

                string sql = "SELECT Tags FROM doc_file_info";

                var result = await db.QueryAsync<string>(sql);

                if (result.Any())
                {
                    return result;
                }

                return null;
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                throw;
            }
        }
    }
}
