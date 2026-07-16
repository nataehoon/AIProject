using Dapper;
using EDMS.Components.Database;
using EDMS.Components.Interface;
using EDMS.Components.Models.Entity;
using System.Text.Json;

namespace EDMS.Components.Service
{
    public class ChatService : IChatService
    {
        private readonly IDapperConnector _dapper;

        public ChatService(IDapperConnector dapper)
        {
            _dapper = dapper;
        }

        public async Task<List<ChatRoom>?> GetChatRoomList(string userId)
        {
            try
            {
                using var db = _dapper.CreateConnection();

                string sql = "SELECT * FROM chat_room WHERE UserId = @userId";

                var result = await db.QueryAsync<ChatRoom>(sql, new { userId = userId });

                if (result.Any())
                {
                    return result.ToList();
                }

                return null;
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                throw;
            }
        }

        public async Task<List<Chatting>?> GetChatList(string roomId)
        {
            try
            {
                using var db = _dapper.CreateConnection();

                string sql = "SELECT * FROM chatting WHERE Link_RoomId = @roomId";

                var result = await db.QueryAsync<Chatting>(sql, new { roomId });

                Console.WriteLine($"result : {JsonSerializer.Serialize(result)}");

                if (result.Any())
                {
                    return result.ToList();
                }

                return null;
            }
            catch(Exception ex)
            {
                Console.WriteLine(ex.Message);
                throw;
            }
        }

        public async Task<bool> CreateChatRoom(ChatRoom roomItem)
        {
            try
            {
                using var db = _dapper.CreateConnection();

                string sql = "INSERT INTO chat_room(IDX, UID, UserId, Title) VALUES(@IDX, @UID, @UserId, @Title)";

                var result = await db.ExecuteAsync(sql, roomItem);

                if (result == 0 )
                {
                    return false;
                }
                else
                {
                    return true;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
                throw;
            }
        }

        public async Task<bool> CreateChatting(List<Chatting> chatItems)
        {
            try
            {
                using var db = _dapper.CreateConnection();

                string sql = "INSERT INTO chatting(IDX, UID, IsUser, Content, CreateAt, Link_RoomId) VALUES(@IDX, @UID, @IsUser, @Content, @CreateAt, @Link_RoomId)";

                var result = await db.ExecuteAsync(sql, chatItems);

                if (result == 0)
                {
                    return false;
                }
                else
                {
                    return true;
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
