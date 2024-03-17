import os
from typing import List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    load_prompt,
)
from langchain_core.output_parsers import NumberedListOutputParser
from langchain_core.messages import AIMessage, HumanMessage

from honcho import Collection, Session, Message

load_dotenv()


SYSTEM_SUMMARIZE = load_prompt(
    os.path.join(os.path.dirname(__file__), "prompts/core/summarize.yaml")
)
SYSTEM_DERIVE_FACTS = load_prompt(
    os.path.join(os.path.dirname(__file__), "prompts/core/derive_transcript_facts.yaml")
)
# SYSTEM_INTROSPECTION = load_prompt(
#     os.path.join(os.path.dirname(__file__), "prompts/core/introspection.yaml")
# )
# SYSTEM_RESPONSE = load_prompt(
#     os.path.join(os.path.dirname(__file__), "prompts/core/response.yaml")
# )
SYSTEM_CHECK_DUPS = load_prompt(
    os.path.join(os.path.dirname(__file__), "prompts/utils/check_dup_facts.yaml")
)


class TranscriptChain:
    "Wrapper class for encapsulating the multiple different chains used"

    output_parser = NumberedListOutputParser()
    llm: ChatOpenAI = ChatOpenAI(model_name="gpt-4-turbo-preview")
    system_derive_facts: SystemMessagePromptTemplate = SystemMessagePromptTemplate(
        prompt=SYSTEM_DERIVE_FACTS
    )
    system_summarize: SystemMessagePromptTemplate = SystemMessagePromptTemplate(
        prompt=SYSTEM_SUMMARIZE
    )
    # system_response: SystemMessagePromptTemplate = SystemMessagePromptTemplate(
    #     prompt=SYSTEM_RESPONSE
    # )
    system_check_dups: SystemMessagePromptTemplate = SystemMessagePromptTemplate(
        prompt=SYSTEM_CHECK_DUPS
    )

    def __init__(self) -> None:
        pass
    
    @classmethod
    async def summarize(cls, transcript: str):
        """Create SOAP note"""

        # format prompt
        system_summarize = ChatPromptTemplate.from_messages([cls.system_summarize])

        # LCEL
        chain = system_summarize | cls.llm

        # inference
        response = await chain.ainvoke(
            {
                "transcript": transcript
            }
        )

        # parse output
        summary = response.content

        print(f"SOAP Note: {summary}")

        return summary

    @classmethod
    async def derive_facts(cls, transcript: str, summary: str):
        """Derive facts from the user input"""

        # format prompt
        fact_derivation = ChatPromptTemplate.from_messages([cls.system_derive_facts])

        # LCEL
        chain = fact_derivation | cls.llm

        # inference
        response = await chain.ainvoke(
            {
                "transcript": transcript,
                "summary": summary
            }
        )

        # parse output
        facts = cls.output_parser.parse(response.content)

        print(f"DERIVED FACTS: {facts}")

        return facts

    @classmethod
    async def check_dups(
        cls,
        collection: Collection,
        facts: List,
        summary: str,
    ):
        """Check that we're not storing duplicate facts"""

        # format prompt
        check_duplication = ChatPromptTemplate.from_messages([cls.system_check_dups])

        query = " ".join(facts)
        result = collection.query(query=query, top_k=10)
        existing_facts = [document.content for document in result]

        # LCEL
        chain = check_duplication | cls.llm

        # inference
        response = await chain.ainvoke(
            {"existing_facts": existing_facts, "facts": facts}
        )

        # parse output
        new_facts = cls.output_parser.parse(response.content)

        print(f"FILTERED FACTS: {new_facts}")

        # TODO: write to vector store
        for fact in new_facts:
            collection.create_document(content=fact, metadata={"type": "facts"})
        collection.create_document(content=summary, metadata={"type": "summary"})

        # add facts as metamessages
        # for fact in new_facts:
        #     session.create_metamessage(
        #         message=user_message, metamessage_type="fact", content=fact
        #     )

        return

    @classmethod
    async def introspect(
        cls, user_message: Message, session: Session, chat_history: List, input: str
    ):
        """Generate questions about the user to use as retrieval over the fact store"""

        # format prompt
        introspection_prompt = ChatPromptTemplate.from_messages(
            [cls.system_introspection]
        )

        # LCEL
        chain = introspection_prompt | cls.llm

        # inference
        response = await chain.ainvoke(
            {"chat_history": chat_history, "user_input": input}
        )

        # parse output
        questions = cls.output_parser.parse(response.content)

        print(f"INTROSPECTED QUESTIONS: {questions}")

        # write questions as metamessages
        for question in questions:
            session.create_metamessage(
                message=user_message, metamessage_type="introspect", content=question
            )

        return questions

    @classmethod
    async def respond(
        cls, collection: Collection, chat_history: List, questions: List, input: str
    ):
        """Take the facts and chat history and generate a personalized response"""

        # format prompt
        response_prompt = ChatPromptTemplate.from_messages(
            [cls.system_response, *chat_history, HumanMessage(content=input)]
        )

        retrieved_facts = collection.query(query=questions, top_k=10)
        retrieved_facts_content = [document.content for document in retrieved_facts]

        # LCEL
        chain = response_prompt | cls.llm

        # inference
        response = await chain.ainvoke(
            {
                "facts": retrieved_facts_content,
            }
        )

        return response.content

    @classmethod
    async def process(
        cls,
        transcript: str,
        session: Session,
        collection: Collection,
    ):
        """Chat with the model"""

        summary = await cls.summarize(transcript)
        facts = await cls.derive_facts(transcript, summary)
        await cls.check_dups(collection, facts, summary) if facts is not None else None

        # introspect
        # questions = await cls.introspect(user_message, session, chat_history, input)

        # respond
        # response = await cls.respond(collection, chat_history, questions, input)

        return facts
