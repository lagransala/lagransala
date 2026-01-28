from groq import AsyncGroq, Groq
from groq.types.chat import ChatCompletion
from groq.types.chat.chat_completion import Choice
from langfuse import get_client, observe
from loguru import logger

from lagransala.shared.application import cached
from lagransala.shared.infrastructure.file_cache_backend import FileCacheBackend

langfuse = get_client()


# Function to handle Groq chat completion calls, wrapped with @observe to log the LLM interaction
@cached(
    FileCacheBackend(ChatCompletion, ".cache/groq_chat_completion"),
    key_params=["messages", "model"],
)
@observe(as_type="generation")
async def groq_chat_completion(client: AsyncGroq, **kwargs) -> ChatCompletion:
    # Clone kwargs to avoid modifying the original input
    kwargs_clone = kwargs.copy()

    # Extract relevant parameters from kwargs
    messages = kwargs_clone.pop("messages", None)
    model = kwargs_clone.pop("model", None)
    temperature = kwargs_clone.pop("temperature", None)
    max_tokens = kwargs_clone.pop("max_tokens", None)
    top_p = kwargs_clone.pop("top_p", None)

    # Filter and prepare model parameters for logging
    model_parameters = {
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }
    model_parameters = {k: v for k, v in model_parameters.items() if v is not None}

    # Log the input and model parameters before calling the LLM
    langfuse.update_current_generation(
        input=messages,
        model=model,
        model_parameters=model_parameters,
        metadata=kwargs_clone,
    )

    # Call the Groq model to generate a response
    logger.debug(f"Calling Groq model {model}")
    response: ChatCompletion = await client.chat.completions.create(**kwargs)
    logger.debug(f"Received response from Groq model {model}")

    # Log the usage details and output content after the LLM call
    choice = response.choices[0]
    langfuse.update_current_generation(
        usage_details={
            "input": len(str(messages)),
            "output": len(choice.message.content if choice.message.content else ""),
        },
        output=choice.message.content,
    )

    # Return the model's response object
    return response
