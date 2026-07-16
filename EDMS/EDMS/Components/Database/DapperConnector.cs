using System.Data;
using MySqlConnector;

namespace EDMS.Components.Database
{
    public interface IDapperConnector
    {
        IDbConnection CreateConnection();
    }

    public class DapperConnector : IDapperConnector
    {
        private readonly string _connectionString;

        public DapperConnector(IConfiguration configuration)
        {
            _connectionString = configuration.GetConnectionString("DefaultConnection")
                ?? throw new InvalidOperationException(
                    "ConnectionStrings:DefaultConnection 설정이 필요합니다. 환경 변수 ConnectionStrings__DefaultConnection을 사용하세요.");

            if (string.IsNullOrWhiteSpace(_connectionString))
            {
                throw new InvalidOperationException(
                    "ConnectionStrings:DefaultConnection 설정이 비어 있습니다. 환경 변수 ConnectionStrings__DefaultConnection을 사용하세요.");
            }
        }

        public IDbConnection CreateConnection()
        {
            return new MySqlConnection(_connectionString);
        }
    }
}
