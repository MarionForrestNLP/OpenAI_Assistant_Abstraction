from openai import OpenAI
from openai import AssistantEventHandler
from openai.types.beta import Assistant, AssistantDeleted
from openai.types.beta import Thread, ThreadDeleted
from openai.types.beta.threads import Message

from enum import Enum
from typing_extensions import override

class LanguageModel(Enum):
    GPT_3_5_TURBO: str  = "gpt-3.5-turbo-0125"
    GPT_4O_MINI: str = "gpt-4o-mini"

class Stream_Handler(AssistantEventHandler):
    def __init__(self, assistantName: str):
        super().__init__()
        self.assistantName = assistantName

    @override
    def on_text_created(self, text):
        print(f"{self.assistantName} > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

class Assistant_V2:
    def __init__(
        self, 
        client: OpenAI,
        id: str | None = None,
        name: str | None = 'Assistant',
        instructionPrompt: str | None = 'You are a simple chat bot.',
        languageModel: LanguageModel | None = LanguageModel.GPT_3_5_TURBO,
    ):
        # Set user defined attributes
        self.client = client
        self.ID = id
        self.name = name
        self.instructionPrompt = instructionPrompt
        self.languageModel = languageModel

        # Set default attributes
        self.threads: dict[str, str] = {}
        self.streamHandler: Stream_Handler = Stream_Handler(self.name)

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
        if self.ID is None:
            self.Create_Assistant()

        # Retrieve the assistant
        return self.client.beta.assistants.retrieve(
            assistant_id=self.ID
        )

    def Create_Assistant(self) -> None:

        if self.ID is not None:
            # Delete the pre-existing assistant
            self.Delete_Assistant()

        # Create a new assistant
        self.instance = self.client.beta.assistants.create(
            name=self.name,
            instructions=self.instructionPrompt,
            model=self.languageModel.value
        )

        # Set the assistant ID
        try:
            self.ID = self.instance.id

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
            assistant_id=self.ID
        )

        # Check if the assistant was successfully deleted
        if deletionResponse.deleted:

            # Set the assistant instance to None
            self.instance = None
            self.ID = None

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
                assistant_id=self.ID,
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
                assistant_id=self.ID,
                instructions=instructionPrompt
            )
            
            # Reset the assistant instruction prompt
            self.instructionPrompt = instructionPrompt
            return True

        except Exception as e:
            print(f"Failed to update assistant instruction prompt: {e}")
            return False
        
    def Update_Assistant_Language_Model(self, languageModel: LanguageModel) -> bool:

        try:
            # Update the assistant
            self.instance = self.client.beta.assistants.update(
                assistant_id=self.ID,
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

    def Create_Thread(self, threadName: str) -> None:
        # Verify that the thread name is unique
        if threadName in self.threads:
            raise ValueError("Thread name already exists")

        try:
            # Create a new thread
            newThread: Thread = self.client.beta.threads.create()

            # Add the new thread to the threads dictionary
            self.threads[threadName] = newThread.id

        except Exception as e:
            print(f"Failed to create thread: {e}")
            raise e
        
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
            print(f"Failed to retrieve thread: {e}")
            raise e
        
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

    def Update_Thread_Tools(self, threadName: str, newThreadTools: list) -> bool:
        raise NotImplementedError

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
            assistant_id=self.ID            
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
    
    def Stream_Response(self, threadName: str) -> None:

        # Verify that the thread exists
        self._Verify_Thread_Name(threadName)

        # Create a stream
        with self.client.beta.threads.runs.stream(
            thread_id=self.threads[threadName],
            assistant_id=self.ID,
            event_handler=self.streamHandler
        ) as stream:
            stream.until_done()