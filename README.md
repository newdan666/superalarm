# 爱因斯坦闹钟

一个 Windows 桌面端小闹钟程序，双击即用（首次运行可选择“安装到本机”）。

> **两种交付物**
> - `爱因斯坦闹钟-1.0.0.zip`：**推荐**。解压后直接运行文件夹里的 `EinsteinAlarm.exe`。
>   不依赖系统临时目录，任何环境都能启动（onedir 模式）。
> - `爱因斯坦闹钟-Setup-1.0.0.exe`：单文件 `exe`。正常 Windows 上双击即可；
>   但在**系统临时目录不可写**的环境（如某些沙箱、受限账户）会报
>   “could not create temporary directory”，此时请改用上面的 ZIP 版本。

## 功能

- **右下角弹窗**：像广告弹窗一样，在屏幕右下角滑入一个小爱因斯坦头像，头像之外背景透明。
- **思索气泡**：头像头顶一个思索对话框，里面显示你设置的内容（可在设置里改）。
- **定时提醒**：可设**多条闹钟**，每条有独立的时间、频率（每天/只弹一次）和气泡内容；
  设置里点“＋ 添加闹钟”可继续加，点 ✕ 删除，前面的勾可临时停用。
- **名单**：头像**左侧**一本小书，点开可查看/编辑名单。
  - 条目可 **加对勾（完成）**、**加删除线**、**直接改文字**、**删除**。
  - 底部留一块**备注区**。
  - 名单窗口**右上角一个小齿轮**，点它进入**设置**。
- **提示音**：可开关；可选**预制提示音**（叮咚/风铃/鸟鸣/闹钟）或**自设声音**（wav/mp3/flac/ogg）。
- **开机自启**：设置里勾选“开机自动运行”，写注册表 Run 键。
- **GitHub 更新**：设置更新源 `owner/repo`，可开启“从 GitHub 自动更新版本”或暂停更新。
  - 自动更新：启动时查询 GitHub Releases 最新版，发现更新则下载并运行安装包。
- **托盘图标**：运行时在系统托盘，右键菜单可显示弹窗/名单/设置/安装/卸载/检查更新/退出。
- **单实例**：已运行则不再开第二个，提示看托盘。

## 使用

1. 解压 `爱因斯坦闹钟-1.0.0.zip`，进入 `EinsteinAlarm` 文件夹，双击 `EinsteinAlarm.exe`。
2. 首次运行弹窗询问“是否安装到本机”——选**是**：整个程序目录复制到
   `%LOCALAPPDATA%\EinsteinAlarm`，创建开始菜单/桌面快捷方式，并注册开机自启；
   选**否**：仅本次运行（便携模式）。
3. 运行后在系统托盘有爱因斯坦图标，右键菜单可打开**名单**和**设置**。

### 设置项

| 项 | 说明 |
|---|---|
| 闹钟（可多条） | 每条：启用勾选 + 时间 HH:MM + 频率（每天/只弹一次）+ 气泡内容 + ✕ 删除 |
| ＋ 添加闹钟 | 追加一条闹钟；可设多条，各自到点弹窗 |
| 气泡内容 | 思索气泡里显示的文字（每条闹钟独立） |
| 自动隐藏(秒) | `0`=一直显示直到手动关闭；>0 秒后自动滑出 |
| 强制显示在所有窗口之前 | 勾选后弹窗始终置顶，不会被其他窗口盖住（默认开） |
| 启用提示音 | 弹窗时是否播放声音 |
| 声音来源 | 预制提示音 或 自设声音 |
| 预制提示音 | 叮咚 / 风铃 / 鸟鸣 / 闹钟（可“试听”） |
| 自设声音 | 选择本地音频文件（wav/mp3/flac/ogg） |
| 开机自动运行 | 写 `HKCU\...\Run`，登录时自启 |
| 从 GitHub 自动更新 | 启动时检查更新源 Releases，有新版自动下载运行 |
| 更新源 | `owner/repo`，如 `someone/einstein-alarm` |

## 数据存放

- 配置/名单/备注：`%APPDATA%\EinsteinAlarm\config.json`
- 预制提示音：`%APPDATA%\EinsteinAlarm\sounds\*.wav`
- 安装目录（自安装模式）：`%LOCALAPPDATA%\EinsteinAlarm\`

## 开发者

- 语言/框架：Python 3.11 + PySide6（Qt 6）
- 打包：PyInstaller 6.x，windowed；onedir（`build_onedir.spec`）与 onefile（`build.spec`）两套
- 图标：`src/make_icon.py` 生成 `assets/icon.ico`
- 声音播放：winmm MCI（Windows 内置编解码器，零额外依赖），预制音用 stdlib `wave` 生成

### 打包命令

```powershell
# onedir（推荐，ZIP 交付物）
python -m PyInstaller build_onedir.spec --noconfirm --distpath dist --workpath build_onedir
# 产物：dist/EinsteinAlarm/ 整目录，压缩为 爱因斯坦闹钟-<版本>.zip

# onefile（单文件 exe，正常环境可用）
python -m PyInstaller build.spec --noconfirm --distpath dist --workpath build
# 产物：dist/EinsteinAlarm.exe，重命名为 爱因斯坦闹钟-Setup-<版本>.exe
```

> **“could not create temporary directory”**：onefile 版启动时要把自身解压到系统临时目录；
> 若该目录不可写（沙箱、受限账户、盘符异常等）会报此错。onedir 版不依赖临时目录，不受影响。
