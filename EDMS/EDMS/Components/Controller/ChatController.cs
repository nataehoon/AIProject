using EDMS.Components.Interface;
using EDMS.Components.Models.Entity;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;

namespace EDMS.Components.Controller
{
    [Route("api/[action]")]
    [ApiController]
    public class ChatController : ControllerBase
    {
        private readonly IHttpClientFactory _clientInfo;
        private readonly IChatService _chatService;

        public ChatController(IHttpClientFactory clientInfo, IChatService chatService)
        {
            _clientInfo = clientInfo;
            _chatService = chatService;
        }

        [HttpPost]
        public async Task<IActionResult> GetChatRoomList([FromBody] string userId)
        {
            try
            {
                var roomList = await _chatService.GetChatRoomList(userId);

                return Ok(roomList);
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                return StatusCode(500);
            }
        }

        [HttpPost]
        public async Task<IActionResult> GetChattingList([FromBody] string roomId)
        {
            try
            {
                var chatList = await _chatService.GetChatList(roomId);

                return Ok(chatList);
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                return StatusCode(500);
            }
        }

        [HttpPost]
        public async Task<IActionResult> CreateChatRoom([FromBody] ChatRoom roomItem)
        {
            try
            {
                var result = await _chatService.CreateChatRoom(roomItem);

                if (result)
                {
                    return Ok("생성 되었습니다.");
                }
                else
                {
                    return BadRequest();
                }
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                return StatusCode(500);
            }
        }

        [HttpPost]
        public async Task<IActionResult> CreateChatting([FromBody] List<Chatting> chatItems)
        {
            try
            {
                var result = await _chatService.CreateChatting(chatItems);

                if (result)
                {
                    return Ok("생성 되었습니다.");
                }
                else
                {
                    return BadRequest();
                }
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                return StatusCode(500);
            }
        }
    }
}
