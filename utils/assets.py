import os
import base64

# raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


STATIC_IMG = os.path.join(
    BASE_DIR,
    "static",
    "img"
)

IMG_DIR = os.path.join(
    STATIC_IMG,
    "OLDS"
)

PATH_IMGS = os.path.join(
    BASE_DIR,
    "img",
    "Figuras"
)

def load_img_base64(path):

    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()


def load_images(prefix, filtro):

    images = []

    if not os.path.exists(IMG_DIR):
        print("PASTA NÃO EXISTE:", IMG_DIR)
        return images

    files = sorted(os.listdir(IMG_DIR))

    print(BASE_DIR)
    print(IMG_DIR)
    print(os.path.exists(IMG_DIR))

    print("ARQUIVOS:")
    for f in files:
        print(f)

    for f in os.listdir(IMG_DIR):
        print(f)

        if prefix.lower() in f.lower() and filtro.lower() in f.lower():

            full_path = os.path.join(IMG_DIR, f)

            images.append(
                load_img_base64(full_path)
            )

    print("TOTAL:", len(images))

    return images