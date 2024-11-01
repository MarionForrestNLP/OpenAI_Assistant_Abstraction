# Imports
import os

from openai import AssistantEventHandler, OpenAI
from openai.types import beta as Beta_Types
from openai.types.beta import AssistantStreamEvent
from openai.types.beta.threads import Message, Text, TextDelta, Run
from openai.types.beta.threads.runs import ToolCall, ToolCallDelta
from typing_extensions import override

"""
Vector Storage
"""

# Vestor Storage Constants
DEFAULT_LIFE_TIME = 1
DEFAULT_VECTOR_STORE_NAME = "Vector_Storage"
DEFAULT_FILE_PURPOSE = "assistants"
FILE_PURPOSE_ENUM = ["assistants", "fine-tune", "vision", "batch"]

# Vector Storage Class
class Vector_Storage:
    """
    Vector Storage Class

    This class is used to create, modify, and delete vector stores. It also provides methods to attach files to the vector store.

    Properties:
        client (OpenAI): The OpenAI client used to access the OpenAI API.
        name (str): The name of the vector store.
        days_until_expiration (int): The time in terms of 24 hour days that the vector store will be kept alive.
        intance (dict): The vector store instance.

    Methods:
        Retrieve_Vector_Store(vector_store_id:str) -> dict
        Delete_Vector_Store(delete_attached:bool|None=None) -> bool
        Modify_Vector_Store(new_name:str=None, new_life_time:int=None) -> dict
        Get_Attributes() -> dict
        Attach_Existing_File(file_id:str) -> str
        Attach_New_File(file_path:str) -> str
    """

    # Properties
    client = None
    """The OpenAI client used to access the OpenAI API."""
    name = ""
    """The name of the vector store."""
    days_until_expiration = 0
    """The time in terms of 24 hour days that the vector store will be kept alive."""
    intance = None
    """The vector store instance."""

    # Constructor
    def __init__(self, openai_client:OpenAI, name:str|None=None, life_time:int|None=None):
        """
        Initializes a new instance of the vector store class.

        Parameters:
        ---
            openai_client (OpenAI): The OpenAI client used for API communication.
            name (str): The name of the vector store. | OPTIONAL | DEFAULT: "Vector_Storage".
            life_time (int): The number of days until the vector store expires. | OPTIONAL | DEFAULT: 1.
        """
        # Handle Defaults
        if name is None:
            name = DEFAULT_VECTOR_STORE_NAME
        if life_time is None:
            life_time = DEFAULT_LIFE_TIME

        # Set properties
        self.client = openai_client
        self.name = name
        self.days_until_expiration = life_time

        # Create the vector store
        self.intance = self.client.beta.vector_stores.create(
            name=self.name,
            expires_after={
                "anchor": "last_active_at",
                "days": self.days_until_expiration
            }
        )
    # End of Constructor

    def Retrieve_Vector_Store(self, vector_store_id: str) -> dict:
        """
        Retrieves a vector store with the given ID.

        Parameters:
        ---
            vector_store_id (str): The ID of the vector store to retrieve.

        Returns:
        ---
            dict: The retrieved vector store as a dictionary, or None if the vector store could not be retrieved.
        """
        # Initialize the returned vector store
        retrieved_vector_store = None

        # Try to retrieve the vector store
        try:
            # Retrieve the vector store
            retrieved_vector_store = self.client.beta.vector_stores.retrieve(vector_store_id)
        except Exception as e:
            # Return none if the vector store could not be retrieved
            return None

        # Check if the vector store was retrieved
        if retrieved_vector_store is None:
            # Return none if the vector store was not found
            return None

        # Replace the instance with the retrieved vector store
        if self.Delete_Vector_Store():
            self.intance = retrieved_vector_store
            self.name = self.intance.name
            self.days_until_expiration = self.intance.expires_after["days"]

            # Return the retrieved vector store
            return self.intance
        else:
            # Return none if the current vector store was not deleted
            return None
    # End of Retrieve_Vector_Store

    def Delete_Vector_Store(self, delete_attached: bool|None=False) -> bool:
        """
        Deletes the vector store and optionally deletes the files attached to it.

        Parameters:
        ---
            delete_attached (bool, optional): If True, deletes the files attached to the vector store. 
                Defaults to False.

        Returns:
        ---
            bool: True if the vector store is successfully deleted, False otherwise.
        """
        # Return False if the vector store instance is None
        if self.intance is None:
            return False

        # Delete files attached to the vector store if specified
        if delete_attached:
            # Get the files attached to the vector store
            try:
                attached_files = self.client.beta.vector_stores.files.list(vector_store_id=self.intance.id, limit=100).data
            except Exception as e:
                # Log the exception and return False if there was an error retrieving the files
                print(f"Error retrieving files attached to vector store: {e}")
                return False
            for attached_file in attached_files:
                # Delete the attached file
                try:
                    self.client.files.delete(attached_file.id)
                except Exception as e:
                    # Log the exception and return False if there was an error deleting the file
                    print(f"Error deleting file {attached_file.id}: {e}")
                    return False
            # Loop End

        # Delete the vector store
        try:
            deletion_status = self.client.beta.vector_stores.delete(self.intance.id)
        except Exception as e:
            # Log the exception and return False if there was an error deleting the vector store
            print(f"Error deleting vector store: {e}")
            return False

        # Set the instance to None
        self.intance = None

        # Return the deletion status
        return deletion_status.deleted
    # End of Delete_Vector_Store

    def Modify_Vector_Store(self, new_name: str = None, new_life_time: int = None) -> dict:
        """
        Modifies the vector store by updating its name and expiration time.

        Parameters:
        ---
            new_name (str, optional): The new name for the vector store. Defaults to None.
            new_life_time (int, optional): The new expiration time in days. Defaults to None.

        Returns:
        ---
            dict: The modified vector store.

        Raises:
        ---
            ValueError: If the vector store instance does not exist or if there is an error modifying the vector store.
        """
        # Check if the vector store instance exists
        if self.intance is None:
            raise ValueError("Vector store instance does not exist")

        # Set the new name and life time
        if new_name is not None:
            self.name = new_name
        if new_life_time is not None:
            self.days_until_expiration = new_life_time

        # Modify the vector store
        try:
            modified_vector_store = self.client.beta.vector_stores.update(
                vector_store_id=self.intance.id,
                name=self.name,
                expires_after={
                    "anchor": "last_active_at",
                    "days": self.days_until_expiration
                }
            )
        except Exception as e:
            raise ValueError(f"Error modifying vector store: {e}")

        # Replace the instance with the modified vector store
        self.intance = modified_vector_store

        # Return the modified vector store
        return self.intance
    # End of Modify_Vector_Store

    def Get_Attributes(self) -> dict:
        """
        Get the attributes of the vector store instance.

        Returns:
        ---
            dict: A dictionary containing the attributes of the vector store instance.
                The dictionary includes the following keys:
                - "id": The ID of the vector store instance.
                - "name": The name of the vector store instance.
                - "status": The status of the vector store instance.
                - "created at": The creation timestamp of the vector store instance.
                - "days until expiration": The number of days until the vector store instance expires.
                - "file count": The total number of files in the vector store instance.
                - "memory usage": The memory usage of the vector store instance in bytes.
        
        Raises:
        ---
            ValueError: If the vector store instance does not exist.
        """
        # Check if the vector store instance exists
        if self.intance is None:
            raise ValueError("Vector store instance does not exist")

        # Create an attributes dictionary
        attributes = {
            "id": self.intance.id,
            "name": self.name,
            "status": self.intance.status,
            "created at": self.intance.created_at,
            "days until expiration": self.days_until_expiration,
            "file count": self.intance.file_counts.total if hasattr(self.intance, "file_counts") else 0,
            "memory usage": self.intance.usage_bytes if hasattr(self.intance, "usage_bytes") else 0,
        }

        # Return the status
        return attributes
    # End of Get_Attributes

    def Attach_Existing_File(self, file_id: str) -> str:
        """
        Attach an existing file to the vector store.

        Parameters:
        ---
            file_id (str): The ID of the file to attach.

        Returns:
        ---
            str: The ID of the attached file.
        """

        # Attach the file
        vector_store_file = self.client.beta.vector_stores.files.create_and_poll(
            vector_store_id=self.intance.id,
            file_id=file_id
        )

        # Return the file's ID
        return vector_store_file.id
    # End of Attach_Existing_File

    def Attach_New_File(self, file_path:str, purpose:str|None=None) -> str:
        """
        Attach a new file to the assistant.

        Parameters:
        ---
            file_path (str): The path of the file to be attached.
            purpose (str|None): The purpose of the file. | OPTIONAL | DEFAULT: None

        Returns:
        ---
            str: The ID of the attached file.
        """

        # Handle Defaults
        if (purpose is None) or (purpose not in FILE_PURPOSE_ENUM):
            purpose = DEFAULT_FILE_PURPOSE

        # Upload the file
        uploaded_file = self.client.files.create(
            file=open(file_path, "rb"),
            purpose=purpose
        )

        # Attach the file
        file_ID = self.Attach_Existing_File(uploaded_file.id)

        # Return the attachment status
        return file_ID
    # End of Attach_New_File
# End of Vector_Storage Class

"""
Assistant
"""

# Assistant Constants
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MESSAGE_HISTORY_LENGTH = 25
DEFAULT_MAX_PROMPT_TOKENS = 10000 # OpenAI recommends at least 20,000 prompt tokens for best results
DEFAULT_MAX_COMPLETION_TOKENS = 10000
DEFAULT_MODEL_PARAMETERS = {
    "temperature": 1.0,
    "top_p": 1.0
}

# Assistant Class
class Assistant:
    """
    This class is designed to abstract interactions with the OpenAI Assistant

    Properties
        client (OpenAI): The OpenAI client instance
        id (str): The ID of the assistant
        name (str): The name of the assistant
        instructions (str): The assistant's context prompt
        tool_set (list): A list of tool dictionaries
        model (str): The model to use for the assistant
        model_parameters (dict): The parameters for the model
        max_prompt_tokens (int): The maximum number of prompt tokens
        max_completion_tokens (int): The maximum number of completion tokens
        vector_store (Vector_Storage): The internal vector store
        intance (openai.types.beta.Assistant): The OpenAI Assistant instance
        thread (openai.types.beta.Thread): The Assistant Thread instance

    Methods
        Delete_Assistant() -> bool
        Attach_Files(file_paths:list[str]) -> bool
        Update_Tool_Set(tool_set:list) -> bool
        Send_Message(message_content:str, message_attachments:list=[]) -> dict
        Get_Response(event_handler:AssistantEventHandler) -> None
        Get_Attributes() -> dict
        Get_Vector_Store() -> Vector_Storage
    """

    # Properties
    client:OpenAI
    """The OpenAI client used to communicate with the OpenAI API."""
    id:str|None = None
    """The ID of the assistant."""
    name:str|None = None
    """The name of the assistant."""
    instructions:str|None = None
    """The assistant's context prompt."""
    tool_set:list|None = None
    """A list of tool dictionaries."""
    model:str|None = None
    """The model to use for the assistant."""
    model_parameters:dict|None = None
    """The parameters for the model."""
    max_prompt_tokens:int|None = None
    """The maximum number of prompt tokens."""
    max_completion_tokens:int|None = None
    """The maximum number of completion tokens."""
    vector_store:Vector_Storage
    """The internal vector store."""
    intance:Beta_Types.Assistant
    """The OpenAI Assistant instance."""
    thread:Beta_Types.Thread
    """The Assistant Thread instance."""

    # Constructor
    def __init__(
            self,
            client:OpenAI, 
            assistant_id:str|None=None, 
            assistant_name:str|None=None, 
            instruction_prompt:str|None=None, 
            tool_set:list|None=[],
            model:str|None=None, 
            model_parameters:dict|None=None,
            max_prompt_tokens:int|None=None, 
            max_completion_tokens:int|None=None
        ):
        """
        This class is designed to abstract interactions with the OpenAI Assistant.
        
        Parameters
        ---
            client (OpenAI): The OpenAI client used to communicate with the OpenAI API. | REQUIRED
            assistant_id (str): The id of the assistant you would like to connect to. If None or left blank, a new assistant will be created. When connecting to a preexisting assistant, all other parameters will be used to modify the assistant. | OPTIONAL | DEFAULT: None
            assistant_name (str): The name of the assistant. | OPTIONAL | DEFAULT: "Assistant"
            instruction_prompt (str): The assistant's context prompt | OPTIONAL | DEFAULT: "You are a simple chat bot."
            tool_set (list): A list of tool dictionaries. | OPTIONAL | DEFAULT: [ {"type": "file_search"} ]
            model (str): The model to use for the assistant. | OPTIONAL | DEFAULT: "gpt-3.5-turbo-0125"
            model_parameters (dict): The parameters for the model. | OPTIONAL | DEFAULT: {temperature: 1.0, top_p: 1.0}
            max_prompt_tokens (int): The maximum number of prompt tokens. | OPTIONAL | DEFAULT: 10000
            max_completion_tokens (int): The maximum number of completion tokens. | OPTIONAL | DEFAULT: 10000
        """
        # Handle Defaults
        if assistant_name is None:
            assistant_name = "Assistant"
        if instruction_prompt is None:
            instruction_prompt = "You are a simple chat bot."
        if (model_parameters is None) or (len(model_parameters.keys()) == 0):
            model_parameters = DEFAULT_MODEL_PARAMETERS
        if model is None:
            model = DEFAULT_MODEL
        if max_prompt_tokens is None:
            max_prompt_tokens = DEFAULT_MAX_PROMPT_TOKENS
        if max_completion_tokens is None:
            max_completion_tokens = DEFAULT_MAX_COMPLETION_TOKENS

        # Verify file_search tool is present
        tool_set = self.__Verify_File_Search_Tool(tool_set)
        
        # Set properties
        self.client = client
        self.name = assistant_name
        self.instructions = instruction_prompt
        self.tool_set = tool_set
        self.model = model
        self.model_parameters = model_parameters
        self.max_prompt_tokens = max_prompt_tokens

        # Create internal vector store
        self.vector_store = Vector_Storage(
            openai_client=self.client,
            name=f"{self.name}_Vector_Store",
            life_time=1
        )

        # Connect to a preexisting assistant
        try:
            # Set instance
            self.intance = self.client.beta.assistants.retrieve(assistant_id)
            self.id = assistant_id # Set id if successfully retrieved

            # Modify properties
            self.intance = self.client.beta.assistants.update(
                assistant_id=self.id,
                model=self.model,
                name=self.name,
                instructions=self.instructions,
                tools=self.tool_set,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [
                            self.vector_store.Get_Attributes()["id"]
                        ]
                    }
                },
                temperature=self.model_parameters["temperature"],
                top_p=self.model_parameters["top_p"],
            )
        except Exception as e:
            # Create assistant
            self.intance = self.client.beta.assistants.create(
                model=self.model,
                name=self.name,
                instructions=self.instructions,
                tools=self.tool_set,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [
                            self.vector_store.Get_Attributes()["id"]
                        ]
                    }
                },
                temperature=self.model_parameters["temperature"],
                top_p=self.model_parameters["top_p"],
            )

            # Set id
            self.id = self.intance.id
        finally:
            # Initialize thread
            self.thread = client.beta.threads.create()
    # End of Constructor

    def __Verify_File_Search_Tool(self, tool_set:list[dict[str, any]]) -> list[dict[str, any]]:
        """
        A function that verifies the presence of the file_search tool in the tool set and adds it if not present.

        Parameters
        ---
        tool_set : list[dict[str, any]]
            A list of tool dictionaries
        
        Returns
        ---
        tool_set : list[dict[str, any]]
            The updated list of tool dictionaries
        """
        def Add_File_Search_Tool(tool_set:list[dict[str, any]]):
            tool_set.append({
                "type": "file_search"
            })
        # Function End

        # Check if tool set is empty
        if len(tool_set) == 0:
            # Add file_search tool
            Add_File_Search_Tool(tool_set)
            return tool_set
        
        # Check if file_search tool is present among the tools
        for tool in tool_set:
            if tool["type"] == "file_search":
                return tool_set
        # Loop end

        # Add file_search tool
        Add_File_Search_Tool(tool_set)
        return tool_set
    # Function End

    def Delete_Assistant(self, clear_vector_store:bool|None=False) -> bool:
        """
        Deletes the assistant. Call this method once you are done using the assistant.

        Parameters
        ---
        clear_vector_store : bool|None, optional
            A flag to delete the files attached to the internal vector store. Defaults to False.

        Returns
        ---
        bool
            True if the assistant is successfully deleted, False otherwise.
        """
        # Return false is the assistant instance is None
        if self.intance is None:
            return False

        # Delete vector store object
        self.vector_store.Delete_Vector_Store(
            # Clear attached files if set to True
            delete_attached=clear_vector_store
        )

        # Delete assistant
        deletion_object = self.client.beta.assistants.delete(
            assistant_id=self.intance.id
        )

        # update instance
        self.intance = None

        # return status
        return deletion_object.deleted
    # Function End

    def Attach_Files(self, file_paths:list[str]|None) -> list[str]:
        """
        Takes in a list of file path strings and adds the respective files to the assistant's internal vector store.
        Returns a list of file IDs.

        Parameters
        ----------
        file_paths : list[str] | None, required
            A list of file paths strings. If None, an empty list is returned.

        Returns
        -------
        list[str]
            A list of file IDs. If a file path does not exist, None is appended to the list.
        """
        # Variable initialization
        id_list = []

        # Check if file paths are provided
        if (file_paths is not None) and (len(file_paths) > 0):
            # Iterate through file paths
            for file_Path in file_paths:
                # Check if file path exists
                if os.path.exists(file_Path) == True:
                    # Send to vector store
                    file_ID = self.vector_store.Attach_New_File(file_path=file_Path)

                    # Add file ID to list
                    id_list.append(file_ID)

                # File path does not exist
                else:
                    id_list.append(None)
            # Loop End
                
            # return status
            return id_list
        
        # No file paths provided
        else:
            return id_list
    # Function End

    def Update_Tool_Set(self, tool_set:list[dict]) -> bool:
        """
        Updates the assistant's tools.

        Parameters
        ----------
        tool_Set : list[dict]
            A list of tool dictionaries

        Returns
        -------
        bool:
            The completions status of the operation
        """

        try:
            # Update tool set
            updated_assistant = self.client.beta.assistants.update(
                assistant_id=self.intance.id,
                tools=tool_set,
            )

            # update intance
            self.intance = updated_assistant
            self.tool_set = tool_set

            # return status
            return True
        except:
            # return status
            return False
    # Function End
    
    def __Create_Message(self, role:str, content:str, attachment_id:str|None=None) -> Message:
        """
        Internal Method to create a new message in the assistant's thread.

        Parameters
            role (str): The role of the originator of the message
            content (str): The content of the message
            attachment_id (str): The file ID of the attachment | OPTIONAL

        Returns
            message (Message): The new message object
        """
        return self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role=role,
            content=content,
            attachments=[{
                "file_id": attachment_id,
                "tools": [{"type": "file_search"}]
            }] if attachment_id is not None else None
        )

    def Send_Message(self, message_content:str, attachment_path:str|None=None, attachment_file_id:str|None=None) -> Message:
        """
        Adds a new message to the assistant's thread
        and returns the new message object.

        Parameters
            message_content (str): The text content of the message
            attachment_path (str): The path to the attachment | OPTIONAL
            attachment_file_id (str): The file ID of the attachment | OPTIONAL
        Returns
            message (Message): The new message object
        """        
        # Variable initialization
        message = None

        # Attachment ID
        if attachment_file_id is not None:
            # Send message
            message = self.__Create_Message(
                role="user",
                content=message_content,
                attachment_id=attachment_file_id
            )

        # Attachment Path
        elif attachment_path is not None:
            # Attach file to vector store
            file_ID = self.vector_store.Attach_New_File(file_path=attachment_path)

            # Send message
            message = self.__Create_Message(
                role="user",
                content=message_content,
                attachment_id=file_ID
            )

        # No attachment
        else:
            # Send message
            message = self.__Create_Message(
                role="user",
                content=message_content
            )
        
        # Return message
        return message
    # Function End

    def Get_Response(self, event_handler:AssistantEventHandler|None=None) -> None:
        """ 
        Streams the assistant's response to the console (or to wherever the event_handler class defines).

        Parameters
            event_handler (AssistantEventHandler): The event handler class to use. | OPTIONAL

        Returns
            None
        """
        # Handle defaults
        if event_handler is None:
            event_handler = Assistant_Event_Handler

        # Run stream
        with self.client.beta.threads.runs.stream(
            thread_id=self.thread.id,
            assistant_id=self.intance.id,
            event_handler=event_handler(client=self.client)
        ) as stream:
            stream.until_done()
    # Function End
    
    def Get_Attributes(self) -> dict:
        """
        Gets the assistant's attributes.

        Parameters
            None

        Returns
            attributes (dict): The assistant's attributes
        """

        attributes = {
            "id": self.intance.id,
            'creation time': self.intance.created_at,
            "name": self.name,
            "instructions": self.instructions,
            "tool_set": self.tool_set,
            "user_defined_functions": self.user_defined_functions,
            "model": self.model,
            "model_parameters": self.model_parameters,
            "vector_store": self.vector_store.Get_Attributes(),
            "thread id": self.thread.id
        }

        return attributes
    # Function End

    def Get_Vector_Store(self) -> Vector_Storage:
        """
        Gets the assistant's vector store.
        
        Parameters
            None
            
        Returns
            vector_store (Vector_Storage): The assistant's vector store
        """

        # Return the vector store
        return self.vector_store 
    # Function End
# Assistant Class End

"""
Event Handler
"""

# Assistant Event Handler Class
class Assistant_Event_Handler(AssistantEventHandler):
    """
    A class that handles streaming actions taken by the assistant.

    Properties
        client (OpenAI)

    Overridden Methods
        on_event(event: AssistantStreamEvent)
        on_text_created(text: Text)
        on_text_delta(delta: TextDelta, snapshot: Text)
        on_text_done(text: Text)
        on_message_done(message: Message)

    Methods
        Handle_Required_Actions(data: Run, run_id: str) -> None
        Submit_Tool_Outputs(tool_outputs: list[dict], run_id: str) -> None
    """
    
    @override
    def __init__(self, client:OpenAI) -> None:
        super().__init__()
        self.client = client
    # Function End    

    # \/ \/ Event Handlers \/ \/
    @override
    def on_event(self, event:AssistantStreamEvent) -> None:
        # Identify user function calls
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id
            self.Handle_Required_Actions(event.data, run_id)
    # Function End

    # \/ \/ Text Generation \/ \/
    @override
    def on_text_created(self, text: Text) -> None:
        print(f"\n", end="", flush=True)
    # Function End    

    @override
    def on_text_delta(self, delta: TextDelta, snapshot: Text) -> None:
        print(delta.value, end="", flush=True)
    # Function End    

    @override   
    def on_text_done(self, text: Text) -> None:
        print("", end="\n", flush=True)
    # Function End    

    # \/ \/ Tool Handling \/ \/
    def Handle_Required_Actions(self, data: Run, run_id: str) -> None:
        """
        Left Empty for users to override with their custom actions.
        """
        return None
    # Function End

    @override
    def on_tool_call_created(self, tool_call: ToolCall) -> None:
        super().on_tool_call_created(tool_call)

    @override
    def on_tool_call_delta(self, delta: ToolCallDelta, snapshot: ToolCall) -> None:
        super().on_tool_call_delta(delta, snapshot)
    
    def Submit_Tool_Outputs(self, tool_outputs: list[dict], run_id: str) -> None:
        """
        [DO NOT OVERRIDE]

        Submits tool outputs to the assistant.
        Pass in a list of tool outputs to submit them to the assistant.

        Parameters
            tool_outputs (list[dict]): A list of tool output dictionaries
            run_id (str): The ID of the run to submit the tool outputs to

        Returns
            None
        """

        with self.client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            event_handler=self.__class__(client=self.client)
        ) as stream:
            stream.until_done()
    # Function End

    # \/ \/ Message Handling \/ \/
    @override
    def on_message_done(self, message: Message) -> None:
        # print a citation to any files searched
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f"[{index}]"
            )
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = self.client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")

        if (len(citations) > 0):
            print(f"{''.join(citations)}", end="\n", flush=True)
    # Function End    
# Event Handler Class End