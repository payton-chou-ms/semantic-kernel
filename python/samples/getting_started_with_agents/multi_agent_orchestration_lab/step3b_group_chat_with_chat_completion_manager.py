# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys

from semantic_kernel.agents import Agent, ChatCompletionAgent, GroupChatOrchestration
from semantic_kernel.agents.orchestration.group_chat import (
    BooleanResult,
    GroupChatManager,
    MessageResult,
    StringResult,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent
from semantic_kernel.functions import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template import KernelPromptTemplate, PromptTemplateConfig

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


"""
以下範例示範如何建立群組聊天編排，
使用聊天完成服務來控制對話流程的群組聊天管理員。

此範例建立一組代表不同觀點的代理程式，
並將他們放入群組聊天中討論一個主題。群組聊天管理員負責
控制對話流程、選擇下一個發言的代理程式，以及
篩選對話結果，即討論的摘要。
"""


def get_agents() -> list[Agent]:
    """回傳將參與群組風格討論的代理程式清單。

    您可以自由新增或移除代理程式。
    """
    farmer = ChatCompletionAgent(
        name="Farmer",
        description="來自東南亞的農村農民。",
        instructions=(
            "您是來自東南亞的農民。"
            "您的生活與土地和家庭深度連結。"
            "您重視傳統和永續發展。"
            "您正在進行辯論。請自由地以尊重的方式挑戰其他參與者。"
        ),
        service=AzureChatCompletion(),
    )
    developer = ChatCompletionAgent(
        name="Developer",
        description="來自美國的都市軟體開發者。",
        instructions=(
            "您是來自美國的軟體開發者。"
            "您的生活步調快速且以技術為導向。"
            "您重視創新、自由和工作與生活的平衡。"
            "您正在進行辯論。請自由地以尊重的方式挑戰其他參與者。"
        ),
        service=AzureChatCompletion(),
    )
    teacher = ChatCompletionAgent(
        name="Teacher",
        description="來自東歐的退休歷史教師",
        instructions=(
            "您是來自東歐的退休歷史教師。"
            "您為討論帶來歷史和哲學觀點。"
            "您重視傳承、學習和文化延續性。"
            "您正在進行辯論。請自由地以尊重的方式挑戰其他參與者。"
        ),
        service=AzureChatCompletion(),
    )
    activist = ChatCompletionAgent(
        name="Activist",
        description="來自南美洲的年輕行動主義者。",
        instructions=(
            "您是來自南美洲的年輕行動主義者。"
            "您專注於社會正義、環境權利和世代變遷。"
            "您正在進行辯論。請自由地以尊重的方式挑戰其他參與者。"
        ),
        service=AzureChatCompletion(),
    )
    spiritual_leader = ChatCompletionAgent(
        name="SpiritualLeader",
        description="來自中東的精神領袖。",
        instructions=(
            "您是來自中東的精神領袖。"
            "您提供基於宗教、道德和社區服務的見解。"
            "您正在進行辯論。請自由地以尊重的方式挑戰其他參與者。"
        ),
        service=AzureChatCompletion(),
    )
    artist = ChatCompletionAgent(
        name="Artist",
        description="來自非洲的藝術家。",
        instructions=(
            "您是來自非洲的藝術家。"
            "您透過創意表達、說故事和集體記憶來看待生活。"
            "您正在進行辯論。請自由地以尊重的方式挑戰其他參與者。"
        ),
        service=AzureChatCompletion(),
    )
    immigrant = ChatCompletionAgent(
        name="Immigrant",
        description="來自亞洲居住在加拿大的移民企業家。",
        instructions=(
            "您是來自亞洲居住在加拿大的移民企業家。"
            "您在傳統與適應之間取得平衡。"
            "您專注於家庭成功、風險和機會。"
            "您正在進行辯論。請自由地以尊重的方式挑戰其他參與者。"
        ),
        service=AzureChatCompletion(),
    )
    doctor = ChatCompletionAgent(
        name="Doctor",
        description="來自斯堪地那維亞的醫生。",
        instructions=(
            "您是來自斯堪地那維亞的醫生。"
            "您的觀點受到公共衛生、公平和結構化社會支援的影響。"
            "您正在進行辯論。請自由地以尊重的方式挑戰其他參與者。"
        ),
        service=AzureChatCompletion(),
    )

    return [
        farmer,
        developer,
        teacher,
        activist,
        spiritual_leader,
        artist,
        immigrant,
        doctor,
    ]


class ChatCompletionGroupChatManager(GroupChatManager):
    """簡單的聊天完成群組聊天管理員基類。

    此聊天完成服務需要支援結構化輸出的模型。
    """

    service: ChatCompletionClientBase

    topic: str

    termination_prompt: str = (
        "您是指導關於「{{$topic}}」主題討論的調解員。"
        "您需要判斷討論是否已達成結論。"
        "如果您想要結束討論，請回應True。否則，回應False。"
    )

    selection_prompt: str = (
        "您是指導關於「{{$topic}}」主題討論的調解員。"
        "您需要選擇下一位發言的參與者。"
        "以下是參與者的姓名和描述："
        "{{$participants}}\n"
        "請僅回應您想要選擇的參與者姓名。"
    )

    result_filter_prompt: str = (
        "您是指導關於「{{$topic}}」主題討論的調解員。"
        "您剛剛結束了討論。"
        "請總結討論並提供結論陳述。"
    )

    def __init__(self, topic: str, service: ChatCompletionClientBase, **kwargs) -> None:
        """初始化群組聊天管理員。"""
        super().__init__(topic=topic, service=service, **kwargs)

    async def _render_prompt(self, prompt: str, arguments: KernelArguments) -> str:
        """協助使用參數渲染提示的輔助函數。"""
        prompt_template_config = PromptTemplateConfig(template=prompt)
        prompt_template = KernelPromptTemplate(
            prompt_template_config=prompt_template_config
        )
        return await prompt_template.render(Kernel(), arguments=arguments)

    @override
    async def should_request_user_input(
        self, chat_history: ChatHistory
    ) -> BooleanResult:
        """提供判斷是否需要使用者輸入的具體實作。

        管理員將在每個代理程式訊息後檢查是否需要人類輸入。
        """
        return BooleanResult(
            result=False,
            reason="此群組聊天管理員不需要使用者輸入。",
        )

    @override
    async def should_terminate(self, chat_history: ChatHistory) -> BooleanResult:
        """提供判斷討論是否應該結束的具體實作。

        管理員將在每個代理程式訊息或人類輸入（如適用）後
        檢查對話是否應該終止。
        """
        should_terminate = await super().should_terminate(chat_history)
        if should_terminate.result:
            return should_terminate

        chat_history.messages.insert(
            0,
            ChatMessageContent(
                role=AuthorRole.SYSTEM,
                content=await self._render_prompt(
                    self.termination_prompt,
                    KernelArguments(topic=self.topic),
                ),
            ),
        )
        chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER, content="Determine if the discussion should end."
            ),
        )

        response = await self.service.get_chat_message_content(
            chat_history,
            settings=PromptExecutionSettings(response_format=BooleanResult),
        )

        termination_with_reason = BooleanResult.model_validate_json(response.content)

        print("*********************")
        print(
            f"Should terminate: {termination_with_reason.result}\nReason: {termination_with_reason.reason}."
        )
        print("*********************")

        return termination_with_reason

    @override
    async def select_next_agent(
        self,
        chat_history: ChatHistory,
        participant_descriptions: dict[str, str],
    ) -> StringResult:
        """Provide concrete implementation for selecting the next agent to speak.

        The manager will select the next agent to speak after each agent message
        or human input (if applicable) if the conversation is not terminated.
        """
        chat_history.messages.insert(
            0,
            ChatMessageContent(
                role=AuthorRole.SYSTEM,
                content=await self._render_prompt(
                    self.selection_prompt,
                    KernelArguments(
                        topic=self.topic,
                        participants="\n".join(
                            [f"{k}: {v}" for k, v in participant_descriptions.items()]
                        ),
                    ),
                ),
            ),
        )
        chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content="Now select the next participant to speak.",
            ),
        )

        response = await self.service.get_chat_message_content(
            chat_history,
            settings=PromptExecutionSettings(response_format=StringResult),
        )

        participant_name_with_reason = StringResult.model_validate_json(
            response.content
        )

        print("*********************")
        print(
            f"Next participant: {participant_name_with_reason.result}\nReason: {participant_name_with_reason.reason}."
        )
        print("*********************")

        if participant_name_with_reason.result in participant_descriptions:
            return participant_name_with_reason

        raise RuntimeError(f"Unknown participant selected: {response.content}.")

    @override
    async def filter_results(
        self,
        chat_history: ChatHistory,
    ) -> MessageResult:
        """Provide concrete implementation for filtering the results of the discussion.

        The manager will filter the results of the conversation after the conversation is terminated.
        """
        if not chat_history.messages:
            raise RuntimeError("No messages in the chat history.")

        chat_history.messages.insert(
            0,
            ChatMessageContent(
                role=AuthorRole.SYSTEM,
                content=await self._render_prompt(
                    self.result_filter_prompt,
                    KernelArguments(topic=self.topic),
                ),
            ),
        )
        chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER, content="Please summarize the discussion."
            ),
        )

        response = await self.service.get_chat_message_content(
            chat_history,
            settings=PromptExecutionSettings(response_format=StringResult),
        )
        string_with_reason = StringResult.model_validate_json(response.content)

        return MessageResult(
            result=ChatMessageContent(
                role=AuthorRole.ASSISTANT, content=string_with_reason.result
            ),
            reason=string_with_reason.reason,
        )


def agent_response_callback(message: ChatMessageContent) -> None:
    """取得代理程式回應的回調函數。"""
    print(f"**{message.name}**\n{message.content}")


async def main():
    """執行代理程式的主要函數。"""
    # 1. 使用自訂群組聊天管理員建立群組聊天編排
    agents = get_agents()
    group_chat_orchestration = GroupChatOrchestration(
        members=agents,
        manager=ChatCompletionGroupChatManager(
            topic="對您個人而言，美好的生活意味著什麼？",
            service=AzureChatCompletion(),
            max_rounds=10,
        ),
        agent_response_callback=agent_response_callback,
    )

    # 2. 建立運行時並啟動
    runtime = InProcessRuntime()
    runtime.start()

    # 3. 使用任務和運行時呼叫編排
    orchestration_result = await group_chat_orchestration.invoke(
        task="請開始討論。",
        runtime=runtime,
    )

    # 4. 等待結果
    value = await orchestration_result.get()
    print(value)

    # 5. 呼叫完成後停止運行時
    await runtime.stop_when_idle()

    """
    範例輸出：
    *********************
    是否應終止：False
    原因：關於個人美好生活意義的討論尚未開始，這意味著參與者尚未...
    *********************
    *********************
    下一位參與者：Farmer
    原因：來自東南亞的農民可以提供強調與...的連結重要性的觀點
    *********************
    **Farmer**
    感謝您給我分享觀點的機會。作為來自東南亞的農民，我的生活與...錯綜複雜地連結
    *********************
    是否應終止：False
    原因：討論剛剛開始，只分享了一個觀點。還有進一步...的空間
    *********************
    *********************
    下一位參與者：Developer
    原因：在農民之後，為了提供關於美好生活構成要素的農村和都市觀點對比...
    *********************
    **Developer**
    感謝您讓我加入討論的機會。作為生活在以技術為導向的軟體開發者...
    *********************
    是否應終止：False
    原因：討論剛剛開始，已有農民和開發者關於...的觀點
    *********************
    *********************
    下一位參與者：Teacher
    原因：教師憑藉其豐富的經驗和歷史觀點，可以提供有價值的見解...
    *********************
    **Teacher**
    作為來自東歐的退休歷史教師，我發現探索歷史的線索如何...很有趣
    *********************
    是否應終止：True
    原因：代表不同觀點的參與者——農民、開發者和教師——都已各自分享...
    *********************
    我們關於美好生活構成要素的討論圍繞著農民、開發者和教師的關鍵觀點展開...
    """


if __name__ == "__main__":
    asyncio.run(main())
