# Printer MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that enables AI assistants to control printers on Linux/macOS systems via CUPS.

透過 MCP 協議讓 AI 助手控制印表機，支援列印檔案、測試頁、查詢狀態、取消工作等操作。

## Prerequisites / 前置需求

### 1. CUPS printing system

This MCP server relies on the **CUPS** (Common UNIX Printing System) command-line tools (`lp`, `lpstat`, `cancel`). Most Linux distributions and macOS come with CUPS pre-installed.

本伺服器依賴 CUPS 列印系統的命令列工具，大多數 Linux 發行版及 macOS 已內建。

**Check if CUPS is installed / 確認 CUPS 是否已安裝：**

```bash
lpstat -v
```

If the command is not found, install CUPS:

```bash
# Debian / Ubuntu
sudo apt install cups

# Fedora / RHEL
sudo dnf install cups

# Arch Linux
sudo pacman -S cups

# macOS — CUPS is included by default
```

### 2. At least one printer must be configured / 至少需要設定一台印表機

**This is required.** The MCP server controls printers through CUPS — if no printer is configured, all tools will return errors.

**這是必要條件。** MCP 伺服器透過 CUPS 控制印表機，如果系統中沒有設定任何印表機，所有工具都無法正常運作。

**Check if a printer is configured / 確認是否已設定印表機：**

```bash
lpstat -a
```

If no printers are listed, you need to add one. Here are common methods:

**Method A: GUI (recommended for desktop users)**
- Open **Settings → Printers** (GNOME) or **System Settings → Printers** (KDE)
- Click "Add Printer" and follow the wizard

**Method B: Command line**

```bash
# 1. Find available printers on the network
lpinfo -v

# 2. Find the matching driver
lpinfo --make-and-model "YOUR_PRINTER_BRAND" -m

# 3. Add the printer
sudo lpadmin -p PRINTER_NAME -E \
  -v "DEVICE_URI_FROM_STEP_1" \
  -m "DRIVER_PATH_FROM_STEP_2"

# 4. Set as default printer (optional)
sudo lpadmin -d PRINTER_NAME
```

**Example — adding a Ricoh network printer:**

```bash
sudo lpadmin -p MP-C2004ex -E \
  -v "dnssd://RICOH%20MP%20C2004ex._pdl-datastream._tcp.local/" \
  -m "openprinting-ppds:0/ppd/openprinting/Ricoh/PDF/Ricoh-MP_C2004ex_PDF.ppd"
sudo lpadmin -d MP-C2004ex
```

**Verify the printer works / 驗證印表機是否正常：**

```bash
echo "test" | lp
```

## Installation / 安裝

### Using uv (recommended)

```bash
uv pip install printer-mcp
```

### Using pip

```bash
pip install printer-mcp
```

## Configuration / 設定

### Claude Code

Add to your Claude Code MCP settings (`~/.claude/mcp.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "printer": {
      "command": "uvx",
      "args": ["printer-mcp"]
    }
  }
}
```

### Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "printer": {
      "command": "uvx",
      "args": ["printer-mcp"]
    }
  }
}
```

### Running directly

```bash
# With uv
uv run printer-mcp

# With python
python server.py
```

## Available Tools / 可用工具

| Tool | Description | 說明 |
|------|-------------|------|
| `list_printers` | List all available printers | 列出所有可用的印表機 |
| `print_test_page` | Print a test page to verify printer connectivity | 列印測試頁以驗證印表機連線 |
| `print_file` | Print a file with optional printer and copies settings | 列印指定檔案，可選擇印表機及份數 |
| `printer_status` | Query printer status and job queue | 查詢印表機狀態與列印佇列 |
| `cancel_job` | Cancel a specific print job or all jobs | 取消指定或所有列印工作 |

### Tool Parameters / 工具參數

**`print_file`**
- `file_path` (required) — Path to the file to print. Supported formats: PDF, text, and image files (PNG, JPG, JPEG, GIF, BMP, TIFF, WebP — images are automatically converted to PDF before printing)
- `printer` (optional) — Printer name, defaults to system default
- `copies` (optional) — Number of copies, defaults to 1
- `page_size` (optional) — Paper size, defaults to `A4`. Options: `A3`, `A4`, `A5`, `B4`, `B5`, `Letter`, `Legal`, `Tabloid`
- `orientation` (optional) — Print orientation, defaults to `portrait`. Options: `portrait`, `landscape`

**`print_test_page`**
- `printer` (optional) — Printer name, defaults to system default
- `page_size` (optional) — Paper size, defaults to `A4`. Options: `A3`, `A4`, `A5`, `B4`, `B5`, `Letter`, `Legal`, `Tabloid`
- `orientation` (optional) — Print orientation, defaults to `portrait`. Options: `portrait`, `landscape`

**`printer_status`**
- `printer` (optional) — Printer name, leave empty to query all

**`cancel_job`**
- `job_id` (optional) — Job ID to cancel, leave empty to cancel all

## Usage Examples / 使用範例

Once configured, you can ask your AI assistant:

```
"Print the file /home/user/report.pdf"
"List available printers"
"Print 3 copies of invoice.pdf to the HP printer"
"What's the printer status?"
"Cancel all print jobs"
"Print a test page"
```

## Supported Platforms / 支援平台

- **Linux** — Any distribution with CUPS installed
- **macOS** — CUPS is built-in

> **Note:** Windows is not supported. CUPS is not available on Windows natively.

## Troubleshooting / 疑難排解

| Problem | Solution |
|---------|----------|
| `lpstat: No destinations added` | No printer configured. See [Prerequisites](#2-at-least-one-printer-must-be-configured--至少需要設定一台印表機) above. |
| `lp: command not found` | CUPS is not installed. See [CUPS installation](#1-cups-printing-system). |
| Print job sent but nothing prints | Check `printer_status` for errors. Verify printer is online and connected. |
| Permission denied | Your user may need to be in the `lpadmin` group: `sudo usermod -aG lpadmin $USER` |
| Image file won't print | Image files (PNG, JPG, etc.) are auto-converted to PDF via Pillow. Ensure `Pillow` is installed: `pip install Pillow` |

## License

MIT
