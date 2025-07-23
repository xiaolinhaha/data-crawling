import json
import logging

import lmjj_agent

logger = logging.getLogger(__name__)
def get_path(req_text: str):
    logger.info(
        f'chat_summary'
        f'[{req_text}]'
    )
    try:
        args: dict = json.loads(req_text)
    except Exception:
        logger.error(
            f'chat_summary'
            f'[请求参数不是正确的JSON]',
            exc_info=True
        )
        return {
            'error': '请求参数不是正确的JSON',
            'text': '',
        }

    app_code: str = args.get('app_code')
    file_info: str = args.get('file_info')
    from_addr: str = args.get('from_addr')
    output_len: int = args.get('output_len')
    sleep_time: int = args.get('sleep_time')
    app_key: str = args.get('app_key')
    remote_addr: str = from_addr
    base_url = from_addr + "v1"
    headers = {'Authorization': f'Bearer {app_key}'}
    url = f'{base_url}/workflows/run'
    logger.info(f'获取文件path：app_code:{app_code}, file_info:{file_info}, from_addr:{from_addr}, output_len:{output_len},'
                f'sleep_time:{sleep_time},  api_key:{app_key}, base_url:{base_url}')
    # 目前最多只能上传[6]个文件
    # 预分配参数防止工作流crash
    path = {
        'path_1': '',
        'path_2': '',
        'path_3': '',
        'path_4': '',
        'path_5': '',
        'path_6': '',
    }
    idx = 1
    while True:
        head = file_info.find("tenant_id='")
        if head < 0:
            break
        head += + len("tenant_id='")
        tail = head + 36
        tenant_id = file_info[head:tail]

        head = file_info.find("related_id='")
        head += + len("related_id='")
        tail = head + 36
        file_id = file_info[head:tail]

        file_path = lmjj_agent.file_download_by_tenant(
            app_code=app_code,
            file_id=file_id,
            tenant_id=tenant_id,
            remote_addr=remote_addr
        )

        path[f'path_{idx}'] = file_path

        idx += 1
        file_info = file_info[tail:]

    return path