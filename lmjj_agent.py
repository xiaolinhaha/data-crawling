import logging
import mimetypes
import os.path
import tempfile
from urllib.parse import unquote

import requests

import env
import pdf_table_parse

logger = logging.getLogger(__name__)


def get_lmjj_host(remote_addr: str):
    remote_addr = remote_addr if remote_addr.startswith('http') else f'http://{remote_addr}'
    remote_addr = remote_addr if remote_addr.endswith('/') else remote_addr + '/'

    base_url = env.get_lmjj_base_url()
    lmjj_host = base_url if base_url else remote_addr
    logger.info(f'get_lmjj_host[{remote_addr}][{base_url}][{lmjj_host}]')
    return lmjj_host


def get_passport(app_code: str, remote_addr: str):
    url = get_lmjj_host(remote_addr) + 'api/passport'
    h = {
        'X-App-Code': app_code,
    }
    resp = requests.get(url=url, headers=h, )
    logger.info(f'get_passport[{url}][{app_code}][{resp.text}]')
    resp_json: dict = resp.json()
    return resp_json.get('access_token')


def upload_file(app_code: str, file: str, remote_addr):
    token = get_passport(app_code, remote_addr=remote_addr)

    url = get_lmjj_host(remote_addr) + 'api/files/v2/upload'
    h = {
        'Authorization': f'Bearer {token}',
    }

    file_type, _ = mimetypes.guess_type(file)
    # 根据文件类型设置正确的MIME类型
    if file_type and file_type.startswith('application/vnd.openxmlformats-officedocument'):
        if file_type.endswith('.wordprocessingml.document'):
            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif file_type.endswith('.spreadsheetml.sheet'):
            mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            mime_type = file_type  # 如果是其他类型的Office文件，使用猜测的MIME类型
    else:
        # 如果无法猜测MIME类型，可以设置一个默认值或进行错误处理
        mime_type = 'application/octet-stream'

    # 使用正确的MIME类型构建文件字典
    files = {
        'file': (
            os.path.basename(file),
            open(file=file, mode='rb'),
            mime_type,
        ),
    }
    # files = {
    #     'file': (
    #         os.path.basename(file),
    #         open(file=file, mode='rb'),
    #         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    #     ),
    # }
    resp = requests.post(url=url, files=files, headers=h)
    logger.info(f'文件上传结果=>{resp.text}')

    resp_json: dict = resp.json()
    logger.info(f'upload_file[{file}][{resp_json}]')

    file_id = resp_json.get('id')
    download_url = resp_json.get('download_url')

    return {
        'file_id': file_id,
        'download_url': download_url,
    }


def file_preview(app_code: str, file_id: str, remote_addr):
    token = get_passport(app_code, remote_addr=remote_addr)

    url = get_lmjj_host(remote_addr) + 'api/files/v2/preview'
    h = {
        'Authorization': f'Bearer {token}',
    }
    params = {
        'file_id': file_id,
    }
    resp = requests.get(url=url, params=params, headers=h)
    return resp.text


def get_pdf_table_result(app_code: str, file_id: str, remote_addr):
    token = get_passport(app_code, remote_addr=remote_addr)
    url = env.LMJJ_BASE_URL + 'api/files/v2/previewPDF'
    h = {
        'Authorization': f'Bearer {token}',
    }
    params = {
        'file_id': file_id,
    }
    resp = requests.get(url=url, params=params, headers=h)

    return pdf_table_parse.extract_tables(resp.content)


def file_download_by_tenant(app_code: str, file_id: str, tenant_id: str, remote_addr) -> str:
    token = get_passport(app_code, remote_addr=remote_addr)

    url = get_lmjj_host(remote_addr) + 'api/files/v2/download-by-tenant'
    h = {
        'Authorization': f'Bearer {token}',
    }
    params = {
        'file_id': file_id,
        'tenant_id': tenant_id,
    }
    logger.info(f'file_download_by_tenant[{url}][{params}]')

    resp = requests.get(url=url, params=params, headers=h)
    filename: str = resp.headers.get('Content-Disposition')
    filename = filename[len('attachment; filename='):]
    filename = unquote(filename)

    # create a temp file without auto-delete
    with tempfile.NamedTemporaryFile(delete=False, mode='wb') as temp_file:
        temp_file.write(resp.content)
        temp_file.close()

    temp_file_path = temp_file.name
    logger.info(f'file_download_by_tenant[{params}][{filename}][{temp_file_path}]')

    return temp_file_path
