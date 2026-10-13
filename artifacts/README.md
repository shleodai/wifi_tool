# Windows 工作交接

本目录按用户要求上传到公开 GitHub 仓库。`apollo.hc22000` 是用于离线验证的 WPA2 握手哈希，不是已经恢复的 Wi-Fi 密码；目前没有命中密码。

## 文件

- `apollo.hc22000`：一条 Hashcat 22000 / WPA EAPOL 记录，SSID 为 `apollo家`，AP BSSID 为 `7c:7d:21:8e:6b:8a`。
- `dates-1960-20261013.txt`：24,393 个有效日期，格式 YYYYMMDD，两端包含 1960-01-01 与 2026-10-13。
- `repeated-digits.txt`：10 个候选，00000000 至 99999999。
- `apollo-handoff.zip`：包含上述输入、此说明和校验清单，供单独下载或解压。
- `SHA256SUMS.txt`：用于检查输入和说明的完整性；ZIP 内包含同一清单。

完整原始抓包没有上传，其他网络的握手没有上传。公开汇总信息与已授权的目标哈希可见于本目录。

## 已完成的检查与测试

- Mac 无线诊断成功监听信道 11。2026-10-13 16:43:12（北京时间）捕获到该目标的 4 条 EAPOL 消息。
- hcxpcapngtool 7.1.2 提取出一条可用于 Hashcat 22000 模式验证的记录。
- Mac 用 Aircrack-ng 1.7 和 4 个 CPU 工作线程跑完日期列表：约 9.39 秒，测试进程平均约整机 CPU 容量 48.2%，KEY NOT FOUND。
- 8 位重复数字列表也测试完毕，KEY NOT FOUND。
- 这些负面结果不独立证明握手绝对正确；可以在 Windows 上用 Hashcat 复核同一有限列表，再决定下一步。
- 尚未测试其他日期格式、前后缀、扩展字典或其他猜测范围。

## Windows 上继续

在 PowerShell 中：

```powershell
git clone https://github.com/shleodai/wifi_tool.git
cd wifi_tool
py -3 check_env.py --output windows-rtx3060-env.json
```

如果已经 clone，则在仓库中运行 `git pull`。

文件可以直接从 `artifacts/` 使用；如果需要独立目录：

```powershell
Expand-Archive -LiteralPath artifacts/apollo-handoff.zip -DestinationPath local-handoff
Get-FileHash artifacts/apollo.hc22000 -Algorithm SHA256
```

先检查 Python、RTX 3060、NVIDIA 驱动与现有 Hashcat；工具安装参考根目录 README。取得用户批准后再启动计算，不要 clone 后自动执行满载 benchmark。

## 下一轮方案需遵守

- 优先使用原生 Windows Hashcat，模式 22000。
- 用户要同时使用电脑，GPU 以约 50% 平均负载为目标，交互流畅优先。
- `-w 1` 仅是低工作负载配置，不是严格的 50% 限制；计算/暂停占空比也不能保证峰值不超过 50%。限载实现及监测应先验证。
- 首轮约 30 秒，明确输入、设备、运行时限与结果位置；先讨论计划，经用户批准后执行。
- 使用 `results/` 保存本地日志和恢复结果，不提交密码或结果文件到 GitHub。
- 用户授权的网络包括 `apollo家`、`apollo家_plus`、`danjia`，目前只交接 `apollo家` 的一条可用记录。没有另外两个目标的可用握手。

## 给新对话的交接提示

```text
请阅读仓库 OBJECTIVE.md、README.md 和 artifacts/README.md。我要在 Windows RTX 3060 游戏本上继续授权的 WPA2 离线测试。先计划，等我批准后执行。不要直接启动满载 benchmark；GPU 希望约 50% 平均负载，同时保持桌面流畅。先运行或查看只读环境检查结果，确认驱动和 Hashcat。artifacts/apollo.hc22000 是已抓到的真实目标握手，不是明文密码；日期和重复数字候选已经在 Mac 上测试完毕、未命中。后续先复核输入及限载方案，任何扩展候选范围都先说明。不要把恢复密码或本地结果提交到 GitHub。
```
