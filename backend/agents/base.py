from agents.state import State
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import AIMessage
import logging

logger = logging.getLogger(__name__)

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable
        self.max_retries = 3  # Batasi retry untuk mencegah infinite loop

    async def __call__(self, state: State, config: RunnableConfig):
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                # Ensure user_context is passed to the runnable
                runnable_input = {
                    "messages": state.get("messages", []),
                    "user_context": state.get("user_context", {}),
                    "dialog_state": state.get("dialog_state", [])
                }

                result = await self.runnable.ainvoke(runnable_input)

                # Validasi hasil untuk memastikan tidak ada tool call yang tidak lengkap
                if hasattr(result, 'tool_calls') and result.tool_calls:
                    # Jika ada tool calls, pastikan mereka valid
                    for tool_call in result.tool_calls:
                        if not tool_call.get('id'):
                            logger.warning("Tool call tanpa ID ditemukan, akan diabaikan")
                            # Buat response tanpa tool calls untuk menghindari error
                            result = AIMessage(content="Maaf, terjadi kesalahan dalam memproses permintaan. Silakan coba lagi.")
                            break

                if not result.tool_calls and (
                    not result.content
                    or isinstance(result.content, list)
                    and not result.content[0].get("text")
                ):
                    retry_count += 1
                    if retry_count >= self.max_retries:
                        # Jika sudah mencapai max retry, berikan respons default
                        result = AIMessage(content="Maaf, saya tidak dapat memproses permintaan Anda saat ini. Silakan coba lagi nanti.")
                        break

                    messages = state["messages"] + [("user", "Berikan respon yang valid.")]
                    state = {**state, "messages": messages}
                else:
                    break

            except Exception as e:
                retry_count += 1
                logger.error(f"Error in Assistant.__call__ (attempt {retry_count}): {str(e)}")

                # Jika error berkaitan dengan tool_calls, berikan respons tanpa tool calls
                if "tool_calls" in str(e) or "tool_call_id" in str(e):
                    logger.warning("Tool call error detected, returning simple response")
                    result = AIMessage(content="Maaf, terjadi kesalahan dalam memproses permintaan. Silakan coba lagi dengan permintaan yang lebih sederhana.")
                    break

                if retry_count >= self.max_retries:
                    # Jika sudah mencapai max retry, berikan respons default
                    result = AIMessage(content="Maaf, terjadi kesalahan sistem. Silakan coba lagi nanti.")
                    break

                # Untuk retry, jangan tambahkan pesan error ke state untuk menghindari loop
                continue

        return {"messages": result}

