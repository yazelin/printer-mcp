"""
Printer MCP Server - 透過 MCP 控制印表機列印檔案或測試頁面
"""

import subprocess
import tempfile
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("printer")


@mcp.tool()
def list_printers() -> str:
    """列出系統中所有可用的印表機"""
    result = subprocess.run(["lpstat", "-p", "-d"], capture_output=True, text=True)
    if result.returncode != 0:
        return f"錯誤: {result.stderr.strip() or '無法取得印表機列表'}"
    return result.stdout.strip() or "未偵測到任何印表機"


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
VALID_PAGE_SIZES = {"A3", "A4", "A5", "B4", "B5", "Letter", "Legal", "Tabloid"}
VALID_ORIENTATIONS = {"portrait", "landscape"}
VALID_COLOR_MODES = {"gray", "color"}


def _convert_image_to_pdf(file_path: str) -> str:
    """將圖檔轉換為暫存 PDF，回傳暫存檔路徑"""
    from PIL import Image

    img = Image.open(file_path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    img.save(tmp.name, "PDF")
    return tmp.name


def _build_lp_cmd(
    file_path: str,
    printer: str = "",
    copies: int = 1,
    page_size: str = "A4",
    orientation: str = "portrait",
    color_mode: str = "gray",
) -> list[str]:
    """組合 lp 指令參數"""
    cmd = ["lp", "-n", str(copies)]
    if printer:
        cmd.extend(["-d", printer])
    cmd.extend(["-o", f"media={page_size}"])
    if orientation == "landscape":
        cmd.extend(["-o", "landscape"])
    cmd.extend(["-o", f"ColorModel={color_mode.capitalize()}"])
    cmd.append(file_path)
    return cmd


def _validate_options(page_size: str, orientation: str, color_mode: str = "gray") -> str | None:
    """驗證紙張大小、列印方向與色彩模式，回傳錯誤訊息或 None"""
    if page_size not in VALID_PAGE_SIZES:
        return f"錯誤: 不支援的紙張大小 '{page_size}'，可用選項: {', '.join(sorted(VALID_PAGE_SIZES))}"
    if orientation not in VALID_ORIENTATIONS:
        return f"錯誤: 不支援的列印方向 '{orientation}'，可用選項: portrait, landscape"
    if color_mode not in VALID_COLOR_MODES:
        return f"錯誤: 不支援的色彩模式 '{color_mode}'，可用選項: gray(黑白), color(彩色)"
    return None


@mcp.tool()
def print_test_page(
    printer: str = "",
    page_size: str = "A4",
    orientation: str = "portrait",
    color_mode: str = "gray",
) -> str:
    """列印測試頁面

    Args:
        printer: 印表機名稱（留空使用預設印表機）
        page_size: 紙張大小（預設 A4，可選 A3/A4/A5/B4/B5/Letter/Legal/Tabloid）
        orientation: 列印方向（預設 portrait 直印，可選 landscape 橫印）
        color_mode: 色彩模式（預設 gray 黑白，可選 color 彩色）
    """
    if err := _validate_options(page_size, orientation, color_mode):
        return err

    test_content = """
    ==========================================
        Printer MCP Test Page
    ==========================================

    This is a test page printed via MCP.

    If you can read this, the printer is
    working correctly.

    ==========================================
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(test_content)
        tmp_path = f.name

    try:
        cmd = _build_lp_cmd(tmp_path, printer, 1, page_size, orientation, color_mode)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return f"列印失敗: {result.stderr.strip()}"
        return f"測試頁已送出列印: {result.stdout.strip()}"
    finally:
        os.unlink(tmp_path)


@mcp.tool()
def print_file(
    file_path: str,
    printer: str = "",
    copies: int = 1,
    page_size: str = "A4",
    orientation: str = "portrait",
    color_mode: str = "gray",
) -> str:
    """列印指定檔案

    Args:
        file_path: 要列印的檔案路徑
        printer: 印表機名稱（留空使用預設印表機）
        copies: 列印份數
        page_size: 紙張大小（預設 A4，可選 A3/A4/A5/B4/B5/Letter/Legal/Tabloid）
        orientation: 列印方向（預設 portrait 直印，可選 landscape 橫印）
        color_mode: 色彩模式（預設 gray 黑白，可選 color 彩色）
    """
    if not os.path.isfile(file_path):
        return f"錯誤: 找不到檔案 {file_path}"

    if err := _validate_options(page_size, orientation, color_mode):
        return err

    tmp_pdf = None
    actual_path = file_path
    ext = Path(file_path).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        try:
            tmp_pdf = _convert_image_to_pdf(file_path)
            actual_path = tmp_pdf
        except Exception as e:
            return f"圖檔轉 PDF 失敗: {e}"

    try:
        cmd = _build_lp_cmd(actual_path, printer, copies, page_size, orientation, color_mode)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return f"列印失敗: {result.stderr.strip()}"
        return f"檔案已送出列印: {result.stdout.strip()}"
    finally:
        if tmp_pdf:
            os.unlink(tmp_pdf)


@mcp.tool()
def printer_status(printer: str = "") -> str:
    """查詢印表機狀態與佇列

    Args:
        printer: 印表機名稱（留空查詢所有）
    """
    cmd = ["lpstat", "-t"] if not printer else ["lpstat", "-p", printer]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return f"錯誤: {result.stderr.strip()}"
    return result.stdout.strip() or "無狀態資訊"


@mcp.tool()
def cancel_job(job_id: str = "") -> str:
    """取消列印工作

    Args:
        job_id: 列印工作 ID（留空取消所有）
    """
    cmd = ["cancel", job_id] if job_id else ["cancel", "-a"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return f"取消失敗: {result.stderr.strip()}"
    return "列印工作已取消"


def main():
    mcp.run()


if __name__ == "__main__":
    main()
