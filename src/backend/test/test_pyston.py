# pip install aiopyston
# docker-compose -f docker-compose-middleware.yml up piston -d
# 可选包
# curl -X GET http://localhost:2000/api/v2/packages
# 安装最新Python
# curl -X POST http://localhost:2000/api/v2/packages \
#     -H "Content-Type: application/json" \
#     -d '{"language":"python","version":"*"}'
# 安装Python包
# 1. 使用预安装脚本
# 2. 进入容器pip安装

from pyston import PystonClient, File
import asyncio


async def main():
    client = PystonClient(
        base_url='http://127.0.0.1:2000/api/v2/',
    )

    simple_plot_code = """import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np, base64, io, os

x = np.linspace(0, 10, 50); y = np.sin(x)
plt.plot(x, y); plt.savefig('plot.png')

# 读回 → base64 → stdout
with open('plot.png','rb') as f:
    print(base64.b64encode(f.read()).decode())
    """

    output = await client.execute("python", [File(simple_plot_code)])

    print(output.raw_json)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())