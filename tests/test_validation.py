from src.validation import contains_banned_word, https_url


def test_https_url_accepts_only_https_addresses():
    assert https_url("https://example.com/app")
    assert not https_url("http://example.com")
    assert not https_url("not a url")


def test_banned_words_ignore_spaces_and_case():
    assert contains_banned_word("hello", "this is SHIT")
    assert contains_banned_word("", "씨 발")
    assert not contains_banned_word("친절한 학생", "좋은 작품입니다")
