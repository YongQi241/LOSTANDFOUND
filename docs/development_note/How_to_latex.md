# Soạn và xem báo cáo LaTeX trong VS Code

Báo cáo dùng mã hóa UTF-8, hỗ trợ tiếng Việt và được cấu hình để biên dịch bằng
**pdfLaTeX**. File gốc của toàn bộ báo cáo là `main.tex`; không biên dịch riêng
các file trong `sections/` hoặc `covers/`.

## 1. Cài công cụ trên Windows

1. Cài [MiKTeX](https://miktex.org/howto/install-miktex) cho tài khoản hiện
   tại. Trong MiKTeX Console, cập nhật package và đặt **Install missing packages
   on-the-fly** thành **Ask me** hoặc **Always**.
2. Cài VS Code nếu máy chưa có.
3. Trong VS Code, cài extension **LaTeX Workshop** (`James-Yu.latex-workshop`).
4. Đóng và mở lại VS Code, sau đó kiểm tra trong terminal:

   ```powershell
   pdflatex --version
   ```

Lần build đầu tiên, MiKTeX có thể yêu cầu cài thêm các package như `babel`,
`babel-vietnamese`, `vntex`, `geometry`, `tikz`, `titlesec` hoặc `fancyhdr`. Hãy chấp nhận
cài đặt để pdfLaTeX có đủ font T5 và các package mà báo cáo sử dụng.

## 2. Mở và chỉnh sửa báo cáo

1. Mở **toàn bộ thư mục repository** trong VS Code bằng **File > Open Folder**.
2. Mở `report/main.tex` để sửa cấu hình chung và thứ tự các chương.
3. Sửa nội dung từng chương trong `report/sections/`.
4. Luôn lưu file ở UTF-8. Dòng trạng thái phía dưới VS Code phải hiển thị
   `UTF-8`; nếu không, bấm vào tên encoding và chọn **Save with Encoding >
   UTF-8**.

Các file chương có dòng `% !TeX root = ../main.tex`, vì vậy LaTeX Workshop sẽ
dùng `main.tex` làm tài liệu gốc ngay cả khi đang mở một file trong `sections/`.

## 3. Build và xem PDF

- Nhấn `Ctrl+Alt+B` để build.
- Nếu VS Code hỏi recipe, chạy lệnh **LaTeX Workshop: Build with recipe** trong
  Command Palette (`Ctrl+Shift+P`) và chọn **pdflatex**.
- Nhấn `Ctrl+Alt+V` để mở PDF trong tab VS Code.
- Chạy build ít nhất hai lần sau khi đổi tiêu đề, số chương, hình hoặc bảng để
  mục lục và các tham chiếu được cập nhật.

Cũng có thể build thủ công từ terminal:

```powershell
cd report
pdflatex -synctex=1 -interaction=nonstopmode -file-line-error main.tex
pdflatex -synctex=1 -interaction=nonstopmode -file-line-error main.tex
```

PDF được tạo tại `report/main.pdf`.

## 4. Buộc LaTeX Workshop dùng pdfLaTeX

Nếu extension mặc định chạy `latexmk` hoặc XeLaTeX, tạo hoặc cập nhật
`.vscode/settings.json` tại thư mục gốc repository:

```json
{
  "latex-workshop.latex.tools": [
    {
      "name": "pdflatex",
      "command": "pdflatex",
      "args": [
        "-synctex=1",
        "-interaction=nonstopmode",
        "-file-line-error",
        "%DOC%"
      ]
    }
  ],
  "latex-workshop.latex.recipes": [
    {
      "name": "pdflatex twice",
      "tools": ["pdflatex", "pdflatex"]
    }
  ],
  "latex-workshop.latex.recipe.default": "first",
  "latex-workshop.view.pdf.viewer": "tab"
}
```

Sau đó chạy **Developer: Reload Window** và build lại.

## 5. Xử lý lỗi thường gặp

- **`pdflatex is not recognized`**: MiKTeX chưa được cài hoặc thư mục executable
  của MiKTeX chưa có trong `PATH`. Khởi động lại VS Code sau khi cài.
- **Thiếu file `.sty` hoặc `vietnamese.ldf`**: mở MiKTeX Console, cập nhật
  package database, bật cài package còn thiếu rồi build lại.
- **Chữ tiếng Việt bị lỗi**: xác nhận file được lưu bằng UTF-8 và giữ nguyên
  `inputenc`, font encoding `T5`, cùng `babel` tiếng Việt trong `main.tex`.
- **Mục lục hoặc số hình sai**: build hai lần.
- **Build một file chương bị lỗi**: build `main.tex`; các file chương chỉ được
  đưa vào tài liệu qua lệnh `\input`.

Tài liệu cấu hình recipe và root file của extension:
[LaTeX Workshop compile guide](https://github.com/James-Yu/LaTeX-Workshop/wiki/Compile).