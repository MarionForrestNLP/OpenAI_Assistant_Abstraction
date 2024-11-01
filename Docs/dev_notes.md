# Developer Notes

## Planed Future Implementations

- Delete thread by ID
- Message attachments
- User defined function calling
- Adding files to vector stores using file IDs

## Error Codes

### Code 1XX - Threads

```json
{
    100: {
        "message": "Thread already exists.",
        "details": "The thread name provided already exists. Please try again with a different name."
    },

    101: {
        "message": "Failed to create thread.",
        "details": "The OpenAI client failed to create the thread. Verify your OpenAI client and try again."
    },

    102: {
        "message": "Failed to retrieve thread.",
        "details": "The OpenAI client failed to retrieve the thread with the provided id. Verify your OpenAI client and/or thread id and try again."
    },

    103: {
        "message": "No thread with alias: {threadName}.",
        "details": "The thread name provided does not correspond to an existing thread. Please try again with a different name."
    },

    104: {
        "message": "Failed to update thread name.",
        "details": "The new thread alias was unable to be saved in the threads dictionary."
    },

    105: {
        "message": "Failed to delete thread.",
        "details": "The OpenAI client failed to delete the thread. Verify your OpenAI client and try again."
    }
}
```

### Code 2XX - Assistants

```json
{
    200: {
        "message": "Failed to update assistant.",
        "details": "The OpenAI client failed to update the assistant's name. Verify your OpenAI client and try again."
    },
    
    201: {
        "message": "Failed to update assistant.",
        "details": "The OpenAI client failed to update the assistant's instruction prompt. Verify your OpenAI client and try again."
    },
    
    202: {
        "message": "Failed to update assistant.",
        "details": "The OpenAI client failed to update the assistant's language model. Verify your OpenAI client and try again."
    },

    203: {
        "message": "Failed to delete assistant.",
        "details": "The OpenAI client failed to delete the assistant. Verify your OpenAI client and try again."
    },

    204: {
        "message": "Failed to create assistant.",
        "details": "The OpenAI client failed to create the assistant. Verify your OpenAI client and try again."
    },

    205: {
        "message": "Failed to retrieve assistant.",
        "details": "The OpenAI client failed to retrieve the assistant with the provided id. Verify your OpenAI client and/or assistant id and try again."
    }
}
```

### Code 3XX - Messages, Runs, and Streams

```json
{
    300: {
        "message": "Failed to create message.",
        "details": "The OpenAI client failed to create the message. Verify your OpenAI client and/or thread id and try again."
    },

    301: {
        "message": "Failed to create run instance.",
        "details": "The OpenAI client failed to create the run instance. Verify your OpenAI client and/or thread id and/or assistant id and try again."
    },

    302: {
        "message": "Run failed to complete. | {run.status}",
        "details": "The OpenAI client failed to complete the run. Review status codes: https://platform.openai.com/docs/api-reference/run-steps/step-object#run-steps/step-object-status"
    },

    303: {
        "message": "Stream failed to complete.",
        "details": "The OpenAI client failed to stream the messages. Verify your OpenAI client and/or thread id and/or assistant id and try again. Verify you streamHandler is one was provided."
    }
}
```

### Code 4XX - Vector Stores

```json
{
    400: {
        "message": "Failed to retrieve vector store.",
        "details": "The OpenAI client failed to retrieve the vector store. Verify your OpenAI client and/or vector store id and try again."
    },

    401: {
        "message": "Failed to create vector store.",
        "details": "The OpenAI client failed to create the vector store. Verify your OpenAI client and try again."
    },

    402: {
        "message": "Failed to upload file to vector store.",
        "details": "The OpenAI client failed to upload the file to the vector store. Verify your OpenAI client and try again."
    },

    403: {
        "message": "Failed to read file.",
        "details": "The provided file could not be read to a stream. Verify your file path and try again."
    },

    404: {
        "message": "Failed to delete file.",
        "details": "The OpenAI client failed to delete the file. Verify your OpenAI client and try again."
    },

    405: {
        "message": "Vector store does not exist.",
        "details": "The vector store does not exist. Verify your vector store id and try again."
    },

    406: {
        "message": "Failed to link vector store to assistant.",
        "details": "The OpenAI client failed to link the vector store to the assistant. Verify your OpenAI client and try again."
    },

    407: {
        "message": "Failed to link vector store to thread.",
        "details": "The OpenAI client failed to link the vector store to the thread. Verify your OpenAI client and try again."
    }
}
```