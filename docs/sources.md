# Sources

This is the knowledge base the chatbot answers from. It holds five documents, which I fetched and loaded into a Pinecone index named `mpesa-assistant`. The bot is meant to answer only from these documents. Every test in this project depends on what is in them, so this page records exactly what they are.

## Summary

| Slug | Document | Type | Characters | Chunks |
|---|---|---|---|---|
| wikipedia-m-pesa | Wikipedia, "M-Pesa" | Web page (Wikipedia API, plain text) | 21,581 | 32 |
| wikipedia-safaricom | Wikipedia, "Safaricom" | Web page (Wikipedia API, plain text) | 17,358 | 28 |
| wikipedia-central-bank-of-kenya | Wikipedia, "Central Bank of Kenya" | Web page (Wikipedia API, plain text) | 3,545 | 5 |
| cbk-nps-act | National Payment System Act, No. 39 of 2011 | PDF from the Central Bank of Kenya | 48,520 | 59 |
| cbk-nps-regulations-2014 | National Payment System Regulations, 2014 | PDF from the Central Bank of Kenya | 99,247 | 121 |

Total: 245 chunks. Each chunk is up to 1,000 characters, with 150 characters of overlap between neighbouring chunks.

## Where each document comes from

- **Wikipedia, M-Pesa:** https://en.wikipedia.org/wiki/M-Pesa
- **Wikipedia, Safaricom:** https://en.wikipedia.org/wiki/Safaricom
- **Wikipedia, Central Bank of Kenya:** https://en.wikipedia.org/wiki/Central_Bank_of_Kenya
- **National Payment System Act:** https://www.centralbank.go.ke/wp-content/uploads/2016/08/NATIONAL-PAYMENT-SYSTEM-ACT-No-39-of-2011-21.pdf
- **National Payment System Regulations, 2014:** https://www.centralbank.go.ke/images/docs/legislation/NPSRegulations2014.pdf

## Licences and credit

- **Wikipedia text** is available under the Creative Commons Attribution-ShareAlike licence (CC BY-SA). The text is credited to the Wikipedia articles listed above and their contributors. I fetched it through the Wikipedia API with a User-Agent that names this project.
- **The Act and the Regulations** are published by the Central Bank of Kenya. I did not find a licence statement on the PDFs. I use them to test a chatbot, I link to the originals, and I do not publish the extracted text: the folder `data/` is gitignored, so the text stays on my machine.

## What each document is, and what version

- **The Act is the 2011 text as originally enacted.** It is the copy the Central Bank of Kenya hosts, and it is not the current consolidated law. Amendments made since 2011 are not in it, so some rules may have changed. Where the bot repeats a rule from the Act, I treat it as correct if it matches this text, and I do not claim it is the law today.
- **The Regulations are the 2014 Gazette text** (Kenya Subsidiary Legislation, 2014).
- **The Wikipedia pages are snapshots** taken when I fetched them. They can change after that, and parts of them are already out of date. For example, the M-Pesa article says Kenya does not have a data protection law, while the Central Bank article mentions a Data Protection Act. The tests follow the text in the knowledge base, not the live page.

## Sources I did not use, and why

- **Safaricom's website (safaricom.co.ke):** it blocks automated access (a bot challenge page), so I could not fetch tariffs or customer help pages. I did not try to get around it. Because of this, the bot is not a customer-help assistant, and questions about current tariffs are tested as out-of-scope questions.
- **Kenya Law (new.kenyalaw.org):** it also blocks automated access (an empty response instead of the page). I did not get around it and used the Central Bank's PDFs instead.

## Known faults in the text

These come from the PDF extraction, not from the original documents. I cleaned the obvious page headers and footers, but the text is not perfect.

- **Stray spaces and wrong characters from OCR:** for example "comme nce", "regard s" and "ser vice". Quote marks appear as odd glyphs (`―bank‖`).
- **Margin headings inside sentences:** a heading from the page margin sometimes lands in the middle of a sentence. In regulation 40(5), the heading "Resolution of complaints." sits between "not satisfied with the decision of the" and "payment service provider regarding a complaint". The wording is intact apart from that heading.
- **Page headers removed by a rule:** lines such as "NO. 39 National Payment System" and "Kenya Subsidiary Legislation, 2014" were removed with a pattern. One running header, "NO. 39 National Payment System 27", still appears inside the text of section 26 in the Act.
- **Wikipedia plain text:** headings appear as `== Heading ==`, and reference markers are removed.

## How ground truth uses these sources

The 40 fact and rule rows in `docs/03-ground-truth.md` (GT01 to GT40) each name their source (the document and the section), and I checked each one against the original PDF or page, not against the extracted text. The other 20 rows (GT41 to GT60: refusals, attacks and robustness, Swahili, bias pairs, and dated content) test behaviour rather than facts from the sources, so there is no original to check them against.
