import pytinytex


def test_parse_tlmgr_list_machine_readable():
    output = (
        "i collection-basic: 1 file, 4k\n"
        "i amsmath: 12345 56k\n"
        "  booktabs: 67890 12k\n"
    )
    result = pytinytex._parse_tlmgr_list(output)
    assert len(result) == 3
    assert result[0]["name"] == "collection-basic"
    assert result[0]["installed"] is True
    assert result[1]["name"] == "amsmath"
    assert result[1]["installed"] is True
    assert result[2]["name"] == "booktabs"
    assert result[2]["installed"] is False


def test_parse_tlmgr_list_dash_format():
    output = (
        "booktabs - Publication quality tables in LaTeX\n"
        "amsmath - AMS mathematical facilities for LaTeX\n"
    )
    result = pytinytex._parse_tlmgr_list(output)
    assert len(result) == 2
    assert result[0]["name"] == "booktabs"
    assert result[0]["description"] == "Publication quality tables in LaTeX"
    assert result[1]["name"] == "amsmath"


def test_parse_tlmgr_list_empty():
    assert pytinytex._parse_tlmgr_list("") == []
    assert pytinytex._parse_tlmgr_list("\n\n") == []


def test_parse_tlmgr_list_plain_lines():
    output = "somepkg\nanotherpkg\n"
    result = pytinytex._parse_tlmgr_list(output)
    assert len(result) == 2
    assert result[0]["name"] == "somepkg"
    assert result[1]["name"] == "anotherpkg"


def test_parse_tlmgr_info():
    output = (
        "package:    booktabs\n"
        "revision:   12345\n"
        "cat-version: 1.618\n"
        "category:   Package\n"
        "shortdesc:  Publication quality tables\n"
        "longdesc:   The booktabs package provides\n"
        "            additional commands for tables.\n"
        "installed:  Yes\n"
    )
    result = pytinytex._parse_tlmgr_info(output)
    assert result["package"] == "booktabs"
    assert result["revision"] == "12345"
    assert result["cat-version"] == "1.618"
    assert result["shortdesc"] == "Publication quality tables"
    assert "additional commands" in result["longdesc"]
    assert result["installed"] == "Yes"


def test_parse_tlmgr_info_empty():
    assert pytinytex._parse_tlmgr_info("") == {}
