# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentGroupChat, AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.contents import AuthorRole

"""
The following sample demonstrates how to create an OpenAI assistant using either
Azure OpenAI or OpenAI, a chat completion agent and have them participate in a
group chat to work towards the user's requirement.

注意：此範例使用 Semantic Kernel 的 `AgentGroupChat`，
目前已不再維護。建議改用 `GroupChatOrchestration`。

Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python

Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


REVIEWER_NAME = "ArtDirector"
REVIEWER_INSTRUCTIONS = """
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved.  Do not use the word "approve" unless you are giving approval.
If not, provide insight on how to refine suggested copy without example.
"""

COPYWRITER_NAME = "CopyWriter"
COPYWRITER_INSTRUCTIONS = """
You are a copywriter with ten years of experience and are known for brevity and a dry humor.
The goal is to refine and decide on the single best copy as an expert in the field.
Only provide a single proposal per response.
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"""

TASK = "a slogan for a new line of electric cars."


async def main():
    ai_agent_settings = AzureAIAgentSettings()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 在 Azure AI Agent 服務建立審核者 agent
        reviewer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=REVIEWER_NAME,
            instructions=REVIEWER_INSTRUCTIONS,
        )

        # 2. 建立對應的 Semantic Kernel 審核者 agent
        agent_reviewer = AzureAIAgent(
            client=client,
            definition=reviewer_agent_definition,
        )

        # 3. 在 Azure AI Agent 服務建立撰寫者 agent
        copy_writer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=COPYWRITER_NAME,
            instructions=COPYWRITER_INSTRUCTIONS,
        )

        # 4. 建立對應的 Semantic Kernel 撰寫者 agent
        agent_writer = AzureAIAgent(
            client=client,
            definition=copy_writer_agent_definition,
        )

        # 5. 將 agents 加入群組聊天並設定自訂終止策略
        chat = AgentGroupChat(
            agents=[agent_writer, agent_reviewer],
            termination_strategy=ApprovalTerminationStrategy(
                agents=[agent_reviewer], maximum_iterations=10
            ),
        )

        try:
            # 6. 將任務加入群組聊天
            await chat.add_chat_message(message=TASK)
            print(f"# {AuthorRole.USER}: '{TASK}'")
            # 7. 呼叫群組聊天
            async for content in chat.invoke():
                print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
        finally:
            # 8. 清理資源：刪除 agents
            await chat.reset()
            await client.agents.delete_agent(agent_reviewer.id)
            await client.agents.delete_agent(agent_writer.id)

        """
        範例輸出：
        # AuthorRole.USER: 'a slogan for a new line of electric cars.'
        # AuthorRole.ASSISTANT - CopyWriter: '"Charge Ahead: Drive the Future."'
        # AuthorRole.ASSISTANT - ArtDirector: 'This slogan has a nice ring to it and captures the ...'
        # AuthorRole.ASSISTANT - CopyWriter: '"Plug In. Drive Green."'
        ...
        """


if __name__ == "__main__":
    asyncio.run(main())
