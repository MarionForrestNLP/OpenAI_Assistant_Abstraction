# Error Codes

## Threads | Code 10X

```json
{
    100: {
        "message": "Thread already exists",
        "details": "The thread name provided already exists. Please try again with a different name."
    },

    101: {
        "message": "Failed to create thread",
        "details": "The OpenAI client failed to create the thread. Verify your OpenAI client and try again."
    },

    102: {
        "message": "Failed to retrieve thread",
        "details": "The OpenAI client failed to retrieve the thread with the provided id. Verify your OpenAI client and/or thread id and try again."
    }
}
```