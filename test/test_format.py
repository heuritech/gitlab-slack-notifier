from gitlabnotifier.format import format_slack_link, format_slack_text


def test_format_slack_link():
    link = "http://www.test.com?foo=1&bar=2"
    name = "<foo&>"
    text = format_slack_link(link, name)
    expected_text = "<http://www.test.com?foo=1&bar=2|&lt;foo&amp;&gt;>"
    assert text == expected_text


def test_format_slack_text():
    text = "& test &lt; <yes|no&amp;> &gt;& &amtest"
    expected_text = "&amp; test &lt; &lt;yes|no&amp;&gt; &gt;&amp; &amp;amtest"
    formatted_text = format_slack_text(text)
    assert formatted_text == expected_text
