"""Kenya/Africa-focused evidence seed corpus and seeding utility.

All statistics are sourced from named, publicly verifiable organisations.
The ``source`` field in each chunk's metadata records the originating report
or body so the claim_verifier node can surface attributions when flagging.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Seed corpus — 18 chunks across 6 topics (framing + stat + example per topic)
# Topics: mental_health, gender_equality, social_media, education_access,
#         leadership, climate
# ---------------------------------------------------------------------------

SEED_CORPUS: list[dict[str, Any]] = [
    # ── 1. MENTAL HEALTH ────────────────────────────────────────────────────
    {
        "id": "mh-framing-ke",
        "text": (
            "Mental health is a national development issue in Kenya and across Africa, "
            "not a private struggle. The region carries a disproportionate share of the "
            "global mental health burden while receiving the least investment in care. "
            "Stigma, poverty, and a critical shortage of trained professionals combine "
            "to leave the majority of people with mental health conditions without any "
            "support — making community-based solutions and policy reform essential."
        ),
        "metadata": {
            "topic": "mental_health",
            "chunk_type": "framing",
            "source": "WHO Mental Health Atlas 2020; Kenya Mental Health Policy 2015–2030",
            "region": "Kenya/Africa",
        },
    },
    {
        "id": "mh-stat-ke",
        "text": (
            "The WHO Mental Health Atlas 2020 reported that the African region has just "
            "1.4 mental health workers per 100,000 population, compared to 50 per 100,000 "
            "in Europe. Kenya's Mental Health Policy 2015–2030 acknowledges that at least "
            "25% of outpatients in Kenyan health facilities present with a mental health "
            "condition, yet fewer than 1 in 10 receive any form of treatment."
        ),
        "metadata": {
            "topic": "mental_health",
            "chunk_type": "stat",
            "source": "WHO Mental Health Atlas 2020; Kenya Mental Health Policy 2015–2030",
            "region": "Kenya/Africa",
        },
    },
    {
        "id": "mh-example-ke",
        "text": (
            "Kenya's county devolution system has created openings for community-based "
            "mental health integration. Nakuru and Kisumu counties have piloted task-shifting "
            "programmes that train community health workers to screen for depression and "
            "anxiety, reducing pressure on overstretched specialists. At the continental "
            "level, the Africa Mental Health Research and Training Foundation (AMHRTF) "
            "advocates for ring-fenced mental health budgets within national health plans."
        ),
        "metadata": {
            "topic": "mental_health",
            "chunk_type": "example",
            "source": "AMHRTF; Kenya County Health Reports 2022",
            "region": "Kenya/Africa",
        },
    },

    # ── 2. GENDER EQUALITY ──────────────────────────────────────────────────
    {
        "id": "ge-framing-ke",
        "text": (
            "Kenya's Constitution 2010 is one of the most progressive gender-equality "
            "frameworks in Africa: Article 27 guarantees freedom from discrimination on "
            "the basis of sex, and Article 81(b) establishes the two-thirds gender rule "
            "for elective and appointive bodies. Yet the gap between constitutional promise "
            "and lived reality — in parliament, in wages, and in freedom from violence — "
            "remains wide and demands sustained structural action beyond legal text."
        ),
        "metadata": {
            "topic": "gender_equality",
            "chunk_type": "framing",
            "source": "Constitution of Kenya 2010, Articles 27 and 81",
            "region": "Kenya",
        },
    },
    {
        "id": "ge-stat-ke",
        "text": (
            "Following Kenya's 2022 general election, women held 23% of National Assembly "
            "seats — below the constitutional two-thirds gender rule and below the African "
            "Union's 50/50 parity target. The Kenya National Bureau of Statistics Gender "
            "Statistics Report 2021 found women earn on average 32% less than men in formal "
            "employment. The Kenya Demographic and Health Survey 2022 recorded that 45% of "
            "Kenyan women have experienced gender-based violence."
        ),
        "metadata": {
            "topic": "gender_equality",
            "chunk_type": "stat",
            "source": "IEBC 2022; KNBS Gender Statistics Report 2021; KDHS 2022",
            "region": "Kenya",
        },
    },
    {
        "id": "ge-example-ke",
        "text": (
            "Kenya enacted the Anti-FGM Act in 2011, criminalising female genital mutilation "
            "and establishing the Anti-FGM Board. Prevalence has since declined from 38% "
            "(1998 KDHS) to 15% (2022 KDHS), demonstrating that legislation combined with "
            "community engagement — including the Maasai Women Development Organisation's "
            "alternative rite of passage programme — can shift deep-rooted practices. "
            "Across the continent, Rwanda's constitutional gender quotas have put women in "
            "61% of parliamentary seats, the highest proportion in the world."
        ),
        "metadata": {
            "topic": "gender_equality",
            "chunk_type": "example",
            "source": "KDHS 1998 & 2022; Anti-FGM Board Kenya; Rwanda Parliament 2024",
            "region": "Kenya/Africa",
        },
    },

    # ── 3. SOCIAL MEDIA & DIGITAL ───────────────────────────────────────────
    {
        "id": "sm-framing-ke",
        "text": (
            "Kenya is East Africa's digital economy hub — Nairobi's 'Silicon Savannah' "
            "hosts over 200 active tech startups and produced globally significant "
            "innovations like M-Pesa. For millions of Kenyan youth, smartphones and social "
            "media are the primary means of news consumption, civic participation, and "
            "economic opportunity. Yet the digital gender gap and urban-rural divide mean "
            "these opportunities are not distributed equally, and the harms of social "
            "media — misinformation, online gender-based violence, comparison culture — "
            "fall disproportionately on women and girls."
        ),
        "metadata": {
            "topic": "social_media",
            "chunk_type": "framing",
            "source": "GSMA Mobile Economy Sub-Saharan Africa 2023; iHub Nairobi reports",
            "region": "Kenya",
        },
    },
    {
        "id": "sm-stat-ke",
        "text": (
            "The Communications Authority of Kenya reported 67% internet penetration as "
            "of 2023, with mobile phones as the access device for over 95% of internet "
            "users. However, the Alliance for Affordable Internet (A4AI) found that Kenyan "
            "women are 37% less likely than men to own a mobile phone and 52% less likely "
            "to use mobile internet — one of the largest gender digital gaps in East Africa."
        ),
        "metadata": {
            "topic": "social_media",
            "chunk_type": "stat",
            "source": "Communications Authority of Kenya 2023; A4AI Gender Digital Divide Report 2022",
            "region": "Kenya",
        },
    },
    {
        "id": "sm-example-ke",
        "text": (
            "M-Pesa, launched by Safaricom in Kenya in 2007, is the world's most successful "
            "mobile money platform, processing transactions equivalent to over 50% of Kenya's "
            "GDP annually. It has given millions of unbanked Kenyans — particularly women in "
            "rural areas — access to savings, credit, and business payments for the first time. "
            "Digital literacy programmes by Eneza Education have delivered curriculum content "
            "to over 3 million learners across Kenya via SMS, bridging the access gap without "
            "requiring smartphones or stable internet."
        ),
        "metadata": {
            "topic": "social_media",
            "chunk_type": "example",
            "source": "Safaricom Annual Report 2023; Eneza Education impact reports",
            "region": "Kenya",
        },
    },

    # ── 4. EDUCATION ACCESS ─────────────────────────────────────────────────
    {
        "id": "ed-framing-ke",
        "text": (
            "Education is the most powerful equaliser — and Kenya has demonstrated both "
            "the gains and the limits of policy-driven access. Free Primary Education "
            "(2003) and Free Day Secondary Education (2008) drove dramatic enrolment "
            "increases. Yet completion, quality, and equity remain unfinished work: "
            "girls from arid and semi-arid counties, girls from low-income urban "
            "households, and girls in communities with high rates of early marriage "
            "still face structural barriers that legislation alone has not solved."
        ),
        "metadata": {
            "topic": "education_access",
            "chunk_type": "framing",
            "source": "Kenya Basic Education Act 2013; UNESCO Education Progress Report 2023",
            "region": "Kenya",
        },
    },
    {
        "id": "ed-stat-ke",
        "text": (
            "Kenya achieved near gender parity in primary school net enrolment — a ratio "
            "of 0.98 girls to every boy — according to the Kenya Economic Survey 2023. "
            "However, the secondary completion gap widens: only 54% of girls complete "
            "secondary school compared to 62% of boys. In counties like Garissa and "
            "Mandera, girls' secondary enrolment falls below 30%. UNESCO estimates that "
            "10 million children across Africa are kept out of school by period poverty alone."
        ),
        "metadata": {
            "topic": "education_access",
            "chunk_type": "stat",
            "source": "Kenya Economic Survey 2023; UNESCO 2022; UNICEF period poverty reports",
            "region": "Kenya/Africa",
        },
    },
    {
        "id": "ed-example-ke",
        "text": (
            "Kenya's Sanitary Towels Programme, established under the Basic Education Act, "
            "distributes free sanitary products to girls in public schools — directly "
            "addressing one of the leading causes of absenteeism and dropout. The Equity "
            "Bank Wings to Fly scholarship programme has put over 25,000 vulnerable "
            "students — the majority girls from rural Kenya — through secondary school "
            "and university since its launch in 2012. Both programmes show that targeted, "
            "structural interventions outperform awareness campaigns alone."
        ),
        "metadata": {
            "topic": "education_access",
            "chunk_type": "example",
            "source": "Ministry of Education Kenya; Equity Bank Wings to Fly 2023 Impact Report",
            "region": "Kenya",
        },
    },

    # ── 5. WOMEN'S LEADERSHIP ───────────────────────────────────────────────
    {
        "id": "ld-framing-ke",
        "text": (
            "Africa has produced some of the world's most consequential women leaders — "
            "and Kenya stands at the centre of that story. From Wangari Maathai's Nobel "
            "Peace Prize to Martha Karua's historic vice-presidential candidacy in 2022, "
            "Kenyan women have repeatedly broken barriers in politics, science, and civil "
            "society. The challenge now is to move from celebrating individual firsts to "
            "building systems that make women's leadership the expected outcome, not the "
            "exceptional one."
        ),
        "metadata": {
            "topic": "leadership",
            "chunk_type": "framing",
            "source": "African Union Gender Policy 2009; Kenya National Gender and Equality Commission",
            "region": "Kenya/Africa",
        },
    },
    {
        "id": "ld-stat-ke",
        "text": (
            "Sub-Saharan Africa has 26.6% women in parliament according to IPU "
            "(Inter-Parliamentary Union) data for 2024, masking vast national disparities: "
            "Rwanda leads the world at 61% while Kenya sits at 23%. At the corporate "
            "level, the Kenya Private Sector Alliance reports that women hold just 19% of "
            "board seats in Kenya's top 50 companies and 11% of CEO positions — a "
            "structural underrepresentation that costs organisations measurable performance."
        ),
        "metadata": {
            "topic": "leadership",
            "chunk_type": "stat",
            "source": "IPU Parline Database 2024; Kenya Private Sector Alliance 2023",
            "region": "Kenya/Africa",
        },
    },
    {
        "id": "ld-example-ke",
        "text": (
            "Wangari Maathai (1940–2011) founded the Green Belt Movement in 1977, "
            "mobilising rural Kenyan women to plant over 51 million trees while organising "
            "for democracy and women's rights — earning the 2004 Nobel Peace Prize, the "
            "first African woman to receive it. Martha Karua became Kenya's first female "
            "presidential running mate in 2022. At the continental level, Ellen Johnson "
            "Sirleaf of Liberia became Africa's first elected female head of state in 2006, "
            "and Ngozi Okonjo-Iweala has served as WTO Director-General since 2021."
        ),
        "metadata": {
            "topic": "leadership",
            "chunk_type": "example",
            "source": "Nobel Prize Foundation 2004; Green Belt Movement; WTO official records",
            "region": "Kenya/Africa",
        },
    },

    # ── 6. CLIMATE & ENVIRONMENT ────────────────────────────────────────────
    {
        "id": "cl-framing-ke",
        "text": (
            "Kenya and the African continent face a profound climate injustice: Africa "
            "contributes less than 4% of global greenhouse gas emissions yet bears some "
            "of the heaviest costs — erratic rainfall, prolonged droughts, rising coastal "
            "sea levels, and the collapse of smallholder agriculture that sustains most "
            "Kenyan households. For Kenya, climate is not an abstract future threat; it "
            "is a present-day driver of food insecurity, conflict over water and pasture, "
            "and displacement of communities."
        ),
        "metadata": {
            "topic": "climate",
            "chunk_type": "framing",
            "source": "IPCC Sixth Assessment Report 2022; African Development Bank Climate Reports",
            "region": "Kenya/Africa",
        },
    },
    {
        "id": "cl-stat-ke",
        "text": (
            "Kenya generates over 90% of its electricity from renewable sources — "
            "geothermal, wind, solar, and hydro — making it one of the world's greenest "
            "electricity grids. The Lake Turkana Wind Power Project, operational since "
            "2019, is Africa's largest wind farm at 310 MW capacity. Despite this clean "
            "energy leadership, the World Bank estimates the 2022 drought cost Kenya's "
            "economy 2.8% of GDP, and climate projections suggest an additional 2.5 million "
            "Kenyans could fall below the poverty line by 2030 due to climate impacts."
        ),
        "metadata": {
            "topic": "climate",
            "chunk_type": "stat",
            "source": "KPLC Renewable Energy Report 2023; World Bank Kenya Economic Update 2023",
            "region": "Kenya",
        },
    },
    {
        "id": "cl-example-ke",
        "text": (
            "Wangari Maathai's Green Belt Movement is the defining African example of "
            "grassroots environmental leadership: Kenyan women planting 51 million trees "
            "as acts of political resistance, community resilience, and ecological "
            "restoration. Kenya committed to a 32% emissions reduction by 2030 under its "
            "Nationally Determined Contribution to the Paris Agreement. Youth-led movements "
            "like Fridays for Future Kenya, led by climate activist Elizabeth Wathuti, have "
            "brought African voices to the global climate conversation at COP summits."
        ),
        "metadata": {
            "topic": "climate",
            "chunk_type": "example",
            "source": "Green Belt Movement; Kenya NDC 2020; Elizabeth Wathuti public record",
            "region": "Kenya/Africa",
        },
    },
]


def seed_if_empty() -> int:
    """Seed the Chroma collection with the Kenya/Africa corpus if it is empty.

    Idempotent: skips seeding if the collection already contains documents.
    Designed to be called once at application startup (e.g. via
    ``@st.cache_resource``).

    Returns:
        Number of chunks in the collection after the operation.

    Example:
        >>> n = seed_if_empty()
        >>> n >= 18
        True
    """
    from pageant_assistant.rag.store import collection_size, add_chunks  # local import avoids circular deps

    size = collection_size()
    if size > 0:
        logger.info(
            "seed_if_empty: collection already has %d chunk(s) — skipping", size
        )
        return size

    logger.info(
        "seed_if_empty: collection empty — seeding %d Kenya/Africa chunks …",
        len(SEED_CORPUS),
    )
    chunks = [
        {"id": c["id"], "text": c["text"], "metadata": c["metadata"]}
        for c in SEED_CORPUS
    ]
    add_chunks(chunks)
    final_size = collection_size()
    logger.info(
        "seed_if_empty: seeding complete — %d chunk(s) now in collection", final_size
    )
    return final_size
