from runtime.orchestration.orchestrator import run_orchestrator


def router(request):
    return {
        "task_type": "document_draft",
        "route_to": "planner",
        "confidence": 1.0,
        "reasoning_summary": "Drafting task",
        "handoff_payload": request,
    }


def planner(payload):
    message_text = payload.get("message_text", "")

    return {
        "intent": "communication",
        "sections": [
            {
                "id": "intro",
                "title": "Opening",
                "purpose": "Start formally",
                "required": True,
            },
            {
                "id": "body",
                "title": "Main",
                "purpose": message_text,
                "required": True,
            },
            {
                "id": "closing",
                "title": "Closing",
                "purpose": "Close formally",
                "required": True,
            },
        ],
        "draft_instructions": {
            "language": "ka",
            "tone": "formal",
            "constraints": [],
        },
    }


def reply_agent(planner_output):
    body_purpose = ""
    sections = planner_output.get("sections", [])
    for section in sections:
        if section.get("id") == "body":
            body_purpose = section.get("purpose", "")
            break

    if "შვებულებაში" in body_purpose or "leave" in body_purpose.lower():
        text = (
            "მოგესალმებით, გაცნობებთ, რომ თანამშრომელი შვებულებაში იმყოფება "
            "და სამსახურს დაუბრუნდება 5 სამუშაო დღეში. პატივისცემით,"
        )
    elif "შეხვედრა" in body_purpose or "meeting" in body_purpose.lower():
        text = (
            "მოგესალმებით, გაცნობებთ, რომ დაგეგმილი შეხვედრა გადაიდო. "
            "ახალი თარიღისა და დროის შესახებ დამატებით მოგაწვდით ინფორმაციას. "
            "პატივისცემით,"
        )
    else:
        text = (
            "მოგესალმებით, გაცნობებთ, რომ საკითხი დამუშავების პროცესშია. "
            "დამატებითი ინფორმაცია მოგვიანებით გეცნობებათ. პატივისცემით,"
        )

    return {
        "requires_gile": False,
        "text": text,
    }


def gile_client(payload):
    return {"text": payload.get("text", "")}


request = {
    "message_text": "დაწერე ოფიციალური წერილი, სადაც აცნობებ რომ მოთხოვნა მიღებულია და მიმდინარეობს დამუშვება, შედეგები ეცნობებათ უმოკლედ დროში.",
    "metadata": {},
    "context": {},
}


result = run_orchestrator(
    request=request,
    router=router,
    planner=planner,
    reply_agent=reply_agent,
    gile_client=gile_client,
)

print(result)