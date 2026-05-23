import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def call_chat_api(user_question, debug=False):
    url = "https://drtax.deloitte.com.cn/test_cn/api/ver2.0/tax-chat/chat/sendMsgStream"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "d801665a-c0c2-4b1c-a400-3da08a5eb84f"
    }

    payload = {
        "sessionId": None,
        "model": "kimi-k2.5",
        "conversationMode": "Chat",
        "fileSearchType": None,
        "parentChatId": None,
        "collection": "",
        "stream": False,
        "webSearch": False,
        "messages": [
            {
                "role": "user",
                "content": user_question
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, verify=False, timeout=180)

        if debug:
            print("响应状态码:", response.status_code)
            print("\n--- 调试模式：完整响应 ---")
            print(f"响应头: {dict(response.headers)}")

        full_response = ""

        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8', errors='ignore')

                if debug:
                    print(f"[RAW] {repr(line_str)}")

                data_str = None

                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                elif ':' in line_str and not line_str.startswith(':'):
                    data_str = line_str.split(':', 1)[1].strip()
                else:
                    data_str = line_str

                if data_str and data_str.strip():
                    if data_str == '[DONE]':
                        break

                    try:
                        data = json.loads(data_str)

                        if debug:
                            print(f"[PARSED] {json.dumps(data, ensure_ascii=False)}")

                        content = ""

                        if 'choices' in data and len(data['choices']) > 0:
                            choice = data['choices'][0]
                            if 'delta' in choice:
                                delta = choice.get('delta', {})
                                content = delta.get('content', '')
                            elif 'text' in choice:
                                content = choice.get('text', '')
                            elif 'message' in choice:
                                message = choice.get('message', {})
                                content = message.get('content', '')

                        elif 'content' in data:
                            content = data.get('content', '')

                        elif 'data' in data:
                            data_field = data.get('data', '')
                            if isinstance(data_field, str):
                                content = data_field
                            elif isinstance(data_field, dict):
                                content = data_field.get('content', '') or data_field.get('text', '')

                        elif 'text' in data:
                            content = data.get('text', '')

                        elif 'message' in data:
                            message = data.get('message', {})
                            content = message.get('content', '')

                        if content:
                            if not (content.startswith('[^') and content.endswith('^]')):
                                full_response += content

                        if not full_response and debug:
                            print(f"[DEBUG] No content found, full data: {data}")

                    except json.JSONDecodeError as e:
                        if debug:
                            print(f"[JSON ERROR] {e}, line: {repr(data_str)}")
                        pass

        if debug:
            print("\n\n完整响应:", full_response)
        return full_response

    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return None


def batch_test():
    test_questions = [
        "税务调查时效年限是多久？税务调查时效年限的起点从何时计算？"
    ]

    results = []

    print("=== 开始批量测试 ===")
    for i, question in enumerate(test_questions, 1):
        print(f"\n【问题 {i}】 {question}")
        print("【回答】")
        
        result = call_chat_api(question, debug=False)
        print(result)
        
        results.append({
            "question": question,
            "answer": result
        })

    print("\n=== 批量测试完成 ===")
    return results


if __name__ == "__main__":
    import sys

    debug_mode = '--debug' in sys.argv
    single_mode = '--single' in sys.argv

    if single_mode:
        user_input = input("请输入你的问题: ")
        call_chat_api(user_input, debug=debug_mode)
    else:
        batch_test()
