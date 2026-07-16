using EDMS.Components.Models.Entity;

namespace EDMS.Components.Interface
{
    public interface IChatService
    {
        Task<List<ChatRoom>?> GetChatRoomList(string userId);
        Task<List<Chatting>?> GetChatList(string roomId);

        Task<bool> CreateChatRoom(ChatRoom roomItem);
        Task<bool> CreateChatting(List<Chatting> chatItems);
    }
}
