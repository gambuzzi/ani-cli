# ani-cli

```
uv run https://raw.githubusercontent.com/gambuzzi/ani-cli/refs/heads/main/ani-cli.py SPRING 2025 TV

alias anicli-search='function _anicli_search() { uv run https://raw.githubusercontent.com/gambuzzi/ani-cli/refs/heads/main/ani-cli.py "$1" | rg "ok.ru|mp4upload|episodes"; }; _anicli_search'
```