from PIL import Image, ImageEnhance
import glob, os, sys
NAVY = (13, 20, 41)
for d in sys.argv[1:]:
    out = d + "/echt"; os.makedirs(out, exist_ok=True)
    for p in sorted(glob.glob(d + "/roh/*.jpg")):
        im = Image.open(p).convert("RGB")
        im = ImageEnhance.Color(im).enhance(0.72)
        im = ImageEnhance.Contrast(im).enhance(1.06)
        im = Image.blend(im, Image.new("RGB", im.size, NAVY), 0.14)
        im = ImageEnhance.Brightness(im).enhance(1.04)
        im.save(out + "/" + os.path.basename(p), "JPEG", quality=92)
    print(d, len(os.listdir(out)))
