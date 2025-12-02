from typing import Optional
import re
import requests
from bs4 import BeautifulSoup, Tag
from rdflib import Graph, Namespace, RDF, RDFS, Literal

HSR = Namespace("http://example.org/hsr-ontology#")


def normalize(term: str) -> str:
    """Normalize a string to a safe fragment for IRIs."""
    if not term:
        return ""
    s = term.replace("The ", "").strip()
    s = s.replace("%", "_percent")
    s = re.sub(r'[^0-9A-Za-z_]', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')


def _text_from_first_link(td: Optional[Tag]) -> Optional[str]:
    if td is None:
        return None
    a = td.find("a")
    if a and a.text and a.text.strip():
        return a.text.strip()
    # fallback: other text
    txt = td.get_text(separator=" ", strip=True)
    return txt or None


def _href_from_first_link(td: Optional[Tag]) -> Optional[str]:
    if td is None:
        return None
    a = td.find("a", href=True)
    if a:
        return a["href"].strip()
    return None


def _create_team_instance(graph: Graph, page_label: str, subgroup: str, idx: int, source_url: Optional[str]):
    """
    Create a new Team instance URI and add basic metadata (type, label, sourceURL).
    Returns the team URI.
    """
    team_label = f"{page_label} — {subgroup}" if subgroup else page_label
    if idx > 0:
        team_label = f"{team_label} ({idx})"
    team_norm = normalize(team_label)
    team_uri = HSR[team_norm]
    graph.add((team_uri, RDF.type, HSR.Team))
    graph.add((team_uri, RDFS.label, Literal(team_label)))
    if source_url:
        graph.add((team_uri, HSR.sourceURL, Literal(source_url)))
    return team_uri


def parse_teams(graph: Graph, url: str):
    """
    Parse team tables from a page like the sample and add Team instances to the graph.

    Behavior:
    - Finds section headers (h4 with class containing 'a-header--4' or any h4) and then
      the following <table> elements that define teams for that header.
    - Each table can contain multiple subgroups (rows with a single <th colspan="4">, e.g. "F2P",
      "Hypercarry Team"). The parser treats each subgroup as a separate team (if there are
      multiple member rows for the subgroup, it will create separate team instances with index suffix).
    - For each member row it maps columns to roles using the header row (e.g. "DPS", "Support", "Support", "Sustain")
      and creates role-specific triples:
         team hsr:hasDPS <char>
         team hsr:hasSupport <char>
         team hsr:hasSustain <char>
      (multiple supports allowed).
    - Members are referenced by normalized HSR URI (HSR:Normalize(Name)). If the character already exists
      in the graph, the same URI will be used.
    - team and member labels are added where possible (team label always, members referenced by URI only).
    """
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; team-parser/1.0)"
    })
    resp = s.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")

    # find candidate headers (h4) that name team page sections
    headers = soup.find_all(lambda t: t.name == "h4" and (t.get_text(strip=True)))
    if not headers:
        # fallback: parse all tables that look like team tables
        tables = soup.find_all("table", class_=lambda v: v and "a-table" in v)
        page_label = "Teams"
        for table in tables:
            _parse_team_table(graph, table, page_label, url)
        return

    for h in headers:
        page_label = h.get_text(strip=True)
        # the table(s) for this header are usually the next sibling table(s)
        node = h
        while True:
            node = node.find_next_sibling()
            if node is None:
                break
            if isinstance(node, Tag) and node.name == "table":
                _parse_team_table(graph, node, page_label, url)
                # break if you expect only one table per header; but continue to handle multiple tables
            # stop if next header reached
            if isinstance(node, Tag) and node.name in ("h2", "h3", "h4"):
                break


def _parse_team_table(graph: Graph, table: Tag, page_label: str, source_url: Optional[str]):
    """
    Parse a single <table> that contains one or more subgroup teams.
    The table format expected (based on your sample):
      - a row with <th colspan="4">Subgroup title (e.g. "F2P")</th>
      - a row with role headers (DPS / Support / Support / Sustain)
      - a row with 4 <td> each containing a link to character
    There may be multiple subgroup blocks in one table.
    """
    tbody = table.find("tbody") or table
    rows = tbody.find_all("tr", recursive=False)

    current_subgroup = ""
    team_counter = {}  # subgroup -> count for indexing multiple member rows
    i = 0
    while i < len(rows):
        tr = rows[i]
        # detect subgroup title row: a single <th colspan="..."> with text
        ths = tr.find_all("th")
        if ths and len(ths) == 1 and (ths[0].get("colspan") or "").strip():
            subgroup_text = ths[0].get_text(separator=" ", strip=True)
            current_subgroup = subgroup_text
            # next row should be the role header (skip), then a member row(s)
            i += 1
            # skip role header if present
            if i < len(rows):
                next_tr = rows[i]
                # role header typically has multiple <th> like DPS/Support...
                if next_tr.find_all("th") and len(next_tr.find_all("th")) >= 2:
                    i += 1
            # now parse one or more member rows until we hit another subgroup or end
            member_row_idx = 0
            while i < len(rows):
                look = rows[i]
                # stop if next subgroup title detected
                look_ths = look.find_all("th")
                if look_ths and len(look_ths) == 1 and (look_ths[0].get("colspan") or "").strip():
                    break
                # expect this to be a member row with <td> columns
                tds = look.find_all("td")
                if not tds:
                    i += 1
                    continue
                # ensure we have role columns (could be 4 or less)
                cols = [td for td in tds]
                # create a team instance for this member_row
                count = team_counter.get(current_subgroup, 0)
                team_uri = _create_team_instance(graph, page_label, current_subgroup, count, source_url)
                team_counter[current_subgroup] = count + 1

                # role order is inferred from header pattern: try to detect role names from previous header row
                # fallback to positions: [DPS, Support, Support, Sustain]
                role_names = ["DPS", "Support", "Support", "Sustain"]
                # If there is an explicit role header row right before the member row, parse it
                # (we already skipped it above, but keep fallback)
                # assign members to roles
                for col_idx, td in enumerate(cols):
                    actor_name = _text_from_first_link(td)
                    actor_href = _href_from_first_link(td)
                    if not actor_name:
                        continue
                    actor_norm = normalize(actor_name)
                    actor_uri = HSR[actor_norm]
                    # add optional label for character if not present
                    existing_label = list(graph.objects(actor_uri, RDFS.label))
                    if not existing_label:
                        graph.add((actor_uri, RDFS.label, Literal(actor_name)))
                    # add sourceURL for the character link (optional)
                    if actor_href:
                        graph.add((actor_uri, HSR.sourceURL, Literal(actor_href)))
                    # add role-specific triple
                    role = role_names[col_idx] if col_idx < len(role_names) else f"Role_{col_idx+1}"
                    prop = None
                    if role.lower().startswith("dps"):
                        prop = HSR.hasDPS
                    elif role.lower().startswith("support"):
                        prop = HSR.hasSupport
                    elif role.lower().startswith("sustain"):
                        prop = HSR.hasSustain
                    else:
                        # generic member property
                        prop = HSR.hasMember
                    graph.add((team_uri, prop, actor_uri))
                member_row_idx += 1
                i += 1
            continue
        else:
            # If table doesn't use subgroup <th> rows (rare), attempt to parse straightforwardly:
            # look for a role header row followed by one or more member rows
            # detect role header
            if tr.find_all("th") and len(tr.find_all("th")) >= 2:
                # role header found -> parse next row as member row
                i += 1
                if i < len(rows):
                    member_tr = rows[i]
                    tds = member_tr.find_all("td")
                    if tds:
                        # create a team using page_label only
                        count = team_counter.get(page_label, 0)
                        team_uri = _create_team_instance(graph, page_label, "", count, source_url)
                        team_counter[page_label] = count + 1
                        role_names = [th.get_text(strip=True) for th in tr.find_all("th")]
                        for col_idx, td in enumerate(tds):
                            actor_name = _text_from_first_link(td)
                            actor_href = _href_from_first_link(td)
                            if not actor_name:
                                continue
                            actor_norm = normalize(actor_name)
                            actor_uri = HSR[actor_norm]
                            existing_label = list(graph.objects(actor_uri, RDFS.label))
                            if not existing_label:
                                graph.add((actor_uri, RDFS.label, Literal(actor_name)))
                            if actor_href:
                                graph.add((actor_uri, HSR.sourceURL, Literal(actor_href)))
                            # map role by header text
                            r = role_names[col_idx] if col_idx < len(role_names) else "Member"
                            prop = HSR.hasMember
                            if "DPS" in r.upper():
                                prop = HSR.hasDPS
                            elif "SUPPORT" in r.upper():
                                prop = HSR.hasSupport
                            elif "SUSTAIN" in r.upper():
                                prop = HSR.hasSustain
                            graph.add((team_uri, prop, actor_uri))
                i += 1
                continue
            # else skip row
            i += 1
            continue