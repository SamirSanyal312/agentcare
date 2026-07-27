from app.llm.provider import get_llm


def main() -> None:
    llm = get_llm()

    response = llm.invoke(
        [
            (
                "system",
                (
                    "You are a healthcare administrative assistant. "
                    "You do not diagnose conditions, prescribe medication, "
                    "recommend dosages, or replace clinicians."
                ),
            ),
            (
                "human",
                (
                    "A patient wants to schedule a cardiology "
                    "appointment next week. In one sentence, state "
                    "the administrative task."
                ),
            ),
        ]
    )

    print(response.content)


if __name__ == "__main__":
    main()