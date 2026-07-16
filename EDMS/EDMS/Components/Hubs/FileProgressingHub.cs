using EDMS.Components.BackGroundServices;
using EDMS.Components.Models;
using Microsoft.AspNetCore.SignalR;
using System.Collections.Concurrent;
using System.Text.Json;

namespace EDMS.Components.Hubs
{
    public class FileProgressingHub : Hub
    {
        public async Task JoinGroup()
        {
            await Groups.AddToGroupAsync(Context.ConnectionId, $"progressInfo");

            var currentProgress = BackgroundProcessorService._progressData.ToDictionary(
                kvp => kvp.Key,
                kvp => kvp.Value
            );

            if (currentProgress.Any())
            {
                await Clients.Caller.SendAsync("ProgressInfo", currentProgress);
            }
        }

        public async Task OutGroup()
        {
            await Groups.RemoveFromGroupAsync(Context.ConnectionId, $"progressInfo");
        }
    }
}
