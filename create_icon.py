"""生成程序图标 - 使用简单方法确保兼容性"""

from PIL import Image, ImageDraw


def create_icon():
    """创建眼睛形状的图标"""
    # 创建 256x256 的图标
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 眼睛轮廓 - 外层
    draw.ellipse([20, 50, 236, 206], outline=(100, 200, 100, 255), width=12)
    # 眼球
    draw.ellipse([60, 70, 196, 186], fill=(100, 200, 100, 255))
    # 瞳孔
    center = size // 2
    draw.ellipse([center - 30, center - 30, center + 30, center + 30], fill=(30, 80, 30, 255))
    # 高光
    draw.ellipse([center - 20, center - 40, center + 10, center - 10], fill=(255, 255, 255, 200))

    # 保存为 ico（包含多种尺寸）
    img.save("eye_care.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("图标已生成: eye_care.ico")

    # 同时保存 png 用于托盘
    img_small = img.resize((64, 64), Image.Resampling.LANCZOS)
    img_small.save("eye_care_icon.png", format="PNG")
    print("PNG 图标已生成: eye_care_icon.png")

    # 验证图标文件
    import os
    ico_size = os.path.getsize("eye_care.ico")
    print(f"ico 文件大小: {ico_size} 字节")


if __name__ == "__main__":
    create_icon()
