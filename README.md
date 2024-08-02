# **OpenAI Assistant Abstraction**

## Goal

This project was initialized to make the [OpenAI](https://platform.openai.com/docs/api-reference/introduction) API easier to integrate into your own projects. With an emphasis on abstracting the [assistants api](https://platform.openai.com/docs/api-reference/assistants).

## Table of Contents

- [Assistant Class](#assistant-class)
- [Vector Store Class](#vector-store-class)
- [User Defined Functions](#user-defined-functions)

## Assistant Class

This class is designed to abstract interactions with the OpenAI [Assistant](https://platform.openai.com/docs/assistants/overview/agents). This implementation of the OpenAI Assistant comes with the [File Search](https://platform.openai.com/docs/assistants/tools/file-search/file-search-beta) tool built in and the [Function Calling](https://platform.openai.com/docs/assistants/tools/function-calling/function-calling-beta) and [Code Interpreter](https://platform.openai.com/docs/assistants/tools/code-interpreter/code-interpreter-beta) tools can be added add the developer's discretion.

*Note*: The code interpreter tool comes at an additional cost, so be sure to check the its [cost](https://platform.openai.com/docs/assistants/tools/code-interpreter/how-it-works) and verify the code interpeter's usage aligns with your implementation and spending goals before adding it to your assistant.

### Assistant Properties

- **Client**: The OpenAI connection intance used to access the assistant and other APIs.
- **ID**: The ID of the assistant instance.
- **Name**: The name of the assistant as is displayed on OpenAI assistants dashboard.
- **Instructions**: The context prompt used to set up the assistant's initial behavior. Be concise and clear in your instructions to the assistant. This prompt is included in the **prompt tokens** count, thus it is recommended you keep it as short as possible.
- **Tool Set**: The list of tools used by the assistant. file search, code interpreter, and function calling.
- **Model**: The OpenAI AI model utilized by the assistant. gpt4, 3.5, etc.
- **Model Parameters**: The dictionary containing the assistant's model response parameters. Currently includes temperature and top P.
- **Max Prompt Tokens**: The maximum number of tokens allowed in a prompt by a user.
- **Max Completion Tokens**: The maximum number of tokens allowed in a response from the assistant.
- **Vector Store**: This is the internally referenced vector store used by the assistant. This is an instance of the [Vector Store class](#vector-store-class).
- **Intance**: This is the instance of the Assistant that our chat bot is tied to and actively using.
- **Thread**: This is the object in which user and assistant interactions are stored.

### Assistant Constructor

The constructor takes in an OpenAI client, the name of the assistant as a string, the instruction prompt as a string, the tool set as a list, a function dicitonary, the open ai model to implement as a string, and the model parameters as a dictionary. It then creates an assistant object using the OpenAI client and stores it in the instance property. The function dictionary is optional and will default to an empty dicitonary. The model string is optional and will default to `"gpt-3.5-turbo-0125"`. The model parameter dictionary is optional and will default to the following.

    model_parameters = {
        "temperature": 1.0,
        "top_p": 1.0
    }

The max prompt tokens and max completion tokens parameters are bot integers and will both be set to 10,000 by default. OpenAI recommends using 20,000 tokens.

#### Assistant Retrieval

The constructor also takes an optional `assistant_id` parameter. If an string is provided, the constructor will retrieve a preexisting assistant instance with the provided id from OpenAI and store it in the instance property. When an `assistant_id` is given, the remaining parameters are used to modify the retrieved assistant instance.

### Assistant Methods

- **Attach File**: Takes in a list of file path strings and passes the repective file paths to the [attach new file](#vector-store-methods) method of the assistant's internal [vector store](#vector-store-class). Returns False if any of the files were not added successfully or if no file paths were provided.

- **Delete Assistant**: This method deletes the assistant instance. It gets the assistant ID, [deletes the assistant](https://platform.openai.com/docs/api-reference/assistants/deleteAssistant) using the OpenAI client, and then updates the assistant instance property to None. The method returns a boolean indicating whether the deletion was successful or not.

- **Get Attributes**: This method returns a dictionary containing the assistant's attributes. The dictionary contains the assistant's ID, creation time (*in seconds*), name, instructions, tool set, user defined functions, model, model parameters, vector store, and thread id.

- **Get Response**: This method takes in an [Assistant Event Handler](#assistant-event-handler) object and streams the assistant's response. By default it will stream the assistant's response to the console, but you can override the [methods](#assistant-event-handler-methods) to stream to response to your liking.

- **Get Vector Store**: This method returns the assistant's internal [vector store](#vector-store-class).

- **Send Message**: This method creates a [message object](https://platform.openai.com/docs/api-reference/messages/object) and inserts it into the assistant's thread. The message object is then returned. Files paths and [file ids](https://platform.openai.com/docs/api-reference/files/object#files/object-id) can be passed to this method to attach files to the message for the assistant to use as additional context.

- **Update Tool Set**: This method updates the tool set used by the assistant. It takes a list of tool dictionaries. It updates the assistant instance and tool set. The method returns a boolean indicating whether the update was successful or not.

## Assistant Event Handler

This class is designed to make streaming possible for this implementation of the OpenAI assistant. It is used to handle the events that are streamed from the assistant.

### Assistant Event Handler Properties

- **Client**: The OpenAI connection intance used to access the assistant and other APIs.

### Assistant Event Handler Constructor

The constructor takes in the OpenAI client and creates an assistant event handler object using the OpenAI client.

### Assistant Event Handler Methods

- **On Event**: Callback that is fired for every Server-Sent-Event
- **On Text Created**: Callback that is fired when a new text content block is created
- **On Text Delta**: Callback that is fired when a text content block is updated
- **On Text Done**: Callback that is fired when a text content block is completed
- **On Message Done**: Callback that is fired when a message is completed
- **Handle Required Actions**: See [User Defined Functions](#user-defined-functions) for more information.
- **Submit Tool Outputs**: This method submits a list of tool output dictionaries to the assistant.

## Vector Store Class

This class is designed to abstract and simplify interactions with vector stores. The main goal of this class was to remove reducancies within the assistant class.

### Vector Store Properties

- **Client**: The Open AI client used to access the vector store and other APIs.
- **Name**: A string representing the name of the vector store.
- **Days Until Expiration**: An integer representing the number of 24 hour days until the vector store expires.
- **Instance**: The vector store object being abstracted.

### Vector Store Constructor

The constructor takes in the OpenAI client, the name of the vector store, and the number of days until the vector store expires. It then creates a vector store object using the OpenAI client and stores it in the instance property. The name and days until expiration properties are optional and will default to `"Vector_Storage"` and `1` respectively.

### Vector Store Methods

- **Attach Existing File**: This method attaches an existing file to the vector store. It takes in the ID of the file you want to attach. It then creates a [vector store file object](https://platform.openai.com/docs/api-reference/vector-stores-files/file-object) using the OpenAI client to attach the file to the vector store. The method returns the status of the file attachment.

- **Attach New File**: This method attaches a new file to the vector store. It takes in the path of the file you want to attach and the purpose of the file as an optional parameter (defaults to "assistant"). It then creates a [file object](https://platform.openai.com/docs/api-reference/files/object) using the OpenAI client then passes the file's id to the `Attach_Existing_File` method to attach the file to the vector store. The method returns the status of the file attachment.
  - Valid purposes are "assistants", "vision", "fine-tuning", and "batch".

- **Delete Vector Store**: This method deletes the vector store instance. It gets the vector store ID, [deletes the vector store](https://platform.openai.com/docs/api-reference/vector-stores/delete) using the OpenAI client, and then updates the vector store instance property to None. The method returns a boolean indicating whether the deletion was successful or not.

- **Get Attributes**: This method returns a dictionary containing the vector store's attributes. The dictionary contains the vector store's ID, name, status, creation time (*in seconds*), days until expiration, file count, memory usage (*in bytes*).

- **Modify Vector Store**: This method modifies the vector store instance. It takes in string representing the new name of the vector store and an integer representing the new number of days until the vector store expires. It then updates the vector store instance property with the new name and days until expiration. The method returns the modified instance.

- **Retrieve Vector Store**: This method allows you to replace the vector store created at initialization with a pre-existing vector store. It takes in the ID  of the vector store you want to retrieve. This method deletes the old instance of the the vector store and returns the retrieved instance.

## User Defined Functions

The OpenAI assistant supports user defined [function calling](https://platform.openai.com/docs/assistants/tools/function-calling/function-calling-beta), which allows you to describe functions to the assistant and have it intelligently call the functions. For this integration of the assistant, there are two steps required to get the assistant to effectively utilize your functions.

### Step 1: Tool Set Definition

Within the [tool_set](#assistant-properties) list, you must define and describe your function. This definition is [passed to the assistant](https://platform.openai.com/docs/assistants/tools/function-calling/step-1-define-functions) for it to identify when certain functions should be called. It is recommended to be as detailed as possible in the `description` fields. Include when the function should be called, what the function returns, how to use the return, and what to do when the assistant doesn't know all the required parameters.

#### Tool Set Example

```json
[
    {
        "type": "function",
        "function": {
            "name": "Get_Current_Temperature",
            "description": "This function returns a string representing the current temperature in the given notation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "notation": {
                        "type": "string",
                        "enum": ["Celsius", "Fahrenheit"],
                        "description": "The temperature unit to use. If the user does not provide a unit, default to Celsius."

                    }
                },
                "required": ["notation"]
            }
        }
    },
]
```

### Step 2: Add the Function to the Event Handler

Override the `Handle_Required_Actions` method in the [Assistant Event Handler](#assistant-event-handler-methods) class and add the following code block:

```python
@override
def Handle_Required_Actions(self, data: Assistant.Run, run_id: str) -> None:
    toolOutputs = []

    for tool in data.required_action.submit_tool_outputs.tool_calls:
        ...

    self.Submit_Tool_Outputs(tool_outputs=toolOutputs, run_id=run_id)
```

Within the for loop add if/else statements to check for the function name and call the function accordingly by inserting the following code.

```python
@override
def Handle_Required_Actions(self, data: Assistant.Run, run_id: str) -> None:
    toolOutputs = []

    for tool in data.required_action.submit_tool_outputs.tool_calls:
        if tool.function.name == "Get_Current_Temperature":
            toolOutputs.append({
                "tool_id": tool.tool_id,
                "output": Get_Current_Temperature(<ARGUMENTS>)
            })
        elif ... :
            ...

    self.Submit_Tool_Outputs(tool_outputs=toolOutputs, run_id=run_id)
```

You can get a dicitonary of the `<ARGUMENTS>` for your function by calling `json.loads` on `tool.function.arguments`. From here you can access the arguments by their paramter names.

```Python
@override
def Handle_Required_Actions(self, data: Assistant.Run, run_id: str) -> None:
    toolOutputs = []

    for tool in data.required_action.submit_tool_outputs.tool_calls:
        if tool.function.name == "Get_Current_Temperature":
            argumentDictionary = json.loads(tool.function.arguments)

            toolOutputs.append({
                "tool_call_id": tool.id, "output": Get_Current_Temperature(
                    notation=argumentDictionary["notation"]
                )
            })
        elif ... :
            ...

    self.Submit_Tool_Outputs(tool_outputs=toolOutputs, run_id=run_id)
```

Your assistant will now be able to call your newly added function. For a live demostration of this functionality run the `Example_Implementation.py` file.
