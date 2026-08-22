# GitHub 发布指南

这份文档记录如何把 VRC Translate 发布到你自己的 GitHub 仓库，以及程序里哪些链接需要改成你的账号。

---

## 一、需要改的链接（共 2 个文件，5 处）

### 1. `update_checker.py` — 自动更新检查（2 处）

程序启动时会从远程拉取 `version.json` 检查有没有新版本。把占位仓库 `vrc-translate/vrc_trans` 改成你的 `你的用户名/你的仓库名`：

```python
# 第 17 行：GitHub 主地址（raw.githubusercontent.com）
VERSION_CHECK_URL = "https://raw.githubusercontent.com/你的用户名/你的仓库名/main/version.json"

# 第 19 行：Gitee 备用地址（国内访问 GitHub 失败时用，没有 Gitee 可以留着不改，不影响）
VERSION_CHECK_URL_BACKUP = "https://gitee.com/你的用户名/你的仓库名/raw/main/version.json"
```

> 如果你默认分支叫 `master` 而不是 `main`，把 URL 里的 `/main/` 改成 `/master/`。

### 2. `install.iss` — Windows 安装包信息（3 处）

```iss
#define MyAppVersion "2.2.0"                          ; 每次发新版改这里
AppPublisherURL=https://github.com/你的用户名/你的仓库名
AppSupportURL=https://github.com/你的用户名/你的仓库名/issues
AppUpdatesURL=https://github.com/你的用户名/你的仓库名/releases
```

### 3. `install.iss` 里的 AppId（可选但建议）

```iss
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
```
这是安装包的唯一标识。建议用 Visual Studio 或在线 GUID 生成器生成一个你自己的，替换掉这个占位 GUID。这样以后升级安装能正确覆盖旧版。

---

## 二、version.json（更新检查用）

在仓库根目录放一个 `version.json`，程序通过它判断有没有新版本：

```json
{
  "version": "2.2.0",
  "download_url": "https://github.com/你的用户名/你的仓库名/releases/latest",
  "release_notes": "V8：修复主界面崩溃、模型下载卡死等问题"
}
```

- `version`：最新版本号，要和 `update_checker.py` 里的 `CURRENT_VERSION` 对应。这里的版本号比用户本地的大，程序就会提示更新。
- `download_url`：点更新后跳转的地址，一般填 Releases 最新版页面。
- `release_notes`：更新提示里显示的文字。

**每次发新版都要改这个文件**，否则用户收不到更新提示。

---

## 三、模型和 FFmpeg 从哪下？（不用你管）

程序运行时要下载的东西有三类，**都不在你的仓库里**，不用你上传：

| 下载内容 | 来源 | 说明 |
|---------|------|------|
| sherpa-onnx 语音模型 | `github.com/k2-fsa/sherpa-onnx` 官方 Release | 程序通过 12 条 GitHub 加速镜像自动下载，你不用管 |
| FFmpeg | `github.com/BtbN/FFmpeg-Builds` 官方 Release | 同上，自动下载 |
| VB-CABLE 虚拟音频线 | `vb-audio.com/Cable/` | 程序内打开官网，用户自己装 |

这些都是第三方官方维护的，你的程序只是加了国内加速镜像去下载。你不需要把这些几百 MB 的文件传到自己仓库。

### 如果你想自己托管模型（可选）

如果你担心 k2-fsa 的 Release 哪天挂了，可以把模型 `.tar.bz2` 传到你自己的 GitHub Release（单文件限制 2GB，模型最大 998MB，没问题），然后在 `bootstrap.py` 里把你的 Release 链接加到镜像列表最前面：

```python
mirror_prefixes = [
    "https://github.com/你的用户名/你的仓库名/releases/download/v2.2.0/",  # 你自己的镜像优先
    "https://ghfast.top/",
    # ... 其他镜像
]
```

但这不是必须的，先用官方源 + 公共加速镜像就行。

---

## 四、发布步骤（明天照着做）

### 1. 建仓库
- 在 GitHub 新建仓库（建议名 `vrc-translate` 或你喜欢的名字）
- 不要勾选 Initialize with README（你本地已经有了）

### 2. 改链接
- 按第一节改 `update_checker.py` 和 `install.iss`
- 在仓库根目录创建 `version.json`（第二节模板）

### 3. 初始化并推送
```bash
cd 你的项目文件夹
git init
git add .
git commit -m "V8: 主界面 + 同声传译 + 下载修复"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

### 4. 建 Release
- GitHub 仓库页面 → Releases → Create a new release
- Tag 填 `v2.2.0`
- 标题填 `VRC Translate V8`
- 上传打包好的文件（可选）：
  - `VRC_Translate.exe`（用 build_exe.bat 打的单文件）
  - `VRC_Translate_Setup_2.2.0.exe`（用 install.iss 编译的安装包）
  - `vrc_trans_v8_bugfix.zip`（源码包，方便不想打包的人直接跑）
- 发布

### 5. .gitignore 建议
仓库里别提交这些，先建个 `.gitignore`：
```
__pycache__/
*.pyc
build/
dist/
*.spec.bak
*.zip
models/
```

---

## 五、发版检查清单

每次发新版前过一遍：

- [ ] `update_checker.py` 里 `CURRENT_VERSION` 改了
- [ ] `install.iss` 里 `MyAppVersion` 改了
- [ ] `version.json` 里 `version` 和 `release_notes` 改了
- [ ] `CHANGELOG.md` 更新了
- [ ] 源码能跑（`python main.py`）
- [ ] 打 EXE 能跑（`build_exe.bat`）
- [ ] 没有硬编码的 API Key 或个人信息
- [ ] 打了 tag 并推了 Release
