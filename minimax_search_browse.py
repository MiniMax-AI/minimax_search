"""Search and browse utilities for MiniMax Search."""

import re
import os
import sys
import time
import math
import string
import random
import requests
from openai import OpenAI
from transformers import AutoTokenizer
from concurrent.futures import ThreadPoolExecutor, as_completed


tokenizer = AutoTokenizer.from_pretrained("MiniMaxAI/MiniMax-M2")
client = OpenAI(
    api_key=os.environ.get("MINIMAX_API_KEY"), base_url="https://api.minimax.io/v1"
)


def get_response(query, max_retry=2):
    for retry_cnt in range(max_retry):
        try:
            response = client.chat.completions.create(
                model="MiniMax-M2",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": query},
                ],
            )
            response = response.choices[0].message.content
            response = re.sub(
                r"<think>(.*?)</think>", "", response, flags=re.DOTALL
            ).strip()
            return response.strip()
        except Exception as e:
            print(f"Get response {retry_cnt} error: {e}", file=sys.stderr, flush=True)
            time.sleep(random.uniform(1, 16))
    return None


def search_google(query):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": os.environ.get("SERPER_API_KEY", ""),
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": 10}
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["organic"]


def get_brief_text(contents):
    """Extract brief text from search results"""
    source_text = ""
    for content_json in contents:
        if "extra_snippets" in content_json and len(content_json["extra_snippets"]) > 0:
            snippet = "\n".join(content_json["extra_snippets"])
        elif "snippet" in content_json:
            snippet = content_json["snippet"]
        else:
            snippet = content_json.get("description", "")
        source_text += f"<title>{content_json['title']}</title>\n<url>{content_json.get('url', content_json.get('link', ''))}</url>\n<snippet>\n{snippet}\n</snippet>\n\n"
    return source_text.strip()


def parse_query(query):
    """Parse query string"""
    keywords = ["site", "inurl", "intitle", "intext", "inanchor"]
    tag_dict = {key: "" for key in keywords}

    pattern_dict = {
        "exclude": r"-([^\s]+)",
        "synonym": r"~([^\s]+)",
        "exact": r'"([^"]+)"',
    }
    tag_dict.update({key: set() for key in pattern_dict.keys()})

    # Handle advanced search keywords
    for keyword in keywords:
        pattern = rf"{keyword}:([^\s]+)"
        match = re.search(pattern, query)
        if match:
            value = match.group(1)
            tag_dict[keyword] = value
            query = re.sub(pattern, "", query).strip()

    # Handle other tags
    for tag, pattern in pattern_dict.items():
        matches = re.findall(pattern, query)
        for match in matches:
            tag_dict[tag].add(match)
        query = re.sub(pattern, "", query).strip()

    # Extract remaining actual query content
    real_query = re.sub(f"[{string.punctuation}]", "", query)

    return tag_dict, real_query


def read_jina(url):
    headers = {
        "Authorization": f"Bearer {os.environ.get('JINA_API_KEY', '')}",
        "X-Engine": "direct",
        "Content-Type": "application/json",
        "X-Retain-Images": "none",
        "X-Return-Format": "markdown",
        "X-Timeout": "60",
    }
    payload = {"url": url}
    response = requests.post("https://r.jina.ai/", headers=headers, json=payload)
    response.raise_for_status()
    return response.text


def get_search_results(query, max_retry=3):
    """Get search results"""
    source_text = "Search result is empty. Please try again."
    if query.strip() == "":
        return source_text
    time.sleep(random.uniform(0, 16))
    for retry_cnt in range(max_retry):
        try:
            result = search_google(query)
            source_text = get_brief_text(result)
            break
        except Exception as e:
            print(f"Search {retry_cnt} error: {e}", file=sys.stderr, flush=True)
            time.sleep(random.uniform(1, 16))

    if source_text == "":
        if '"' in query:
            message = "Search result for query [{}] is empty. Return search result for cleaned query instead.".format(
                query.replace("\n", r"\n")
            )
            print(message, file=sys.stderr, flush=True)
            source_text = get_search_results(query.replace('"', ""))
            if source_text != "" and "Please try again" not in source_text:
                source_text = message + "\n\n" + source_text
            else:
                source_text = "Search result is empty. Please try again."
        else:
            print(
                "Search result for query [{}] is empty".format(
                    query.replace("\n", r"\n")
                ),
                file=sys.stderr,
                flush=True,
            )
            source_text = "Search result is empty. Please try again."
    return source_text


def get_searches_results(queries, max_retry=3):
    futures = []
    with ThreadPoolExecutor(max_workers=len(queries)) as executor:
        for i in range(len(queries)):
            futures.append(
                executor.submit(
                    lambda j, q: (j, get_search_results(q, max_retry=max_retry)),
                    i,
                    queries[i],
                )
            )
    results = ["" for _ in range(len(queries))]
    for future in as_completed(futures):
        i, output_i = future.result()
        results[i] = output_i
    output = ""
    for i, result in enumerate(results):
        output += f"--- search result for [{queries[i]}] ---\n{result}\n--- end of search result ---\n\n"
    return output.strip()


def get_browse_answer(source_text, browse_query, max_retry=2):
    token_limit = 190000

    tokenized_source_text = tokenizer.tokenize(source_text)
    if len(tokenized_source_text) > token_limit:
        output = "Since the content is too long, the result is split and answered separately. Please combine the results to get the complete answer.\n"
        num_split = math.ceil(len(tokenized_source_text) / token_limit)
        chunk_len = math.ceil(len(tokenized_source_text) / num_split)
        print(
            f"Browse too long with length {len(tokenized_source_text)}, split into {num_split} parts, with each part length {chunk_len}",
            file=sys.stderr,
            flush=True,
        )

        futures = []
        with ThreadPoolExecutor(max_workers=num_split) as executor:
            for i in range(num_split):
                start_idx = i * chunk_len
                end_idx = min(start_idx + chunk_len + 1024, len(tokenized_source_text))
                source_text_i = tokenizer.convert_tokens_to_string(
                    tokenized_source_text[start_idx:end_idx]
                )
                query_i = f"Please read the source content and answer a following question:\n--- begin of source content ---\n{source_text_i}\n--- end of source content ---\n\nIf there is no relevant information, please clearly refuse to answer.\nWhen answering, please identify and extract the original content as the evidence. Now answer the question based on the above content:\n{browse_query}"

                futures.append(
                    executor.submit(
                        lambda j, q: (j, get_response(q, max_retry=max_retry)),
                        i,
                        query_i,
                    )
                )

            outputs = ["" for _ in range(num_split)]
            for future in as_completed(futures):
                i, output_i = future.result()
                outputs[i] = output_i
            for i in range(num_split):
                if outputs[i] is None or outputs[i].strip() == "":
                    return None
                output += f"--- begin of result part {i + 1} ---\n{outputs[i]}\n--- end of result part {i + 1} ---\n\n"
    else:
        query = f"Please read the source content and answer a following question:\n---begin of source content---\n{source_text}\n---end of source content---\n\nIf there is no relevant information, please clearly refuse to answer.\nWhen answering, please identify and extract the original content as the evidence. Now answer the question based on the above content:\n{browse_query}"
        output = get_response(query, max_retry=max_retry)
    return output


def get_browse_results(url, browse_query, max_retry=3):
    """Browse webpage and answer query"""
    time.sleep(random.uniform(0, 16))
    source_text = ""

    for retry_cnt in range(max_retry):
        try:
            source_text = read_jina(url)
        except Exception as e:
            print(
                f"Read jina {retry_cnt} error: {e}, url: {url}",
                file=sys.stderr,
                flush=True,
            )
            if any(word in str(e) for word in ["Client Error"]):
                return "Access to this URL is denied. Please try again."
            time.sleep(random.uniform(1, 16))

    if source_text.strip() == "":
        print(f"Browse error with empty source_text.", file=sys.stderr, flush=True)
        return "Browse error. Please try again."
    if browse_query == "":
        browse_query = "Detailed summary of the page."

    output = get_browse_answer(source_text, browse_query, max_retry=max_retry)

    if output is None or output.strip() == "":
        print(f"Browse error with empty output.", file=sys.stderr, flush=True)
        return "Browse error. Please try again."
    return output.strip()


def get_browses_results(urls, browse_query, max_retry=3):
    futures = []
    with ThreadPoolExecutor(max_workers=len(urls)) as executor:
        for i in range(len(urls)):
            futures.append(
                executor.submit(
                    lambda j, u, b: (j, get_browse_results(u, b, max_retry=max_retry)),
                    i,
                    urls[i],
                    browse_query,
                )
            )
    results = ["" for _ in range(len(urls))]
    for future in as_completed(futures):
        i, output_i = future.result()
        results[i] = output_i
    output = ""
    for i, result in enumerate(results):
        output += (
            f"--- answer based on [{urls[i]}] ---\n{result}\n--- end of answer ---\n\n"
        )
    return output.strip()


if __name__ == "__main__":
    # print(search_google("china"))
    print(get_searches_results(["china", "china history"]))
    print(
        get_browses_results(
            [
                "https://zh.wikipedia.org/zh-hans/%E4%B8%AD%E5%8D%8E%E4%BA%BA%E6%B0%91%E5%85%B1%E5%92%8C%E5%9B%BD",
                "https://zh.wikipedia.org/wiki/%E7%BE%8E%E5%9B%BD",
            ],
            browse_query="装备",
        )
    )
