from langchain_core.prompts.chat import ChatPromptTemplate
from utils.datetime import async_now

async def get_runnable(llm, tools, agent_prompt):
    # Mendapatkan tanggal dan waktu saat ini
    now = await async_now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    # Menyisipkan tanggal dan waktu saat ini ke dalam prompt agen
    agent_prompt = f"{agent_prompt}\n\nTanggal saat ini: {current_date}\nWaktu saat ini: {current_time}"

    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
            "system",
            agent_prompt + "\n\nUSER CONTEXT: {user_context}"
            ),
            ("placeholder", "{messages}"),
        ]
    )

    agent_runnable = prompt_template | llm.bind_tools(tools)
    return agent_runnable


