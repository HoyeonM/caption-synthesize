import tempfile
from PIL import Image
import gzip
import os
import glob

def read_info_from_image_stealth(image):
    print(image.mode)
    # if tensor, convert to PIL image
    if hasattr(image, 'cpu'):
        image = image.cpu().numpy() #((1, 1, 1280, 3), '<f4')
        image = image[0].astype('uint8') #((1, 1280, 3), 'uint8')
        image = Image.fromarray(image)
    # trying to read stealth pnginfo
    width, height = image.size
    pixels = image.load()

    has_alpha = True if image.mode == 'RGBA' else False
    mode = None
    compressed = False
    binary_data = ''
    buffer_a = ''
    buffer_rgb = ''
    index_a = 0
    index_rgb = 0
    sig_confirmed = False
    confirming_signature = True
    reading_param_len = False
    reading_param = False
    read_end = False
    for x in range(width):
        for y in range(height):
            if has_alpha:
                r, g, b, a = pixels[x, y]
                buffer_a += str(a & 1)
                index_a += 1
            else:
                r, g, b = pixels[x, y]
            buffer_rgb += str(r & 1)
            buffer_rgb += str(g & 1)
            buffer_rgb += str(b & 1)
            index_rgb += 3
            if confirming_signature:
                if index_a == len('stealth_pnginfo') * 8:
                    decoded_sig = bytearray(int(buffer_a[i:i + 8], 2) for i in
                                            range(0, len(buffer_a), 8)).decode('utf-8', errors='ignore')
                    if decoded_sig in {'stealth_pnginfo', 'stealth_pngcomp'}:
                        confirming_signature = False
                        sig_confirmed = True
                        reading_param_len = True
                        mode = 'alpha'
                        if decoded_sig == 'stealth_pngcomp':
                            compressed = True
                        buffer_a = ''
                        index_a = 0
                    else:
                        read_end = True
                        break
                elif index_rgb == len('stealth_pnginfo') * 8:
                    decoded_sig = bytearray(int(buffer_rgb[i:i + 8], 2) for i in
                                            range(0, len(buffer_rgb), 8)).decode('utf-8', errors='ignore')
                    if decoded_sig in {'stealth_rgbinfo', 'stealth_rgbcomp'}:
                        confirming_signature = False
                        sig_confirmed = True
                        reading_param_len = True
                        mode = 'rgb'
                        if decoded_sig == 'stealth_rgbcomp':
                            compressed = True
                        buffer_rgb = ''
                        index_rgb = 0
            elif reading_param_len:
                if mode == 'alpha':
                    if index_a == 32:
                        param_len = int(buffer_a, 2)
                        reading_param_len = False
                        reading_param = True
                        buffer_a = ''
                        index_a = 0
                else:
                    if index_rgb == 33:
                        pop = buffer_rgb[-1]
                        buffer_rgb = buffer_rgb[:-1]
                        param_len = int(buffer_rgb, 2)
                        reading_param_len = False
                        reading_param = True
                        buffer_rgb = pop
                        index_rgb = 1
            elif reading_param:
                if mode == 'alpha':
                    if index_a == param_len:
                        binary_data = buffer_a
                        read_end = True
                        break
                else:
                    if index_rgb >= param_len:
                        diff = param_len - index_rgb
                        if diff < 0:
                            buffer_rgb = buffer_rgb[:diff]
                        binary_data = buffer_rgb
                        read_end = True
                        break
            else:
                # impossible
                read_end = True
                break
        if read_end:
            break
    geninfo = ''
    if sig_confirmed and binary_data != '':
        # Convert binary string to UTF-8 encoded text
        byte_data = bytearray(int(binary_data[i:i + 8], 2) for i in range(0, len(binary_data), 8))
        try:
            if compressed:
                decoded_data = gzip.decompress(bytes(byte_data)).decode('utf-8')
            else:
                decoded_data = byte_data.decode('utf-8', errors='ignore')
            geninfo = decoded_data
        except:
            pass
    return str(geninfo)
import tqdm
import json
PATH = r"F:\comfyui\ComfyUI\output\NAI_1215"
def extract_exif(path):
    for file in tqdm.tqdm(glob.glob(os.path.join(path, '*.png'))):
        image = Image.open(file)
        data = (read_info_from_image_stealth(image))
        if not data:
            continue
        data = json.loads(data)
        data = data["Description"]
        with open(file.replace('.png', '.txt'), 'w') as f:
            f.write(data)

import gradio as gr

def classify_image(img):
    img = Image.open(img)
    print("Handling image")
    return read_info_from_image_stealth(img) #returns string

def read_and_extract(img:str):
    return read_info_from_image_stealth(img)
with gr.Blocks(analytics_enabled=False) as block:
    with gr.Tab("Extract Text"):
        #inputs = gr.Image(type="pil", label="Original Image", source="upload")
        input_path = gr.Textbox(label="Path to Image")
        outputs = gr.Textbox(label="Extracted Text")
        
        button = gr.Button(value="Extract")
        button.click(
            fn=classify_image,
            inputs=[input_path],
            outputs=[outputs],
        )
    with gr.Tab("Extract text from image(file)"):
        input = gr.Image(label="source", sources="upload", type="pil",interactive=True,image_mode="RGBA")
        outputs = gr.Textbox(label="Extracted Text")
        button = gr.Button(value="Extract")
        button.click(
            fn=read_and_extract,
            inputs=[input],
            outputs=[outputs],
        )
    with gr.Tab("Extract Text from Folder"):
        inputs = gr.Textbox(label="Folder with Images")
        button = gr.Button(value="Extract")
        button.click(
            fn=extract_exif,
            inputs=[inputs],
        )
        

block.launch()