using EDMS.Components.Interface;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;

namespace EDMS.Components.Controller
{
    [Route("api/[action]")]
    [ApiController]
    public class DocFileController : ControllerBase
    {
        private readonly IDocFileService _docService;

        public DocFileController(IDocFileService docService)
        {
            _docService = docService;
        }

        [HttpPost]
        public async Task<IActionResult> GetDocList()
        {
            try
            {
                Console.WriteLine("문서 리스트");

                var docList = await _docService.GetDocFileList();

                return Ok(docList);
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                return StatusCode(500);
            }
        }

        [HttpPost]
        public async Task<IActionResult> GetTagList()
        {
            try
            {
                var tagList = await _docService.GetTagList();

                return Ok(tagList);
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                return StatusCode(500);
            }
        }
    }
}
