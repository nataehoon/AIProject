using EDMS.Components.Models.DTO;
using Microsoft.AspNetCore.Mvc;
using System.Collections.ObjectModel;

namespace EDMS.Components.Controller
{
    [Route("api/[action]")]
    [ApiController]
    public class FileManageController : ControllerBase
    {
        [HttpPost]
        public async Task<IActionResult> GetFileList([FromBody] string path)
        {
            try
            {
                DirectoryInfo dir = new DirectoryInfo(path);

                List<FileManageDTO> fileList = new List<FileManageDTO>();
                
                await GetChild(dir, null, fileList);
                    
                return Ok(fileList);
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                return StatusCode(500);
            }
        }

        private async Task GetChild(DirectoryInfo dir, string? parentId, List<FileManageDTO> fileList)
        {
            try
            {
                string id = Guid.NewGuid().ToString();
                FileManageDTO addDir = new();
                addDir.Id = id;
                addDir.ParentId = parentId;
                addDir.Name = dir.Name;
                addDir.IsDirectory = true;
                addDir.HasDirectories = dir.GetDirectories().Any();
                addDir.Extension = string.Empty;
                addDir.DateCreated = dir.CreationTime;
                addDir.DateCreatedUtc = dir.CreationTimeUtc;
                addDir.DateModified = dir.LastWriteTime;
                addDir.DateModifiedUtc = dir.LastWriteTimeUtc;
                addDir.Path = dir.FullName;
                addDir.Size = 0;

                fileList.Add(addDir);

                foreach (var item in dir.GetFiles())
                {
                    FileManageDTO addFile = new();
                    addFile.Id = Guid.NewGuid().ToString();
                    addFile.ParentId = id;
                    addFile.Name = item.Name;
                    addFile.IsDirectory = false;
                    addFile.HasDirectories = false;
                    addFile.Extension = item.Extension;
                    addFile.DateCreated = item.CreationTime;
                    addFile.DateCreatedUtc = item.CreationTimeUtc;
                    addFile.DateModified = item.LastWriteTime;
                    addFile.DateModifiedUtc = item.LastWriteTimeUtc;
                    addFile.Path = item.FullName;
                    addFile.Size = item.Length;

                    fileList.Add(addFile);
                }

                foreach(var item in dir.GetDirectories())
                {
                    await GetChild(item, id, fileList);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
            }
        }
    }
}
