using Microsoft.AspNetCore.Mvc;
using System.Text;

namespace EDMS.Components.Service
{
    public class APIService
    {
        public static async Task<string?> PostAPI(string baseUrl, string endPoint, object? data)
        {
            try
            {
                using var client = new HttpClient();
                client.BaseAddress = new Uri(baseUrl);

                Console.WriteLine($"endPoint : {endPoint}");
                Console.WriteLine($"data : {data}");

                using var response = await client.PostAsJsonAsync(endPoint, data);
                Console.WriteLine($"response : {response.StatusCode}");

                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();

                    return result;
                }
                else
                {
                    return "error";
                }
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                throw;
            }
        }
    }
}
