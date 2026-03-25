from datetime import date

from runtime.orchestration.orchestrator import run_orchestrator

GEORGIAN_MONTHS = {
    1: "იანვარი", 2: "თებერვალი", 3: "მარტი", 4: "აპრილი",
    5: "მაისი", 6: "ივნისი", 7: "ივლისი", 8: "აგვისტო",
    9: "სექტემბერი", 10: "ოქტომბერი", 11: "ნოემბერი", 12: "დეკემბერი",
}


def _format_date_ka():
    today = date.today()
    return f"{today.day} {GEORGIAN_MONTHS[today.month]}, {today.year} წელი"


def _build_letter(body: str) -> str:
    date_line = _format_date_ka()
    greeting = "პატივცემულო მიმღებო,"
    closing = (
        "პატივისცემით,\n"
        "საქმისწარმოების სამსახური"
    )
    return f"{date_line}\n\n{greeting}\n\n{body}\n\n{closing}"


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

    if "შვებულებაში" in body_purpose:
        body = (
            "გაცნობებთ, რომ აღნიშნული თანამშრომელი ამჟამად ყოფნის შვებულებაში "
            "და სამსახურს დაუბრუნდება 5 (ხუთი) სამუშაო დღეში. "
            "თქვენი საკითხი განიხილება დასვენებიდან დაბრუნებისთანავე."
        )
    elif "შეხვედრა" in body_purpose:
        body = (
            "გაცნობებთ, რომ დაგეგმილი შეხვედრა ობიექტური გარემოებების გამო გადაიდო. "
            "ახალი თარიღისა და დროის შესახებ დამატებითი შეტყობინება გამოგეგზავნებათ "
            "უახლოეს დროში."
        )
    elif "მოთხოვნა მიღებულია" in body_purpose or "მიღებულია" in body_purpose:
        body = (
            "გაცნობებთ, რომ თქვენი მოთხოვნა მიღებულია და განხილვის პროცესშია. "
            "შესაბამისი სამსახური ამუშავებს წარდგენილ მასალებს დადგენილი წესით. "
            "შედეგები გეცნობებათ რაც შეიძლება მოკლე ვადაში."
        )
    else:
        body = (
            "გაცნობებთ, რომ დასმული საკითხი შესწავლისა და განხილვის პროცესშია. "
            "უფრო დეტალური ინფორმაცია და შემდგომი ნაბიჯები გეცნობებათ მოგვიანებით."
        )

    return {
        "requires_gile": False,
        "text": _build_letter(body),
    }


def gile_client(payload):
    return {"text": payload.get("text", "")}


request = {
    "message_text": (
        "დაწერე ოფიციალური წერილი, სადაც აცნობებ რომ თქვენი მოთხოვნა მიღებულია "
        "და მიმდინარეობს დამუშავება, შედეგები ეცნობებათ უმოკლეს დროში."
    ),
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