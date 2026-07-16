using System.ComponentModel;
using System.Text.Json;
using ClosedXML.Excel;
using Microsoft.SemanticKernel;

namespace EDMS.Components.Plugins
{
    public class ExcelPlugin
    {
        private readonly string _savePath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "downloads");

        public ExcelPlugin()
        {
            if (!Directory.Exists(_savePath)) Directory.CreateDirectory(_savePath);
        }

        [KernelFunction]
        [Description("JSON 데이터를 엑셀 파일로 변환하고 다운로드 경로를 반환합니다.")]
        public async Task<string> CreateExcelFromJson(
            [Description("엑셀로 만들 JSON 데이터 문자열")] string jsonData,
            [Description("저장할 파일 이름 (확장자 제외)")] string fileName)
        {
            try
            {
                var data = JsonSerializer.Deserialize<List<Dictionary<string, object>>>(jsonData);

                using var workbook = new XLWorkbook();
                var worksheet = workbook.Worksheets.Add("Sheet1");

                // 헤더 작성
                var properties = data[0].Keys.ToList();
                for (int i = 0; i < properties.Count; i++)
                {
                    worksheet.Cell(1, i + 1).Value = properties[i];
                }

                // 데이터 작성
                for (int row = 0; row < data.Count; row++)
                {
                    for (int col = 0; col < properties.Count; col++)
                    {
                        worksheet.Cell(row + 2, col + 1).Value = data[row][properties[col]]?.ToString();
                    }
                }

                var fullFileName = $"{fileName}_{DateTime.Now:yyyyMMddHHmmss}.xlsx";
                var filePath = Path.Combine(_savePath, fullFileName);
                workbook.SaveAs(filePath);

                // 사용자가 접근 가능한 URL 반환
                return $"/downloads/{fullFileName}";
            }
            catch (Exception ex)
            {
                return $"엑셀 생성 중 오류 발생: {ex.Message}";
            }
        }
    }
}
