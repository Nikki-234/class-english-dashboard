"""发布后自检: 验证线上页面的 content-type 是 text/html(能渲染) 而不是 text/plain.

用法: python3 verify_online.py <url> [更多 url...]
"""
import subprocess
import sys
import time

CHECK_MARKERS = [
    'id="gate"',
    'id="settings"',
    'function buildGate',
    'function visibleStudents',
]


def head(url):
    r = subprocess.run(
        ['curl', '-sSI', '--max-time', '20', url],
        capture_output=True, text=True)
    out = r.stdout.replace('\r', '')
    status = ''
    ctype = ''
    for line in out.split('\n'):
        if line.startswith('HTTP/'):
            status = line.split(' ', 1)[1].strip() if ' ' in line else line
        elif line.lower().startswith('content-type:'):
            ctype = line.split(':', 1)[1].strip()
    return status, ctype


def body(url):
    r = subprocess.run(
        ['curl', '-sS', '--max-time', '25', url],
        capture_output=True, text=True)
    return r.stdout


def check(url, need_markers=True):
    status, ctype = head(url)
    ok = True
    print(f'  状态: {status or "(无响应)"}')
    print(f'  content-type: {ctype or "(缺失)"}')

    if not status.startswith('2'):
        print('  ❌ 非 2xx 响应')
        ok = False
    if 'text/html' not in ctype:
        print('  ❌ content-type 不是 text/html —— 浏览器会显示源码而非渲染页面')
        ok = False

    if need_markers:
        html = body(url)
        missing = [m for m in CHECK_MARKERS if m not in html]
        if missing:
            print(f'  ❌ 缺少关键标记: {missing}')
            ok = False
        else:
            print(f'  ✅ 关键标记齐全 ({len(CHECK_MARKERS)}/{len(CHECK_MARKERS)})')
            print(f'  ✅ 页面体积 {len(html):,} 字节')

    print(f'  => {"✅ 可用作网页入口" if ok else "❌ 不可用作网页入口"}')
    return ok


def main():
    urls = sys.argv[1:]
    if not urls:
        print('用法: python3 verify_online.py <url> [...]')
        sys.exit(2)
    print('=== 线上可渲染性自检 ===')
    results = []
    for u in urls:
        print(f'\n{u}')
        results.append(check(u))
    print('\n=== 汇总 ===')
    for u, ok in zip(urls, results):
        print(f'  {"✅" if ok else "❌"} {u}')
    sys.exit(0 if all(results) else 1)


if __name__ == '__main__':
    main()
