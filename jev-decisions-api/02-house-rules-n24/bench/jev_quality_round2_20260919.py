# -*- coding: utf-8 -*-
"""Round 1 was too easy - every model scored 20/20, including an 8B. So make it hard the way
production is hard, and test the three things that actually decide whether a classifier is usable.

Q1 accuracy under degradation   OCR-mangled text, Polish/German documents, and one real-length
                                email where the document is buried in a thread. 18 items.
Q2 does it know it doesn't know 6 items where the evidence genuinely does not decide the class.
                                There is no right answer; the right BEHAVIOUR is low confidence.
                                Scored as: mean confidence on decidable items minus mean confidence
                                on undecidable ones. A model that says 0.95 to everything scores 0.
Q3 consistency                  6 items asked 3x. Same input, same answer? A classifier that moves
                                between runs cannot be audited, reconciled or regression-tested.

Chat models get max_tokens=800 this round: three of round 1's "errors" were correct answers
truncated by a 300-token budget their reasoning had already eaten. Not a model failure.
"""
import json
import os
import pathlib
import statistics
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent            # EDIT 1 of 2 (see README)
DEC_URL = "https://openrouter.ai/api/alpha/decisions"
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
JEV = "typesafe/jev-1.13"
SMALL = ["openai/gpt-oss-20b", "mistralai/ministral-8b-2512", "google/gemini-3.8-flash"]
OUT = HERE.parent / "results" / "jev-quality-round2-20260919.json"
RESULTS = {}


def token():                                              # EDIT 2 of 2 (see README)
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("set OPENROUTER_API_KEY")
    return key


HDR = {"Authorization": "Bearer " + token(), "Content-Type": "application/json",
       "HTTP-Referer": "https://bughunt.productcompass.pm", "X-Title": "jev quality round2"}
SPEND = {}


def post(url, body, timeout=180):
    req = urllib.request.Request(url, method="POST", data=json.dumps(body).encode(), headers=HDR)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "ms": int((time.time() - t0) * 1000), "d": json.load(r)}
    except urllib.error.HTTPError as e:
        return {"ok": False, "ms": int((time.time() - t0) * 1000),
                "error": e.read().decode("utf-8", "replace")[:200]}
    except Exception as exc:                                                  # noqa: BLE001
        return {"ok": False, "ms": int((time.time() - t0) * 1000), "error": repr(exc)}


DOC_CRIT = {
    "invoice": "a seller's demand for payment: an amount is owed and not yet paid, with terms or a "
               "due date, for goods or services already supplied or being supplied",
    "receipt": "confirms money has ALREADY been paid; nothing remains outstanding on it",
    "quote": "a priced offer made BEFORE the buyer is committed and before supply, including "
             "pro-forma and estimate documents issued in advance of delivery",
    "purchase_order": "the BUYER's own document instructing a supplier to deliver; it authorises a "
                      "purchase rather than demanding payment",
    "credit_note": "reduces, refunds or cancels an amount previously invoiced; the net effect is in "
                   "the buyer's favour",
    "statement": "a periodic summary listing several transactions or open documents; it is not "
                 "itself the demand for one specific payment",
}
CRIT_TEXT = "\n".join("- %s: %s" % (k, v) for k, v in DOC_CRIT.items())
INSTR = ("Classify this document using ONLY the supplied definitions. The document's own title may "
         "be misleading, the text may be damaged by OCR, and it may not be in English; follow the "
         "definitions.")


def ask_jev(text):
    r = post(DEC_URL, {"model": JEV, "state": {"document_text": text},
                       "questions": {"doc_type": {"type": "choice", "criteria": DOC_CRIT,
                                                  "instructions": INSTR}}})
    if not r["ok"]:
        return {"ok": False, "error": r.get("error"), "ms": r["ms"]}
    u = r["d"].get("usage") or {}
    SPEND[JEV] = SPEND.get(JEV, 0.0) + (u.get("cost") or 0.0)
    a = r["d"]["answers"]["doc_type"]
    probs = a.get("probabilities") or {}
    return {"ok": True, "ms": r["ms"], "picked": a["choice"],
            "p": max(probs.values()) if probs else None, "conf": a.get("confidence")}


def ask_chat(model, text):
    p = ("Classify the document below using ONLY these definitions:\n%s\n\n%s\n\nDocument:\n%s\n\n"
         'Answer with JSON only: {"type":"<one of: %s>","confidence":<number 0-1, how sure you are>}'
         % (CRIT_TEXT, INSTR, text, ", ".join(DOC_CRIT)))
    r = post(CHAT_URL, {"model": model, "max_tokens": 800, "temperature": 0,
                        "messages": [{"role": "system", "content": "Reply with ONLY minified JSON."},
                                     {"role": "user", "content": p}]})
    if not r["ok"]:
        return {"ok": False, "error": r.get("error"), "ms": r["ms"]}
    d = r["d"]
    SPEND[model] = SPEND.get(model, 0.0) + float((d.get("usage") or {}).get("cost", 0) or 0)
    txt = (d["choices"][0]["message"].get("content") or "").strip()
    if txt.startswith("```"):
        txt = txt.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0]
    i, j = txt.find("{"), txt.rfind("}")
    try:
        parsed = json.loads(txt[i:j + 1])
    except Exception:                                                         # noqa: BLE001
        return {"ok": False, "error": "unparsable: " + txt[:90], "ms": r["ms"]}
    c = parsed.get("confidence")
    return {"ok": True, "ms": r["ms"], "picked": str(parsed.get("type", "")).strip(),
            "p": c if isinstance(c, (int, float)) else None, "conf": c}


# ------------------------------------------------------------------ Q1 degraded / multilingual
HARD = [
    # OCR damage
    ("1NV01CE #447l   Due 3O Sep 2O26   T0tal due EUR 2,4OO.OO   Terms: Net 3O", "invoice"),
    ("PR0 F0RMA lNV0lCE 22ll.  N0t a tax inv0ice.  G00ds n0t yet shipped.  Va1id l4 days.", "quote"),
    ("RECE1PT  Pa1d in fu11 l2 Sep 2O26  VlSA ****44l2  Ba1ance due O.OO", "receipt"),
    ("CRED1T N0TE CN-ll8 against inv0ice 447l.  Am0unt -EUR 4OO.OO.  G00ds returned.", "credit_note"),
    # Polish
    ("FAKTURA PRO FORMA nr 22/2026. Nie jest dokumentem ksiegowym. Towar nie zostal wyslany. "
     "Do zaplaty 3 690,00 PLN, termin 14 dni.", "quote"),
    ("PARAGON FISKALNY. SUMA PLN 89,00. Zaplacono gotowka. Dziekujemy za zakupy.", "receipt"),
    ("KOREKTA FAKTURY nr 9902 do faktury 9871. Kwota -350,00 PLN. Przyczyna: zawyzona cena.",
     "credit_note"),
    ("FAKTURA VAT nr 4471. Termin platnosci: 30.09.2026. Do zaplaty: 2 400,00 PLN. Przelew na "
     "rachunek...", "invoice"),
    ("ZAMOWIENIE nr ZAM-5512. Zamawiajacy: Acme Sp. z o.o. Dostawca: Bolt Supplies. Prosimy o "
     "dostawe 40 sztuk do 1 pazdziernika.", "purchase_order"),
    # German
    ("Rechnung Nr. 5501. Zahlungseingang dankend bestaetigt am 14.09.2026. Offener Betrag 0,00 EUR.",
     "receipt"),
    ("Kontoauszug August 2026. Anfangssaldo 3.200. Rg 4410 1.200. Rg 4433 900. Endsaldo 5.300.",
     "statement"),
    ("Angebot A-114. Unverbindliche Preisangabe, freibleibend. Keine Zahlungsaufforderung.", "quote"),
    # buried in a real-length email thread
    ("From: ola@acme.pl\nTo: finance@boltsupplies.com\nSubject: RE: RE: FW: September\n\n"
     "Hi Marek, thanks - looping in finance. See below, and note we still have not had the "
     "delivery note for the August order, which Tomek says went out on the 29th. Can someone "
     "confirm?\n\n> On 14 Sep, Marek wrote:\n> Attaching the document for your records. As "
     "discussed on the call we have applied the 5% we agreed in the framework agreement, and the "
     "logistics surcharge has been dropped for this period.\n>\n> DOCUMENT FOLLOWS\n> "
     "-----------------------------------------\n> Bolt Supplies Sp. z o.o., NIP 5252445566\n> "
     "Document no. 4471 of 1 September 2026\n> Line 1: 40 x connector type B ... 1,800.00\n> "
     "Line 2: logistics surcharge ......... 0.00\n> Line 3: framework discount 5% ... -90.00\n> "
     "Net 1,710.00  VAT 23% 393.30  GROSS 2,103.30\n> Payment terms: 30 days from issue, "
     "30 September 2026\n> Amount outstanding: 2,103.30\n> -----------------------------------------"
     "\n>\n> Let me know if the cost centre is wrong again.\n\n-- \nOla Nowak | Acme",
     "invoice"),
    ("From: billing@saas.io\nTo: pawel@acme.pl\nSubject: Your September documents\n\nHi Pawel,\n\n"
     "Here is the monthly wrap-up for your workspace. Nothing is due - your card on file was "
     "charged automatically and everything below has settled.\n\n  12 Sep  Seats (14)      "
     "406.00  PAID\n  12 Sep  Overage             38.00  PAID\n  12 Sep  Credit applied     -20.00\n"
     "  ------------------------------------------\n  Total charged                   424.00\n"
     "  Balance carried forward           0.00\n\nYou can download individual documents from the "
     "billing portal. Reply to this email if anything looks wrong.\n\nThe SaaS.io billing robot",
     "statement"),
    # conflicting surface evidence
    ("TAX INVOICE 7781. Status: SETTLED. Amount 540.00. Received with thanks, no further payment "
     "required.", "receipt"),
    ("Quotation Q-900 - ACCEPTED AND INVOICED. Please remit EUR 8,000 within 14 days, ref INV-1310.",
     "invoice"),
    ("Statement of account. One open item: invoice 4501, EUR 600.00, due 30 Sep. Please pay this "
     "amount by the due date.", "statement"),
    ("Order form countersigned by Acme Ltd as buyer, instructing Bolt Supplies to ship 40 units; "
     "Bolt will invoice separately on dispatch.", "purchase_order"),
]

# ------------------------------------------------------------------ Q2 genuinely undecidable
AMBIG = [
    "Document 8812.",
    "Total: 450.00. Ref: 8812. Thank you.",
    "Attached please find the document for August, amount 2,000. Regards, Anna",
    "ACME Ltd | 4471 | 2,400.00 | 30/09/2026",
    "Payment advice: we will pay your document 4471 on 30 September from account ...4412.",
    "Dokument nr 77/2026. Kwota: 1 230,00 PLN.",
]

REPEAT = [HARD[0][0], HARD[4][0], HARD[12][0], AMBIG[1], AMBIG[3], HARD[15][0]]


def run_model(name, fn):
    out = {"hard": [], "ambig": [], "repeat": {}}
    ms = []
    for text, truth in HARD:
        r = fn(text)
        if not r["ok"]:
            out["hard"].append({"truth": truth, "error": r.get("error")})
            continue
        ms.append(r["ms"])
        out["hard"].append({"truth": truth, "picked": r["picked"], "hit": r["picked"] == truth,
                            "p": r["p"], "text": text[:50]})
    for text in AMBIG:
        r = fn(text)
        out["ambig"].append({"picked": r.get("picked"), "p": r.get("p"),
                             "error": r.get("error"), "text": text[:50]})
    for text in REPEAT:
        picks = []
        for _ in range(3):
            r = fn(text)
            picks.append((r.get("picked"), r.get("p")))
        out["repeat"][text[:40]] = picks

    ok = [r for r in out["hard"] if "picked" in r]
    acc = statistics.fmean([r["hit"] for r in ok]) if ok else float("nan")
    p_clear = [r["p"] for r in ok if isinstance(r.get("p"), (int, float))]
    p_amb = [r["p"] for r in out["ambig"] if isinstance(r.get("p"), (int, float))]
    drop = (statistics.fmean(p_clear) - statistics.fmean(p_amb)) if (p_clear and p_amb) else float("nan")
    same_label = statistics.fmean([len({p[0] for p in v}) == 1 for v in out["repeat"].values()])
    same_number = statistics.fmean([len({p for p in v}) == 1 for v in out["repeat"].values()])
    out["summary"] = {"acc": acc, "errors": len(out["hard"]) - len(ok),
                      "median_ms": statistics.median(ms) if ms else None,
                      "conf_clear": statistics.fmean(p_clear) if p_clear else None,
                      "conf_ambiguous": statistics.fmean(p_amb) if p_amb else None,
                      "conf_drop": drop, "repeat_same_label": same_label,
                      "repeat_identical": same_number}
    print("  %-32s acc=%3.0f%%  err=%d  conf: clear %.2f / undecidable %.2f  DROP=%+.2f  "
          "repeat same label=%3.0f%% identical=%3.0f%%  median=%sms"
          % (name, acc * 100, out["summary"]["errors"],
             out["summary"]["conf_clear"] or float("nan"),
             out["summary"]["conf_ambiguous"] or float("nan"), drop,
             same_label * 100, same_number * 100, out["summary"]["median_ms"]), flush=True)
    return out


def main():
    print("=" * 96)
    print("Q1 accuracy on 18 degraded/multilingual/buried docs | Q2 confidence on 6 undecidable "
          "| Q3 3x repeats")
    print("=" * 96)
    RESULTS[JEV] = run_model(JEV, ask_jev)
    for m in SMALL:
        RESULTS[m] = run_model(m, lambda t, m=m: ask_chat(m, t))

    print("\nMisses, item by item:")
    for i, (text, truth) in enumerate(HARD):
        line = []
        for m, res in RESULTS.items():
            r = res["hard"][i]
            if not r.get("hit"):
                line.append("%s->%s" % (m.split("/")[-1][:12], r.get("picked") or "ERR"))
        if line:
            print("  want %-15s %s\n    %s" % (truth, "  ".join(line), text[:80].replace("\n", " ")))

    print("\nWhat each model said about the 6 undecidable documents (confidence in brackets):")
    for i, text in enumerate(AMBIG):
        picks = ["%s=%s[%s]" % (m.split("/")[-1][:12], RESULTS[m]["ambig"][i].get("picked"),
                                RESULTS[m]["ambig"][i].get("p")) for m in RESULTS]
        print("  %-52s %s" % (text[:52], "  ".join(picks)))

    print("\nSPEND")
    for k, v in SPEND.items():
        print("  %-34s $%.5f" % (k, v))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"results": RESULTS, "spend": SPEND}, indent=1, default=str),
                   encoding="utf-8")
    print("  written: %s" % OUT)


if __name__ == "__main__":
    main()
