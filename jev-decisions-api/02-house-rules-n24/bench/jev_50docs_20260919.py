# -*- coding: utf-8 -*-
"""50 documents, six models, same prompt, exact billed cost. Run concurrently.

The 18-document round separated the field by exactly one item, which is too thin to rank anything,
and the open question is not "how many" but "does it hold up when the surface cue lies". So this
adds 32 harder ones. Each is still DECIDABLE under the six supplied definitions, but each defeats
the shortcut a classifier reaches for:

  - self-billed invoice      the BUYER issues it -> the buyer/seller cue points at purchase_order
  - deposit invoice          money demanded BEFORE supply -> the timing cue points at quote
  - progress application     no invoice vocabulary at all, just "application for payment"
  - proforma for shipped goods   the title says the usual quote-word, the body is a payment demand
  - purchase order with prices   carries unit prices -> the money cue points at quote
  - "INVOICE SUMMARY" statement  invoice in the title, "not a request for payment" in the body
  - zero-balance statement   nothing outstanding -> the balance cue points at receipt
  - open-items reminder      demands one total -> the "please pay" cue points at invoice
  - credit as a positive number  no minus sign to key on, and no word "credit" in one of them
  - three documents with NO vocabulary: a freelancer's email (invoice), a casual restock ask
    (purchase order), a "nothing booked yet" price in an email (quote)
  - plus Polish, German, Portuguese, Czech, Spanish, French, Dutch, Italian, Hungarian, Japanese,
    OCR damage, and an amount written in words

LATENCY: this run is concurrent, so the per-call ms here is NOT comparable to a sequential run.
Accuracy and billed cost are concurrency-invariant; quote latency from the sequential round only.
"""
import concurrent.futures as cf
import importlib.util
import json
import pathlib
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent            # EDIT 1 of 2 (see README)
spec = importlib.util.spec_from_file_location(
    "r2", HERE / "jev_quality_round2_20260919.py")
r2 = importlib.util.module_from_spec(spec)
sys.modules["r2"] = r2
spec.loader.exec_module(r2)

DOC_CRIT, CRIT_TEXT, INSTR = r2.DOC_CRIT, r2.CRIT_TEXT, r2.INSTR
HDR, DEC_URL, CHAT_URL = r2.HDR, r2.DEC_URL, r2.CHAT_URL
OUT = HERE.parent / "results" / "jev-50docs-20260919.json"
JEV = "typesafe/jev-1.13"

EXTRA = [
    ("SELF-BILLED INVOICE SB-118. Acme Ltd raises this document on behalf of Bolt Supplies under "
     "our self-billing agreement. Amount due to the supplier: EUR 4,200.00, payable 30 days from "
     "the date above.", "invoice"),
    ("DEPOSIT INVOICE 44/2026. A 30% advance is required before manufacturing begins. Amount now "
     "due: EUR 3,000.00. The balance will be invoiced on delivery. Order confirmed 2 September.",
     "invoice"),
    ("APPLICATION FOR PAYMENT No. 3. Works completed to date: 62%. Value of works this period: "
     "GBP 18,400.00. Payment becomes due 14 days from certification.", "invoice"),
    ("STATEMENT. Period: August 2026. No items outstanding. Balance carried forward: 0.00. "
     "Issued for your records only.", "statement"),
    ("GUTSCHRlFT Nr. 2l8 zu Rechnung 99O2. Betrag -35O,OO EUR. Grund: Preiskorrektur nach "
     "Reklamation.", "credit_note"),
    ("ZESTAWIENIE ROZLICZEN za wrzesien 2026. Faktura 4410: 1 200,00. Faktura 4433: 900,00. "
     "Faktura 4501: 600,00. Saldo koncowe: 2 700,00 PLN.", "statement"),
    ("Invoice no. 7781. Payable: four thousand five hundred euros only. Due within twenty-one days "
     "of receipt. Our bank details are unchanged.", "invoice"),
    ("PEDIDO DE COMPRA n. 5512. Comprador: Acme Lda. Fornecedor: Bolt Supplies. Solicitamos a "
     "entrega de 40 unidades no armazem de Lisboa ate 1 de outubro.", "purchase_order"),
    ("PROPOSAL / ESTIMATE. Indicative price EUR 9,800, subject to a site survey. Should you wish "
     "to proceed, a 30% deposit will be requested at that point. This document creates no "
     "obligation.", "quote"),
    ("REMINDER OF OPEN ITEMS. The following documents remain unpaid on your account: 4410 "
     "(1,200.00), 4433 (900.00), 4501 (600.00). Please settle the total of 2,700.00.", "statement"),
    ("UCTENKA c. 88/2026. Celkem 1 250,00 Kc. Zaplaceno kartou dne 12.9.2026. Dekujeme za nakup.",
     "receipt"),
    ("We are crediting your account with EUR 250.00 in respect of the damaged units supplied on "
     "invoice 4501. The amount will be offset against your next payment to us.", "credit_note"),
    ("Hi Marek, as agreed I'm sending my time for September: 42 hours at 85 EUR, so 3,570 EUR "
     "altogether. Bank details are the same as last time. The usual 14 days is fine. Thanks, Ola",
     "invoice"),
    ("TAX INVOICE 6602 / DELIVERY NOTE combined. Goods listed below were delivered 3 September and "
     "signed for by K. Nowak. Total including VAT: EUR 1,845.00. Terms: 30 days net. Late payment "
     "attracts statutory interest. Registered office: ul. Prosta 51, Warsaw. VAT ID PL5252445566. "
     "This document is issued under the framework agreement dated 2 January 2026 and supersedes "
     "any prior pricing communicated verbally.", "invoice"),
    ("NOTA DE CREDITO 77/2026. Anula parcialmente la factura 4410 por importe de 180,00 EUR "
     "debido a la devolucion de mercancia defectuosa.", "credit_note"),
    ("RELEVE DE COMPTE au 31 aout 2026. Facture 220: 450,00. Facture 231: 1 100,00. "
     "Solde du: 1 550,00 EUR. Ce document ne constitue pas une demande de paiement.", "statement"),
    ("INKOOPORDER 8841. Leverancier: Bolt Supplies BV. Gelieve 120 stuks artikel A-55 te leveren "
     "voor 15 oktober. Prijs per stuk EUR 12,50. Factuur graag apart sturen.", "purchase_order"),
    ("RICEVUTA DI PAGAMENTO. Abbiamo ricevuto EUR 640,00 in data 10 settembre a saldo della "
     "fattura 3391. Nulla piu e dovuto.", "receipt"),
    ("PROFORMA INVOICE 55. The goods listed were shipped on 1 September. This document serves as "
     "our formal request for payment of EUR 2,300.00 within 30 days of shipment.", "invoice"),
    ("PURCHA5E 0RDER 44lO. PLEA5E 5UPPLY 2OO UN1T5 T0 0UR WAREH0U5E BY l5 0CT0BER. N0 1NV01CE "
     "T0 BE RA15ED UNT1L DEL1VERY 15 C0NF1RMED.", "purchase_order"),
    ("Thanks for shopping with Northwind! Your order is on its way. FREE RETURNS FOR 90 DAYS. "
     "Refer a friend and you both get 10 EUR off. -- Payment of EUR 89.00 was successful on "
     "11 September, card ending 4412. Nothing further is owed on this order. -- Track your parcel "
     "in the app. Unsubscribe from marketing emails at any time.", "receipt"),
    ("ORDER FORM. Price: EUR 14,500.00. This becomes binding only when signed and returned by the "
     "customer. Valid for 30 days from the date shown.", "quote"),
    ("INVOICE SUMMARY - SEPTEMBER 2026. This is not a request for payment. Documents issued to "
     "you this month: 4410, 4433, 4501. Total issued: 2,700.00 EUR.", "statement"),
    ("Document 9911. Paid in full by bank transfer on 8 September. This document confirms that "
     "payment has been received and that nothing remains outstanding. Retain for your records.",
     "receipt"),
    ("SZAMLA 2026/554. Fizetendo osszeg: 250 000 Ft. Fizetesi hatarido: 2026.10.05. "
     "Teljesites idopontja: 2026.09.10.", "invoice"),
    ("\u9818\u53ce\u66f8 \u91d1\u984d 12,000\u5186 "
     "\u4e0a\u8a18\u6b63\u306b\u9818\u53ce\u3044\u305f\u3057\u307e\u3057\u305f\u3002", "receipt"),
    ("BESTELLUNG Nr. 7712. Bitte liefern Sie 50 Stueck Artikel B-12 bis zum 20. Oktober an unser "
     "Lager in Hamburg. Die Rechnung senden Sie bitte separat.", "purchase_order"),
    ("Following your complaint we are reducing invoice 4433 by EUR 90.00. Your revised balance on "
     "that document is EUR 810.00.", "credit_note"),
    ("Hi Ana, for the 3-day workshop I'd charge 4,800 EUR plus travel. Nothing is booked yet - let "
     "me know if that works and I'll hold the dates for you.", "quote"),
    ("Account 5512. Opening balance 0.00. Charges in period 1,800.00. Payments received -600.00. "
     "Closing balance 1,200.00.", "statement"),
    ("Hey - can you ship us another 200 of the A-55 before the 10th? Same terms as last time. "
     "We'll pay on the usual 30 days once it lands.", "purchase_order"),
    ("Against your purchase order 8841 we now bill 120 units at EUR 12.50, total EUR 1,500.00. "
     "Payment due 30 days from today.", "invoice"),
]
DOCS = list(r2.HARD) + EXTRA
MODELS = [JEV, "openai/gpt-oss-20b", "mistralai/ministral-8b-2512", "google/gemini-3.8-flash",
          "anthropic/claude-haiku-4.5", "anthropic/claude-opus-5"]
CLASS = {JEV: "typed decisions API", "openai/gpt-oss-20b": "open 20B",
         "mistralai/ministral-8b-2512": "open 8B", "google/gemini-3.8-flash": "small hosted",
         "anthropic/claude-haiku-4.5": "small frontier-family",
         "anthropic/claude-opus-5": "frontier - the marketing's denominator"}
LOCK = threading.Lock()
DONE = [0]


def post(url, body, timeout=300):
    req = urllib.request.Request(url, method="POST", data=json.dumps(body).encode(), headers=HDR)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "ms": int((time.time() - t0) * 1000), "d": json.load(r)}
    except urllib.error.HTTPError as e:
        return {"ok": False, "ms": int((time.time() - t0) * 1000),
                "error": e.read().decode("utf-8", "replace")[:160]}
    except Exception as exc:                                                  # noqa: BLE001
        return {"ok": False, "ms": int((time.time() - t0) * 1000), "error": repr(exc)[:160]}


def one(model, text, truth):
    """One document, one model. Retries once so a network blip is not scored as a miss."""
    r = {"ms": 0}
    for attempt in (0, 1):
        if model == JEV:
            r = post(DEC_URL, {"model": JEV, "state": {"document_text": text},
                               "questions": {"doc_type": {"type": "choice", "criteria": DOC_CRIT,
                                                          "instructions": INSTR}}})
            if r["ok"]:
                u = r["d"].get("usage") or {}
                a = r["d"]["answers"]["doc_type"]
                return {"picked": a["choice"], "truth": truth, "hit": a["choice"] == truth,
                        "conf": a.get("confidence"), "cost": u.get("cost") or 0.0, "ms": r["ms"],
                        "in": u.get("input_tokens") or 0, "out": u.get("output_tokens") or 0}
        else:
            p = ("Classify the document below using ONLY these definitions:\n%s\n\n%s\n\n"
                 'Document:\n%s\n\nAnswer with JSON only: {"type":"<one of: %s>"}'
                 % (CRIT_TEXT, INSTR, text, ", ".join(DOC_CRIT)))
            r = post(CHAT_URL, {"model": model, "max_tokens": 900, "temperature": 0,
                                "messages": [{"role": "system",
                                              "content": "Reply with ONLY minified JSON."},
                                             {"role": "user", "content": p}]})
            if r["ok"]:
                d, u = r["d"], (r["d"].get("usage") or {})
                txt = (d["choices"][0]["message"].get("content") or "").strip()
                if txt.startswith("```"):
                    txt = txt.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0]
                i, j = txt.find("{"), txt.rfind("}")
                try:
                    pick = str(json.loads(txt[i:j + 1]).get("type", "")).strip()
                except Exception:                                             # noqa: BLE001
                    return {"truth": truth, "error": "unparsable: " + txt[:60],
                            "cost": float(u.get("cost") or 0), "ms": r["ms"],
                            "in": u.get("prompt_tokens") or 0,
                            "out": u.get("completion_tokens") or 0}
                return {"picked": pick, "truth": truth, "hit": pick == truth,
                        "cost": float(u.get("cost") or 0), "ms": r["ms"],
                        "in": u.get("prompt_tokens") or 0, "out": u.get("completion_tokens") or 0}
        if attempt == 0:
            time.sleep(2.0)
    return {"truth": truth, "error": r.get("error"), "cost": 0.0, "ms": r["ms"], "in": 0, "out": 0}


def main():
    tasks = [(m, i, t, g) for m in MODELS for i, (t, g) in enumerate(DOCS)]
    print("%d documents x %d models = %d calls, concurrent.\n"
          % (len(DOCS), len(MODELS), len(tasks)))
    res = {m: [None] * len(DOCS) for m in MODELS}
    t0 = time.time()

    def work(task):
        m, i, t, g = task
        out = one(m, t, g)
        with LOCK:
            DONE[0] += 1
            if DONE[0] % 25 == 0:
                print("  %d/%d (%.0fs)" % (DONE[0], len(tasks), time.time() - t0), flush=True)
        return m, i, out

    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        for m, i, out in ex.map(work, tasks):
            res[m][i] = out
    print("\n  wall clock: %.0fs\n" % (time.time() - t0))

    agg = {}
    for m in MODELS:
        rows = res[m]
        ok = [r for r in rows if "picked" in r]
        cost = sum(r["cost"] for r in rows)
        agg[m] = {"class": CLASS[m], "hits": sum(r["hit"] for r in ok), "n": len(ok),
                  "errors": len(rows) - len(ok), "cost": cost,
                  "per_1k": (cost / len(ok)) * 1000 if ok else None,
                  "median_ms_concurrent": statistics.median([r["ms"] for r in ok]) if ok else None,
                  "in": sum(r["in"] for r in rows), "out": sum(r["out"] for r in rows),
                  "misses": [{"i": i, "want": r["truth"], "got": r.get("picked"),
                              "doc": DOCS[i][0][:70]}
                             for i, r in enumerate(rows) if "picked" in r and not r["hit"]],
                  "rows": rows}
    base = agg[JEV]["per_1k"]
    for m in MODELS:
        agg[m]["x_vs_jev"] = agg[m]["per_1k"] / base if base and agg[m]["per_1k"] else None

    print("%-30s %-38s %6s  %10s %10s" % ("model", "class", "acc", "$/1k dec", "x vs Jev"))
    print("-" * 100)
    for m in sorted(MODELS, key=lambda k: agg[k]["per_1k"] or 0):
        a = agg[m]
        print("%-30s %-38s %2d/%-3d  $%9.4f %9.2fx%s"
              % (m, a["class"], a["hits"], a["n"], a["per_1k"], a["x_vs_jev"],
                 "  (%d unusable)" % a["errors"] if a["errors"] else ""))

    print("\nWhat each model got WRONG:")
    for m in MODELS:
        a = agg[m]
        print("\n  %s - %d miss(es)" % (m, len(a["misses"])))
        for x in a["misses"]:
            print("     #%-2d want %-14s got %-14s | %s" % (x["i"], x["want"], x["got"], x["doc"]))

    print("\nDocuments that beat at least one model:")
    for i, (text, truth) in enumerate(DOCS):
        wrong = [m.split("/")[-1] for m in MODELS
                 if "picked" in res[m][i] and not res[m][i]["hit"]]
        if wrong:
            print("  #%-2d want %-14s missed by %d: %s" % (i, truth, len(wrong), ", ".join(wrong)))
            print("      %s" % text[:100].replace("\n", " "))

    j = agg[JEV]
    print("\n  Jev billed %d input and %d output tokens across %d decisions (output priced $0)."
          % (j["in"], j["out"], j["n"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(agg, indent=1, default=str), encoding="utf-8")
    print("  written: %s" % OUT)


if __name__ == "__main__":
    main()
