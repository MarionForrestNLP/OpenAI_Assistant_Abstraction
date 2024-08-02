# Import the Assistant Class and relevant libraries
import Assistant # or you can use: from Assistant import Assistant
import json

from openai import OpenAI
from typing_extensions import override

# This function will be used for demostration purposes.
def Get_Current_Temperature(notation:str) -> str:
    return "72 Degrees " + notation

# Create the main function
def Main():
    # Create an OpenAI client
    client = OpenAI(
        api_key="YOUR_OPENAI_API_KEY_HERE",
    )

    print("Creating assistant...") # Create an instance of the Assistant class
    asssistant = Assistant.Assistant(
        # Pass in the OpenAI client || REQUIRED
        client=client,

        # Pass in an ID to retrieve a pre-existing assistant instance || OPTIONAL
        assistant_id=None,
        
        # Pass in a name for the assistant || REQUIRED
        assistant_name="Example Assistant",
        
        # Pass in an instruction prompt || REQUIRED
        instruction_prompt="You are a simple chat bot",
        
        # Pass in a list of tools. If left empty, the "file_search" tool is automatically added || OPTIONAL
        # The following is an example of how to add a user defined function to the tool set. Review the README for more information.
        tool_set=[
            {
                "type": "function",
                "function": {
                    "name": "Get_Current_Temperature",
                    "description": "This function returns the current temperature in the given notation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "notation": {
                                "type": "string",
                                "enum": ["Celsius", "Fahrenheit"],
                                "description": "The temperature unit to use. Ask the user to provide the notation."
                            }
                        },
                        "required": ["notation"]                    
                    }
                }
            }
        ],
        
        # Pass in the model name. If left empty, defaults to "gpt-3.5-turbo-0125" || OPTIONAL
        model=None,
        
        # Pass in a dictionary of model parameters. If left empty, default parameters of {temperature: 1.0, top_p: 1.0} will be used || OPTIONAL
        model_parameters={},
        
        # Pass in the maximum number of prompt and completion tokens this assistant can use. If left empty, 10,000 will be used. OpenAI recommends 20,000 || OPTIONAL
        max_prompt_tokens=None,
        max_completion_tokens=None
    )

    print("Attaching files...") # Attach a file to the assistant. This is an optional example, you can delete this line of code if you want.
    asssistant.Attach_Files(
        # Pass in a list of file paths || REQUIRED
        file_paths=[]
    )

    # Create a custom event handler to extend the functionality of your Assistant.
    class Custom_Event_Handler(Assistant.Assistant_Event_Handler):
        # Override text functions to stream the assistant's response to your liking. This is an optional example, you can delete this code block if you want.
        @override
        def on_text_created(self, text: Assistant.Text) -> None:
            print(f"\n{asssistant.name}: ", end="", flush=True)

        # Override the handle required actions function to add your own custom actions.
        @override
        def Handle_Required_Actions(self, data: Assistant.Run, run_id: str) -> None:
            """
            Use the following function to add your own custom actions.
            Review the "user defined functions" section of the README for more information.
            """

            toolOutputs = []

            for tool in data.required_action.submit_tool_outputs.tool_calls:
                if tool.function.name == "Get_Current_Temperature":
                    argumentDictionary = json.loads(tool.function.arguments)

                    toolOutputs.append({
                        "tool_call_id": tool.id, "output": Get_Current_Temperature(
                            notation=argumentDictionary["notation"]
                        )
                    })
            # Loop End

            self.Submit_Tool_Outputs(tool_outputs=toolOutputs, run_id=run_id)
        # Function End
    # Class End

    # Conversate with the assistant
    while True:
        # Take in user input
        user_input = input("\nUser: ")

        # Escape clause
        if user_input == "exit":
            break
        else:
            # Send the user input to the assistant
            asssistant.Send_Message(
                # Pass in a string representing the message's content || REQUIRED
                message_content=user_input,

                # Attach a file by passing the path of the file as a string || OPTIONAL
                attachment_path=None,

                # Attach a file by passing the file ID as a string || OPTIONAL
                attachment_file_id=None
            )

        # Stream the assistant's response
        asssistant.Get_Response(
            # Pass in a custom event handler || OPTIONAL
            event_handler=Custom_Event_Handler
        )
    # Loop End

    print("Closing connection to assistant...") # Delete the assistant once all activities have been completed
    asssistant.Delete_Assistant(
        clear_vector_store=True # I recommend setting this parameter to True to save on storage costs
    )
# Main End

# Run the main function
if __name__ == "__main__":
    Main()
