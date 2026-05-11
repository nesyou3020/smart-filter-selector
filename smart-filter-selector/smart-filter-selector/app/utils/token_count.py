import tiktoken


def count_tokens(text: str, model: str = "gpt-4-turbo") -> int:
    """
        Count the number of tokens in a given text using the tiktoken library.

        Args:
            text (str): The input text to count tokens for.
            model (str): The model whose tokenizer to use (default: "gpt-4-turbo").

        Returns:
            int: Number of tokens in the input text.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # fallback if model name not found
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)
    return len(tokens)
