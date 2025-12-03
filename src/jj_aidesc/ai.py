import html

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from jj_aidesc.error import AIError


class Description(BaseModel):
    message: str = Field(..., description="The generated commit description")


class AI:
    def __init__(
        self,
        model: BaseChatModel,
        system_prompt: tuple[str, str],
        language: str = "English",
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.language = language

    def generate(
        self,
        diff: str,
        existing_descriptions: list[str] | None = None,
    ) -> str:
        try:
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    self.system_prompt,
                    (
                        "human",
                        "<diff>\n{diff}\n</diff>",
                    ),
                ]
            )

            chain = prompt_template | self.model.with_structured_output(Description)

            result: Description = chain.invoke(
                {
                    "diff": html.escape(diff),
                    "existing_descriptions": html.escape(
                        "\n\n".join(existing_descriptions or [])
                    ),
                    "language": self.language,
                }
            )  # type: ignore

            return result.message

        except Exception as e:
            raise AIError(f"AI generation failed: {e}") from e
