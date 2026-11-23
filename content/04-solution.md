## The solution: audit the score, fix its data, explain it to families

The proposal does not replace the DFC or let AI decide who receives a benefit. It adds three AI tools around the existing rule. Each targets a different failure: nobody knows how often the score is wrong; wrong records lower scores; families cannot see or contest their score.

|  | Independent audit | Data-quality flags | Citizen explainer |
| --- | --- | --- | --- |
| What it does | Measures how often the DFC category disagrees with measured poverty, by region and family type | Flags records that look outdated or wrong before they affect a score | Explains a family's score in Kazakh or Russian and how to correct or appeal it |
| AI used | Supervised ML trained on Household Budget Survey data, compared with DFC categories | Record linkage and anomaly detection (e.g. a car with no tax or insurance for years) | Language model answering only from the published rule and the family's own record (retrieval) |
| Run by | Supreme Audit Chamber or a university, independent of the Ministry | Ministry caseworkers inside the DFC | Ministry, through eGov Mobile |
| Reaches | Parliament, Ministry, public (yearly report) | Families who may be misclassified | Every family told its category |
| Human control | Auditors interpret; no individual decisions | A caseworker confirms every flag; family is told | Never decides; one tap to a human officer |

Design rule: AI is never on the path that removes a benefit. A data-quality flag can only trigger a review that may restore support. This avoids the pattern of the Dutch SyRI system, where data-linking was used to hunt for fraud.

The explainer could run on ISSAI KAZ-LLM, the open-source model released by Nazarbayev University's Institute of Smart Systems and AI in December 2024 for Kazakh, Russian and English (ISSAI, 2024). A local model keeps citizens' data inside Kazakhstan.

## Real cases this builds on

### Togo · Novissi

Deployed nationally to pay COVID-19 relief; independently evaluated in Nature. ML cut exclusion errors by 4–21% against geographic targeting, but did worse than a full registry would have (Aiken et al., 2022). Lesson for Kazakhstan: use ML to audit a registry, not to replace it.

### United Kingdom · GOV.UK Chat

In two public pilots over 18 months, more than 10,000 users asked about 26,000 questions on services including benefits. Measured accuracy rose from 76% to 90%; the tool answers only from official guidance, shows source links and warnings, and users asked for a route to a human advisor (Government Digital Service, 2026). Lesson: an explainer must cite its source and hand over to people. Note that these figures are reported by the government team itself.

### Los Angeles

A randomised experiment shows accurate chatbots help caseworkers, while wrong ones do real harm (Gosciak et al., 2026).

### SyRI and Robodebt

SyRI (Hague District Court, 2020) and Robodebt, which issued around 470,000 wrongful debts before it ended in 2020 (Jurist, 2023; Royal Commission, 2023), show what happens when automated welfare decisions lack transparency and human review.

## Optional: test the explainer yourself

Give a real model (KAZ-LLM, Claude or ChatGPT) the published points rule and ten archetype families whose correct category you have calculated. Ask in Kazakh and Russian: "What category is this family, and why?" Record how many categories and explanations it gets right. [MISSING: optional experiment results.] If it makes mistakes, that is

## The bill

### Environmental

The audit runs a few times a year on survey-sized data and needs little compute. Data-quality flags run on registry records and are also light. The explainer is the main load: a language model answering questions from up to 6.2 million families, mostly in the months after categories are announced. Kazakhstan's electricity comes largely from coal, so this load has a carbon cost; a smaller local model such as the 8-billion-parameter KAZ-LLM, run in a domestic data centre, would cost far less energy than a 70-billion-parameter one. [Check the coal share with KEGOC or IEA data before publishing.]

### Economic

Costs are building the tools, hosting, data-sharing agreements, the independent audit team, caseworker time to review flags, and maintenance every time the rule changes. These would be small next to the 700 billion tenge the government expects to save in 2027. Who profits matters: the DFC is run by the state company National Information Technologies with UNDP (ITU, n.d.), and an outsourced AI contract risks vendor lock-in. The cheapest alternative, which AI must beat, is to publish the full points table, staff a review desk and publish appeals statistics.

### Labor

Caseworkers gain new work: reviewing flags and handling escalations from the explainer. That is a cost, but also the human check the system needs. Hidden labor includes cleaning registry data, translating and testing Kazakh answers, and labelling records to train the flag models. Front-line staff risk deskilling if they defer to the machine; the Los Angeles study shows people follow wrong suggestions too (Gosciak et al., 2026).

### Governance

Kazakhstan's Law No. 230-VIII "On Artificial Intelligence", signed on 17 November 2025 and in force since 18 January 2026, sorts AI systems by risk and gives people the right to know about automated processing, to object to it, and to an explanation (EY Kazakhstan, 2025; Legal500, 2025). An AI tool touching welfare eligibility would likely count as high-risk, which points to independent audit. The bigger risk is surveillance creep: adding bank data and AI flags to a database on 20 million people builds capacity that could be used for control rather than support. Control must sit with an independent auditor, with published results.

### Data ethics

The audit needs survey data linked to DFC categories, which requires a legal basis and strict anonymisation. The flags and the explainer use data the state already holds, but families must be told and able to correct it. Proxy discrimination is a real risk: indicators such as region, housing type or family size can stand in for ethnicity or rural poverty. Every model must report error rates by group.

## Citizen explainer scripts

### Why is this family in category B?

The rule works in steps. For this family, every income band below four subsistence minimums leaves them in category C. Cross 203,404 tenge per person and their income points jump from 400 to 620, the score rises from 650 to 870, and the family moves into

### What if a record is incorrect?

A caseworker confirms every flag; family is told.

### Who can I speak to?

One tap to a human officer.
