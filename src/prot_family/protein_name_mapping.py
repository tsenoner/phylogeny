import re


def dpp_protein_mapping(name):
    # Define regular expressions for each group
    patterns = {
        "Cathepsin C": r"^Cathepsin C$|^Dipeptidyl peptidase 1$",
        "DPP3": r"^Dipeptidyl peptidase 3$",
        "DPP4": r"DPP4|(putative )?(venom )?dipeptidyl[- ]?peptidase (IV|4)(?!-related)",
        "DPP6": r"DPP6|dipeptidyl[- ]?(amino)?peptidase[- ](like )?(protein )?6",
        "DPP7": r"^Dipeptidyl peptidase (2|7)$",
        "DPP8": r"DPP8|(putative )?dipeptidyl[- ]?peptidase 8",
        "DPP9": r"DPP9|(putative )?dipeptidyl[- ]?peptidase 9",
        "DPP10": r"DPP10|DPPY|(Putative )?(Inactive )?Dipeptidyl[ -]?peptidase( like)?[ -]?10",
        "FAP": r"FAP|Fibroblast activation (protein|factor alpha)|Seprase",
    }

    # Check each pattern to find a match
    for group, pattern in patterns.items():
        if re.search(pattern, name, re.IGNORECASE):
            return group

    return "Other"
