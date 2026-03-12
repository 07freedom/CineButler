"""LLM prompt templates for CineButler nodes."""

IDENTIFY_PROMPT = """你是一个媒体识别助手。根据文件名和种子信息，判断这是电影、剧集、成人内容还是无法识别。

规则：
- 电影：单集完整影片
- 剧集：有季/集概念 (S01E01 等)
- 成人内容：色情、 porn 等 -> media_type 填 "adult"
- 无法从 TMDB 匹配到可信结果 -> media_type 填 "unknown"

请使用 TMDB 工具搜索并确认。搜索时用英文或原标题。

最终你必须用以下 JSON 格式回复（不要包含其他文字）：
{{"media_type":"movie"|"tv"|"adult"|"unknown","tmdb_id":数字或null,"title":"作品标题","year":数字或null,"season":数字或null,"episodes":[1,2]}}

文件名: {torrent_name}
解析出的标题线索: {title}
解析出的年份: {year}
解析出的季: {season}
解析出的集: {episodes}
"""
