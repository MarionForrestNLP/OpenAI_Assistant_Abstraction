from openai import OpenAI
from openai import AssistantEventHandler
from openai.types.beta import Assistant, AssistantDeleted
from openai.types.beta import Thread, ThreadDeleted
from openai.types.beta import VectorStore, VectorStoreDeleted
from openai.types.beta.vector_stores import VectorStoreFile, VectorStoreFileDeleted
from openai.types.beta.threads import Message

from enum import Enum
from typing_extensions import override
from os import path

class Thread_Error(Exception):
    """
    Exception class for thread errors.
    """

    def __init__(self, message: str, code: int = 0):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        return f"(Code: {self.code}) {self.message}"
    
    def Lookup_Error(self, code: int) -> str:
        """
        Lookup error message based on code.
        
        Parameters:
        ---
            code (int): The error code.
        
        Returns:
        ---
            str: The full description of the error message.
        """
        raise NotImplementedError # Ironic

class Language_Model(Enum):
    """
    Enum class for language models.
    """

    GPT_3_5_TURBO: str  = "gpt-3.5-turbo-0125"
    GPT_4O_MINI: str = "gpt-4o-mini"

class Stream_Handler(AssistantEventHandler):
    def __init__(self, client: OpenAI, assistantName: str = 'Assistant'):
        super().__init__()

        self.client = client
        self.assistantName = assistantName

    @override
    def on_exception(self, exception):
        print(f"Error occurred while streaming: {exception}")
        return super().on_exception(exception)

    @override
    def on_text_created(self, text):
        print(f"{self.assistantName} > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    @override
    def on_text_done(self, text):
        return super().on_text_done(text)
    
    @override
    def on_tool_call_created(self, tool_call):
        print(f"\n{self.assistantName} > Using the {tool_call.type.replace('_', ' ')} tool.", flush=True)

    @override
    def on_message_done(self, message):

        # Get message annotations
        content = message.content[0].text
        annotations: list = content.annotations

        # Build citations
        citations: list = []
        for index, annotation in enumerate(annotations):
            content.value = content.value.replace(
                annotation.text, f"[{index}]"
            )

            if file_citation := getattr(annotation, "file_citation", None):
                citedFile = self.client.files.retrieve(file_citation.file_id)
                citations.append(f"{citedFile.filename}")

        if (len(citations) > 0):
            print(f"\nSources: ", end="", flush=True)
            for i, x in enumerate(citations):
                print(f"[{i}] {x}, ", end="", flush=True)
            print("", end="\n", flush=True)

class Vector_Store:
    def __init__(
        self, 
        client: OpenAI, 
        id: str | None = None, 
        name: str | None = 'Vector_Store', 
        lifeTime: int | None = 1
    ):
        # User defined attributes
        self.client = client
        self.id = id
        self.name = name
        self.lifeTime = lifeTime

        # Default attributes
        self.files: dict[str, str] = {}

        # Retrieve the vector store
        self.instance = self.Retrieve_Vector_Store()
        self.id = self.instance.id

    # # # #
    # 
    # Vector Store Creation and Deletion Methods
    #
    # # # #

    def Retrieve_Vector_Store(self) -> VectorStore:
        # Create a new vector store if an ID was not provided
        if self.id is None:
            return self.Create_Vector_Store()

        # Retrieve the vector store
        return self.client.beta.vector_stores.retrieve(vector_store_id=self.id)
    
    def Create_Vector_Store(self) -> VectorStore:

        # Create the vector store
        return self.client.beta.vector_stores.create(
            name=self.name,
            expires_after={
                "anchor": "last_active_at",
                "days": self.lifeTime
            }
        )

    def Delete_Vector_Store(self, deleteFiles: bool = True) -> bool:

        # Delete attached files
        if deleteFiles:
            if not self.Delete_All_Files():
                print("Failed to delete attached files")

        # Delete the vector store
        deletionResponse: VectorStoreDeleted = self.client.beta.vector_stores.delete(
            vector_store_id=self.id
        )

        # Check if the vector store was deleted
        if deletionResponse.deleted:
            self.instance = None
            self.id = None
            return True
        else:
            return False
        
    # # # #
    # 
    # File Management Methods
    #
    # # # #

    def Add_Existing_File(self, fileName: str, fileID: str) -> None:
        raise NotImplementedError

    def Add_File_By_Path(self, fileName: str, filePath: str) -> None:
        if path.exists(filePath) == False:
            raise ValueError("File not found")

        # Open the file into a file stream
        fileStream = open(filePath, "rb")

        # Upload and poll the file
        vsFile: VectorStoreFile = self.client.beta.vector_stores.files.upload_and_poll(
            vector_store_id=self.id,
            file=fileStream
        )

        # Add the file to the files dictionary
        self.files[fileName] = vsFile.id

    def Delete_File(self, fileName: str) -> None:
        if self.files == {}:
            return None

        try:
            fileID = self.files[fileName]

            # Delete the file
            deletionResponse: VectorStoreFileDeleted = self.client.beta.vector_stores.files.delete(
                file_id=fileID,
                vector_store_id=self.id
            )

            # Remove the file from the files dictionary
            if deletionResponse.deleted:
                del self.files[fileName]
            else: 
                print(f"Failed to delete {fileName}.")

        except KeyError:
            raise ValueError("File not found")
        
    def Delete_All_Files(self) -> bool:
        # Get file names
        fileNames: list[str] = list(self.files.keys())

        # Check if there are any files
        if len(fileNames) == 0:
            return True

        # Delete all files
        for fileName in fileNames:
            self.Delete_File(fileName)

        # Check status
        if self.files == {}:
            return True
        else:
            return False

class Assistant_V2:
    def __init__(
        self, 
        client: OpenAI,
        id: str | None = None,
        name: str | None = 'Assistant',
        instructionPrompt: str | None = 'You are a simple chat bot.',
        languageModel: Language_Model | None = Language_Model.GPT_3_5_TURBO,
    ):
        # Set user defined attributes
        self.client = client
        self.id = id
        self.name = name
        self.instructionPrompt = instructionPrompt
        self.languageModel = languageModel

        # Set default attributes
        self.threads: dict[str, str] = {}
        self.tools: list[dict[str, any]] = [
            {"type": "file_search"}
        ]
        self.vectorStores: list[Vector_Store] = []

        # Retrieve the assistant
        self.instance: Assistant = self.Retrieve_Assistant()

    # # # #
    # 
    # General Maintenance Methods
    #
    # # # #

    def _Verify_Thread_Name(self, threadName: str) -> bool:
        if threadName not in self.threads:
            raise ValueError("Thread name does not exist")
        return True

    # # # #
    # 
    # Assistant Creation and Deletion Methods 
    #
    # # # #

    def Retrieve_Assistant(self) -> Assistant:
        
        # Create a new assistant if an ID was not provided
        if self.id is None:
            self.Create_Assistant()

        # Retrieve the assistant
        return self.client.beta.assistants.retrieve(
            assistant_id=self.id
        )

    def Create_Assistant(self) -> None:

        if self.id is not None:
            # Delete the pre-existing assistant
            self.Delete_Assistant()

        # Create a new assistant
        self.instance = self.client.beta.assistants.create(
            name=self.name,
            instructions=self.instructionPrompt,
            model=self.languageModel.value,
            tools=self.tools
        )

        # Set the assistant ID
        try:
            self.id = self.instance.id

        # Raise an exception if the assistant could not be created
        except Exception("Failed to create assistant") as e:
            print(f"Failed to create assistant: {e}")
            raise e
        
    def Delete_Assistant(self) -> bool:
        
        # If there is no assistant instance, return True
        if self.instance is None:
            return True
        
        # Delete the assistant
        deletionResponse: AssistantDeleted = self.client.beta.assistants.delete(
            assistant_id=self.id
        )

        # Check if the assistant was successfully deleted
        if deletionResponse.deleted:

            # Set the assistant instance to None
            self.instance = None
            self.id = None

            # Delete the threads associated with the assistant
            self.threads.clear()

            return True
        
        return False
    
    # # # #
    # 
    # Assistant Parameter Modification Methods 
    #
    # # # # 

    def Update_Assistant_Name(self, name: str) -> bool:

        try:
            # Update the assistant
            self.instance = self.client.beta.assistants.update(
                assistant_id=self.id,
                name=name
            )
            
            # Reset the assistant name
            self.name = name
            return True

        except Exception as e:
            print(f"Failed to update assistant name: {e}")
            return False
        
    def Update_Assistant_Instruction_Prompt(self, instructionPrompt: str) -> bool:

        try:
            # Update the assistant
            self.instance = self.client.beta.assistants.update(
                assistant_id=self.id,
                instructions=instructionPrompt
            )
            
            # Reset the assistant instruction prompt
            self.instructionPrompt = instructionPrompt
            return True

        except Exception as e:
            print(f"Failed to update assistant instruction prompt: {e}")
            return False
        
    def Update_Assistant_Language_Model(self, languageModel: Language_Model) -> bool:

        try:
            # Update the assistant
            self.instance = self.client.beta.assistants.update(
                assistant_id=self.id,
                model=languageModel.value
            )
            
            # Reset the assistant language model
            self.languageModel = languageModel
            return True

        except Exception as e:
            print(f"Failed to update assistant language model: {e}")
            return False

    # # # #
    # 
    # Assistant Thread Handling Methods 
    #
    # # # # 

    def Create_Thread(self, threadName: str) -> str:
        # Verify that the thread name is unique
        if threadName in self.threads:
            raise Thread_Error(
                message=f"Thread name '{threadName}' already exists.",
                code=100
            )
        
        # Variable initialization
        threadInstance: Thread = None

        # Create a new thread
        threadInstance = self.client.beta.threads.create()

        # Exception handling
        if threadInstance is None:
            raise Thread_Error(
                message="Failed to create thread.",
                code=101
            )

        # Add the thread to the threads dictionary
        self.threads[threadName] = threadInstance.id

        # Return the thread ID
        return threadInstance.id
        
    def Delete_Thread(self, threadName: str) -> bool:
        self._Verify_Thread_Name(threadName)

        # Retrieve the thread
        threadID: str = self.threads[threadName]

        # Delete the thread
        deletionResponse: ThreadDeleted = self.client.beta.threads.delete(
            thread_id=threadID
        )

        # Check if the thread was successfully deleted
        if deletionResponse.deleted:

            # Remove the thread from the threads dictionary
            del self.threads[threadName]
            return True
        
        # Return False if the thread was not successfully deleted
        return False
    
    def Retrieve_Thread(self, threadID: str) -> Thread:
        # Retrieve the thread
        try:
            return self.client.beta.threads.retrieve(
                thread_id=threadID
            )

        except Exception as e:
            raise Thread_Error(
                message=f"Failed to retrieve thread. | {e}",
                code=102
            )
        
    def Update_Thread_Name(self, threadName: str, newThreadName: str) -> bool:
        self._Verify_Thread_Name(threadName)
        
        if newThreadName in self.threads:
            raise ValueError("New thread name is not unique")

        try:
            # Update the thread
            self.threads[newThreadName] = self.threads[threadName]
            del self.threads[threadName]

            return True

        except Exception as e:
            print(f"Failed to update thread name: {e}")
            return False

    def Link_Vector_Store(self, threadName: str, vectorStore: Vector_Store) -> bool:
        # Variable Initilizaiton
        threadID: str = self.threads[threadName]
        vectorStoreID: str = vectorStore.id

        # Link the vector store
        try:
            self.client.beta.threads.update(
                thread_id=threadID,
                tool_resources={"file_search":{
                    "vector_store_ids":[vectorStoreID]
                }}
            )
        except Exception as e:
            print(f"Error occurred while linkning vector store: {e}")
            raise e

    # # # #
    # 
    # Assistant Message Handling Methods 
    #
    # # # # 
    
    def _Filter_Assistant_Response(self, messages: list[Message]) -> list[Message]:
        """
        This method filters a list of messages into a list of only messages from the
        assistant, after the user's most recent message.

        Parameters
        ----------
        messages (list[Message]): A list of messages to filter.

        Returns
        -------
        list[Message]: A list of only messages from the assistant.
        """

        # Variable initialization
        filteredMessages: list[Message] = []

        # Iterate over the messages
        for message in messages:
            # Check if the message is from the assistant
            if message.role == "assistant":
                # Add the message to the filtered messages
                filteredMessages.append(message)

            else: break

        # Return the filtered messages
        return filteredMessages
    
    def _Filter_Message_Strings(self, messages: list[Message]) -> list[str]:
        # Variable initialization
        messageStrings: list[str] = []

        # Iterate over the messages
        for message in messages:
            # Add the message content to the message strings
            messageStrings.append(
                message.content[0].text.value
            )

        return messageStrings
    
    def Create_Message(self, threadName: str, textContent: str) -> Message:
        # Verify that the thread exists
        self._Verify_Thread_Name(threadName)
        
        # Create a new message
        return self.client.beta.threads.messages.create(
            thread_id=self.threads[threadName],
            role="user",
            content=textContent
        )
    
    def Static_Response(self, threadName: str) -> list[str]:
        # Verify that the thread exists
        self._Verify_Thread_Name(threadName)

        # Create a run
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.threads[threadName],
            assistant_id=self.id            
        )

        if run.status == 'completed':
            # Retrieve the messages in the thread
            allMessages: list[Message] = self.client.beta.threads.messages.list(
                thread_id=self.threads[threadName],
            ).data

            # Filter for the assistant's response
            filteredMessages: list[Message] = self._Filter_Assistant_Response(
                messages=allMessages
            )

            # Return the strings of the assistant's response
            return self._Filter_Message_Strings(
                messages=filteredMessages
            )

        else: raise Exception("Run did not complete successfully")
    
    def Stream_Response(self, threadName: str, streamHandler: Stream_Handler = None) -> None:
        if streamHandler is None:
            streamHandler = Stream_Handler(
                client=self.client,
                assistantName=self.name
            )

        # Verify that the thread exists
        self._Verify_Thread_Name(threadName)

        # Create a stream
        with self.client.beta.threads.runs.stream(
            thread_id=self.threads[threadName],
            assistant_id=self.id,
            event_handler=streamHandler
        ) as stream:
            stream.until_done()