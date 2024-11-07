from openai import OpenAI
from openai import AssistantEventHandler
from openai.types.beta import Assistant, AssistantDeleted
from openai.types.beta import Thread, ThreadDeleted
from openai.types.beta import VectorStore, VectorStoreDeleted
from openai.types.beta.vector_stores import VectorStoreFile, VectorStoreFileDeleted
from openai.types.beta.threads import Message, Run

from enum import Enum
from typing_extensions import override
from os import path

class Assistant_Error(Exception):
    """
    Exception class for assistant errors.
    """

    def __init__(self, message: str, code: int = 0):
        """
        An error that occurs during an assistant's processes.

        Parameters:
            message (str): The error message.
            code (int): The error code.
        """

        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        return f"(Code: {self.code}) {self.message}"

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
    def on_exception(self, exception) -> None:
        print(f"|| Stream failed to complete: {exception} ||", flush=True)
        raise Assistant_Error(
            message=f"Stream failed to complete. {exception}",
            code=303
        )
    
    @override
    def on_event(self, event):
        """
        **[ DO NOT OVERRIDE ]**
        """
        if event.event == 'thread.run.requires_action':
            self.Handle_Required_Actions(data=event.data)

    def Handle_Required_Actions(self, data: Run) -> None:
        return None

    def _Submit_Tool_Outputs(self, toolOutputs: list[dict]) -> None:
        """
        **[ DO NOT OVERRIDE ]**
        """
        with self.client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=toolOutputs,
            event_handler=Stream_Handler(
                client=self.client,
                assistantName=self.assistantName
            )
        ) as stream:
            for text in stream.text_deltas:
                print(text, end="", flush=True)
            print()

    @override
    def on_text_created(self, text) -> None:
        print(f"{self.assistantName} > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot) -> None:
        print(delta.value, end="", flush=True)

    @override
    def on_text_done(self, text) -> None:
        return super().on_text_done(text)
    
    @override
    def on_tool_call_created(self, tool_call) -> None:
        print(f"\n{self.assistantName} > Using the {tool_call.type.replace('_', ' ')} tool.", flush=True)

    @override
    def on_message_done(self, message) -> None:

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
        """
        Retrieves a vector store with the given ID.
        If an ID was not provided, this method creates a new vector store and assigns it to the instance.

        Returns:
            VectorStore: The retrieved vector store

        Raises:
            Assistant_Error: If the vector store could not be retrieved
        """
        
        # Create a new vector store if an ID was not provided
        if self.id is None:
            return self.Create_Vector_Store()

        try:
            # Retrieve the vector store
            return self.client.beta.vector_stores.retrieve(vector_store_id=self.id)
        
        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to retrieve vector store: {e}",
                code=400
            )
    
    def Create_Vector_Store(self) -> VectorStore:
        """
        Creates a new vector store and assigns it to the instance.
        
        Returns:
            VectorStore: The created vector store

        Raises:
            Assistant_Error: If the vector store could not be created
        """

        try:
            # Create the vector store
            return self.client.beta.vector_stores.create(
                name=self.name,
                expires_after={
                    "anchor": "last_active_at",
                    "days": self.lifeTime
                }
            )
        
        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to create vector store: {e}",
                code=401
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

    def Add_File_By_Id(self, fileName: str, fileID: str) -> None:
        raise NotImplementedError

    def Add_File_By_Path(self, fileName: str, filePath: str) -> None:
        """
        Adds a file to the vector store by path.

        Parameters:
            fileName (str): The name of the file to add.
            filePath (str): The path of the file to add.

        Raises:
            FileNotFoundError: If the file path does not exist
            Assistant_Error: If the file could not be added to the vector store
        """

        # Check if the file exists
        if path.exists(filePath) == False:
            raise FileNotFoundError("File not found")
        
        try:
            try:
                # Open the file into a file stream
                fileStream = open(filePath, "rb")
            
            except Exception as e:
                raise Assistant_Error(
                    message=f"Failed to open file: {e}",
                    code=403
                )

            # Upload and poll the file
            vsFile: VectorStoreFile = self.client.beta.vector_stores.files.upload_and_poll(
                vector_store_id=self.id,
                file=fileStream
            )

            # Add the file to the files dictionary
            self.files[fileName] = vsFile.id

            return True

        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to upload file: {e}",
                code=402
            )

    def _Delete_File_By_Id(self, fileID: str) -> bool:
        """
        Deletes a file from the vector store by its ID.
        This method does not delete the reference to the file's name in the files dictionary.

        Parameters:
            fileID (str): The ID of the file to delete.

        Returns:
            bool: True if the file was deleted, False otherwise.

        Raises:
            Assistant_Error: If the file could not be deleted.
        """

        try:
            # Delete the file
            deletionResponse: VectorStoreFileDeleted = self.client.files.delete(
                file_id=fileID
            )

            if deletionResponse.deleted:
                return True
            
            return False

        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to delete file: {e}",
                code=404
            )

    def Delete_File_By_Name(self, fileName: str) -> bool:
        """
        Deletes a file from the vector store by its name.

        Parameters:
            fileName (str): The name of the file to delete.

        Returns:
            bool: True if the file was successfully deleted or if no files exist, False otherwise.

        Raises:
            Assistant_Error: If the file could not be found or deleted.
        """

        # Check if there are any files
        if self.files == {}:
            return True

        try:
            fileID: str = self.files[fileName]

        except KeyError:
            raise KeyError("File name does not exist")
        
        finally:
            if self._Delete_File_By_Id(fileID):
                del self.files[fileName]
                return True
        
    def Delete_All_Files(self) -> bool:
        # Get file names
        fileNames: list[str] = list(self.files.keys())

        # Check if there are any files
        if len(fileNames) == 0:
            return True

        # Delete all files
        for fileName in fileNames:
            self.Delete_File_By_Name(fileName)

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

    def _Verify_Existing_Thread_Name(self, threadName: str) -> bool:
        """
        Verifies that the given thread name exists in the threads dictionary.

        Parameters:
            threadName (str): The name of the thread to verify.

        Returns:
            bool: True if the thread name exists.

        Raises:
            Assistant_Error: If the thread name does not exist.
        """
        if threadName not in self.threads:
            raise Assistant_Error(
                message=f"No thread with alias: {threadName}",
                code=103
            )
        return True
    
    def _Verify_Unique_Thread_Name(self, threadName: str) -> bool:
        """
        Verifies that the given thread name does not already exist in the threads dictionary.

        Parameters:
            threadName (str): The name of the thread to verify.

        Returns:
            bool: True if the thread name does not already exist, False otherwise.

        Raises:
            Assistant_Error: If the thread name already exists.
        """
        
        if threadName in self.threads:
            raise Assistant_Error(
                message=f"Thread name '{threadName}' already exists.",
                code=100
            )
        return True

    # # # #
    # 
    # Assistant Creation and Deletion Methods 
    #
    # # # #

    def Retrieve_Assistant(self) -> Assistant:
        """
        Retrieves an assistant instance from OpenAI.
        If the assistant ID is None, it will create a new assistant first.

        Returns:
            Assistant: The retrieved assistant instance.

        Raises:
            Assistant_Error: If the assistant ID is None and the Create_Assistant method fails.
            Assistant_Error: If the retrieval request fails.
        """
        
        # Create a new assistant if an ID was not provided
        if self.id is None:
            self.Create_Assistant()

        # Retrieve the assistant
        try:
            return self.client.beta.assistants.retrieve(
                assistant_id=self.id
            )
        
        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to retrieve assistant: {e}",
                code=205
            )

    def Create_Assistant(self) -> None:
        """
        Creates a new assistant instance.
        If an existing assistant ID is present, the existing assistant is deleted before creating a new one.

        Raises:
            Assistant_Error: If there is an error during the assistant creation.
        """

        # Check if there is an existing assistant
        if self.id is not None:
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
        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to create assistant: {e}",
                code=204
            )
        
    def Delete_Assistant(self) -> bool:
        """
        Deletes the assistant. Call this method once you are done using the assistant.

        Returns:
            bool: True if the assistant is successfully deleted.

        Raises:
            Assistant_Error: If the assistant could not be deleted.
        """
        
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
        
        raise Assistant_Error(
            message="Failed to delete assistant.",
            code=203
        )
    
    # # # #
    # 
    # Assistant Parameter Modification Methods 
    #
    # # # # 

    def Update_Assistant_Name(self, name: str) -> bool:
        """
        Updates the name of the assistant.

        Parameters:
            name (str): The new name of the assistant.

        Returns:
            bool: True if the assistant was successfully updated, False if not.
        
        Raises:
            Assistant_Error: If the assistant could not be updated.
        """

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
            raise Assistant_Error(
                message=f"Failed to update assistant: {e}",
                code=200
            )
        
    def Update_Assistant_Instruction_Prompt(self, instructionPrompt: str) -> bool:
        """
        Updates the instruction prompt of the assistant.

        Parameters:
            instructionPrompt (str): The new instruction prompt of the assistant.

        Returns:
            bool: True if the assistant was successfully updated, False if not.
        
        Raises:
            Assistant_Error: If the assistant could not be updated.
        """
        
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
            raise Assistant_Error(
                message=f"Failed to update assistant: {e}",
                code=201
            )
        
    def Update_Assistant_Language_Model(self, languageModel: Language_Model) -> bool:

        """
        Updates the language model of the assistant.

        Parameters:
            languageModel (Language_Model): The new language model of the assistant.

        Returns:
            bool: True if the assistant was successfully updated, False if not.
        
        Raises:
            Assistant_Error: If the assistant could not be updated.
        """

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
            raise Assistant_Error(
                message=f"Failed to update assistant: {e}",
                code=202
            )
        
    def Update_Assistant_Tools(self, tools: list[dict[str, any]]) -> bool:

        # Maintain the file search tool
        tools.append({"type": "file_search"})

        try:
            # Update the assistant
            self.instance = self.client.beta.assistants.update(
                assistant_id=self.id,
                tools=tools
            )
            
            # Reset the assistant tools
            self.tools = tools
            return True

        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to update assistant: {e}",
                code=206
            )

    # # # #
    # 
    # Assistant Thread Handling Methods 
    #
    # # # # 

    def Create_Thread(self, threadName: str) -> str:
        """
        Creates a new thread with the given name.

        Parameters:
            threadName (str): The name of the thread to create.

        Returns:
            str: The ID of the created thread.

        Raises:
            Thread_Error: If the thread name already exists or if the thread could not be created.
        """

        # Verify that the thread name is unique
        self._Verify_Unique_Thread_Name(threadName)
        
        # Variable initialization
        threadInstance: Thread = None

        # Create a new thread
        threadInstance = self.client.beta.threads.create()

        # Exception handling
        if threadInstance is None:
            raise Assistant_Error(
                message="Failed to create thread.",
                code=101
            )

        # Add the thread to the threads dictionary
        self.threads[threadName] = threadInstance.id

        # Return the thread ID
        return threadInstance.id
    
    def Delete_Thread_By_Id(self, threadID: str) -> bool:
        raise NotImplementedError
        
    def Delete_Thread_By_Name(self, threadName: str) -> bool:
        """
        Deletes a thread with the given name.

        Parameters:
            threadName (str): The name of the thread to delete.

        Returns:
            bool: True if the thread was successfully deleted, False otherwise.

        Raises:
            Thread_Error: If the thread name does not exist or if the thread could not be deleted.
        """

        # Verify that the thread name exists
        self._Verify_Existing_Thread_Name(threadName)

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
        
        # Raise an exception if the thread could not be deleted
        raise Assistant_Error(
            message="Failed to delete thread.",
            code=105
        )
    
    def Retrieve_Thread_By_Id(self, threadID: str) -> Thread:
        """
        Retrieves a thread by its id.

        Parameters:
            threadID (str): The ID of the thread to retrieve.

        Returns:
            Thread: The retrieved thread.

        Raises:
            Thread_Error: If the thread could not be retrieved.
        """
        
        try:
            # Retrieve the thread
            return self.client.beta.threads.retrieve(
                thread_id=threadID
            )

        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to retrieve thread. | {e}",
                code=102
            )
        
    def Retrieve_Thread_By_Name(self, threadName: str) -> Thread:
        """
        Retrieves a thread by its name.

        Parameters:
            threadName (str): The name of the thread to retrieve.

        Returns:
            Thread: The retrieved thread.

        Raises:
            Thread_Error: If the thread could not be retrieved.
        """
        
        # Verify that the thread exists
        self._Verify_Existing_Thread_Name(threadName)

        # Retrieve the thread
        return self.Retrieve_Thread_By_Id(self.threads[threadName])
        
    def Update_Thread_Name(self, threadName: str, newName: str) -> bool:
        """
        Updates the name of an existing thread.

        Parameters:
            threadName (str): The current name of the thread to update.
            newName (str): The new name to assign to the thread.

        Returns:
            bool: True if the update was successful, False otherwise.

        Raises:
            Thread_Error: If the thread name could not be updated.
        """
        
        # Verify that the thread exists
        self._Verify_Existing_Thread_Name(threadName)
        
        # Verify that the new thread name is unique
        self._Verify_Unique_Thread_Name(newName)

        try:
            # Add the new thread
            self.threads[newName] = self.threads[threadName]

            # Remove the old thread
            del self.threads[threadName]

            return True

        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to update thread name. | {e}",
                code=104
            )
        
    # # # #
    # 
    # Assistant Vector Store Methods
    #
    # # # #

    def _Link_VS_To_Thread(self, threadName: str, vectorStore: Vector_Store) -> bool:
        """
        Links a vector store to a thread.

        Parameters:
            threadName (str): The name of the thread to which the vector store should be linked.
            vectorStore (Vector_Store): The vector store to link to the thread.

        Returns:
            bool: True if the linking was successful, False otherwise.

        Raises:
            Assistant_Error: If the vector store could not be linked to the thread.
        """
        
        self._Verify_Existing_Thread_Name(threadName)

        threadId: str = self.threads[threadName]

        try:
            self.client.beta.threads.update(
                thread_id=threadId,
                tool_resources={"file_search":{
                    "vector_store_ids":[vectorStore.id]
                }}
            )

            return True

        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to link vector store to thread. | {e}",
                code=407
            )
    
    def _Link_VS_To_Assistant(self, vectorStore: Vector_Store) -> bool:
        """
        Links a vector store to an assistant.

        Parameters:
            vectorStore (Vector_Store): The vector store to link to the assistant.

        Returns:
            bool: True if the linking was successful, False otherwise.

        Raises:
            Assistant_Error: If the vector store could not be linked to the assistant.
        """
        
        try:
            self.instance = self.client.beta.assistants.update(
                assistant_id=self.id,
                tool_resources={"file_search":{
                    "vector_store_ids":[vectorStore.id]
                }}
            )

            return True

        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to link vector store to assistant. | {e}",
                code=406
            )

    def Link_Vector_Store(self, vectorStore: Vector_Store, threadName: str | None = None) -> bool:
        """
        Links a vector store to an assistant or a thread.

        Parameters:
            vectorStore (Vector_Store): The vector store to link to the assistant or thread.
            threadName (str | None): The name of the thread to link the vector store to. If None, the vector store is linked to the assistant.

        Returns:
            bool: True if the linking was successful, False otherwise.

        Raises:
            Assistant_Error: If the vector store could not be linked to the assistant or thread.
        """
        
        # Verify that the vector store exists
        vectorStoreID: str = vectorStore.id
        if vectorStoreID is None:
            raise Assistant_Error(
                message="Vector store does not exist.",
                code=405
            )
        
        if threadName is None:
            # Link the vector store to the assistant
            return self._Link_VS_To_Assistant(vectorStore=vectorStore)

        else:
            # Link the vector store to the thread
            return self._Link_VS_To_Thread(threadName=threadName, vectorStore=vectorStore)

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

        # Check if there are no messages
        if len(messages) == 0:
            return filteredMessages

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
        """
        This method extracts and returns a list of strings from a list of Message objects.

        Parameters:
            messages (list[Message]): A list of Message objects whose content strings are to be extracted.

        Returns:
            list[str]: A list of strings extracted from the Message objects.
        """
        
        # Variable initialization
        messageStrings: list[str] = []

        # Iterate over the messages
        for message in messages:
            # Add the message content to the message strings
            messageStrings.append(
                message.content[0].text.value
            )

        return messageStrings
    
    def _Create_Run_Instance(self, threadID: str, assistantID: str) -> Run:
        """
        Creates a new run instance in the specified thread.

        Parameters:
            threadID (str): The ID of the thread to create the run in.
            assistantID (str): The ID of the assistant to associate with the run.

        Returns:
            Run: The created run instance.

        Raises
            Assistant_Error: If the run creation fails.
        """

        try:
            return self.client.beta.threads.runs.create_and_poll(
                thread_id=threadID,
                assistant_id=assistantID
            )
        
        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to create run instance. | {e}",
                code=301
            )
    
    def Create_Message(self, threadName: str, textContent: str) -> None:
        """
        Creates a new message in the specified thread.

        Parameters:
            threadName (str): The name of the thread to which the message should be added.
            textContent (str): The content of the message to be created.

        Raises:
            Assistant_Error: If the thread does not exist or if the message could not be created.
        """
        
        # Verify that the thread exists
        self._Verify_Existing_Thread_Name(threadName)
        
        try:
            # Create a new message
            self.client.beta.threads.messages.create(
                thread_id=self.threads[threadName],
                role="user",
                content=textContent
            )
        
        except Exception as e:
            raise Assistant_Error(
                message=f"Failed to create message. | {e}",
                code=103
            )
    
    def Static_Response(self, threadName: str) -> list[str]:
        """
        This method initiates a run to process user messages and returns a list of strings
        representing the assistant's response.

        Parameters:
            threadName (str): The name of the thread to process.

        Returns:
            list[str]: The strings of the assistant's response.

        Raises:
            Assistant_Error: If the thread does not exist, or if the run failed to complete.
        """
        
        # Verify that the thread exists
        self._Verify_Existing_Thread_Name(threadName)

        # Create a run
        run: Run = self._Create_Run_Instance(
            threadID=self.threads[threadName],
            assistantID=self.id
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

        raise Assistant_Error(
            message=f"Run failed to complete. | {run.status}",
            code=302
        )
    
    def Stream_Response(self, threadName: str, streamHandler: Stream_Handler = None) -> None:
        """
        This method initiates a run to process user messages and streams the assistant's response to the console.

        Parameters:
            threadName (str): The name of the thread to process.
            streamHandler (Stream_Handler): The stream handler to use. If not provided, a default stream handler is used.

        Raises:
            Assistant_Error: If the thread does not exist, or if the run failed to complete.
        """

        # Check if a stream handler was provided
        if streamHandler is None:
            streamHandler = Stream_Handler(
                client=self.client,
                assistantName=self.name
            )

        # Verify that the thread exists
        self._Verify_Existing_Thread_Name(threadName)

        try:
            # Create a stream
            with self.client.beta.threads.runs.stream(
                thread_id=self.threads[threadName],
                assistant_id=self.id,
                event_handler=streamHandler
            ) as stream:
                stream.until_done()

        except Exception as e:
            raise Assistant_Error(
                message=f"Stream failed to complete. | {e}",
                code=303
            )