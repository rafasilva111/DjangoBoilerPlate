###
# General imports
##

## Default
import os
import asyncio
import json

## URL Parsing
from urllib.parse import parse_qs

## Channels
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

### App-specific imports

## Models
from apps.task_app.models import Task

class LogConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming log data from a task to a connected client.

    Attributes:
        task_group_name (str): Group name for the WebSocket channel associated with a task.
        log_file_path (str): Path to the log file of the task.
        log_file (file): File object for the task's log file.
    """
    
    @database_sync_to_async
    def get_task(self, task_id):
        """
        Fetches the Task instance with the specified task ID from the database.

        Args:
            task_id (int): The ID of the task to retrieve.

        Returns:
            Task: The Task instance if found, or None if not found.
        """
        try:
            task = Task.objects.get(id=task_id)
            return task
        except Task.DoesNotExist:
            return None
        
    async def connect(self):
        """
        Handles the WebSocket connection by associating the client with a task's log stream.
        
        - Dynamically assigns a task-based group name.
        - Retrieves the Task instance and checks if the log file exists.
        - If valid, accepts the connection and begins streaming new log lines.
        - If invalid, closes the connection.
        """
        task_id = self.scope['url_route']['kwargs']['task_id']
        self.task_group_name = f"task_{task_id}"
        
        # Get Task and log path
        task = await self.get_task(task_id)
        
        if task is None:
            await self.close()
            return
            
        self.log_file_path = task.log_path

        # If the log file exists, start reading from it and send updates
        if self.log_file_path and os.path.isfile(self.log_file_path):
            await self.accept()
            
            # Open the log file and move to its end
            self.log_file = open(self.log_file_path, 'r')
            self.log_file.seek(0, os.SEEK_END)  # Move to the end of the file
            
            # Periodically check for new lines in the log file
            while True:
                line = self.log_file.readline()
                
                if line:
                    await self.send(text_data=json.dumps({
                        "type": "log_line",
                        "line": line
                    }))
                else:
                    await asyncio.sleep(1)
                    
        else:
            await self.close()

    async def disconnect(self, close_code):
        """
        Handles the WebSocket disconnection by closing the log file if open.

        Args:
            close_code (int): WebSocket close code indicating the reason for disconnection.
        """
        if hasattr(self, 'log_file'):
            self.log_file.close()
