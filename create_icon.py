"""生成程序图标"""

from PIL import Image, ImageDraw


def create_icon():
    """创建眼睛形状的图标"""
    # 创建多个尺寸的图标
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 缩放比例
        scale = size / 64

        # 眼睛轮廓 - 外层
        eye_left = int(8 * scale)
        eye_top = int(16 * scale)
        eye_right = int(56 * scale)
        eye_bottom = int(48 * scale)
        outline_width = max(1, int(3 * scale))

        draw.ellipse(
            [eye_left, eye_top, eye_right, eye_bottom],
            outline=(100, 200, 100, 255),
            width=outline_width
        )

        # 眼球
        pupil_left = int(22 * scale)
        pupil_top = int(22 * scale)
        pupil_right = int(42 * scale)
        pupil_bottom = int(42 * scale)
        draw.ellipse(
            [pupil_left, pupil_top, pupil_right, pupil_bottom],
            fill=(100, 200, 100, 255)
        )

        # 瞳孔
        center = size // 2
        pupil_r = int(4 * scale)
        draw.ellipse(
            [center - pupil_r, center - pupil_r, center + pupil_r, center + pupil_r],
            fill=(30, 80, 30, 255)
        )

        # 高光
        highlight_r = int(2 * scale)
        hx = center - int(2 * scale)
        hy = center - int(4 * scale)
        draw.ellipse(
            [hx - highlight_r, hy - highlight_r, hx + highlight_r, hy + highlight_r],
            fill=(255, 255, 255, 200)
        )

        images.append(img)

    # 保存为 .ico 文件（多尺寸）
    images[0].save(
        "eye_care.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print("图标已生成: eye_care.ico")

    # 同时保存一个 64x64 的 png 用于设置界面
    images[2].save("eye_care_icon.png", format="PNG")
    print("PNG 图标已生成: eye_care_icon.png")


if __name__ == "__main__":
    create_icon()
