import asyncio
import openai


# Method to initiate the chatBot task
async def chat_bot(ctx, *, query, OPENAI_API_KEY):
    # Create a background task to handle the chatbot interaction
    asyncio.create_task(background_task(ctx, query, OPENAI_API_KEY))


# Background task to handle the chatbot interaction
async def background_task(ctx, query, OPENAI_API_KEY):
    # Get the answer from the chatbot
    answer = await chat_OpenAI(query, OPENAI_API_KEY)
    # Reply with the answer
    await ctx.reply(answer)


# Method to interact with the OpenAI chatbot
async def chat_OpenAI(query, OPENAI_API_KEY):
    try:
        # Set the OpenAI API key
        openai.api_key = OPENAI_API_KEY
        # Use asyncio.to_thread to offload the OpenAI API call to a separate thread
        response = await asyncio.to_thread(openai.Completion.create,
                                           engine="davinci",
                                           prompt=f"Q: {query}\nA:",
                                           temperature=0.5,
                                           max_tokens=100,
                                           n=1,
                                           stop=["\nQ:"]
                                           )
        # Process the response from the chatbot
        if response and response.choices and response.choices[0].text:
            answer = response.choices[0].text.strip()
            if len(response) > 2000:
                response = response[:2000]
            return answer
        else:
            return "Sorry, I couldn't generate a response. Please try again later."
    except Exception as error:
        raise error


# Background task to keep the OpenAI API connection alive
async def keep_openai_alive(OPENAI_API_KEY):
    while True:
        try:
            # Set the OpenAI API key
            openai.api_key = OPENAI_API_KEY
            # Perform a ping-pong test to check the API connection
            response = openai.Completion.create(
                engine="davinci",
                prompt="ping",
                max_tokens=1,
                n=1,
                stop=None,
                temperature=0.5
            )
            if response.choices[0].text.strip() == "pong":
                print("OpenAI API connection is live!")
        except Exception as error:
            print(f"OpenAI API connection failed with error: {str(error)}")
        # Sleep for 5 minutes before the next ping-pong test
        await asyncio.sleep(300)
